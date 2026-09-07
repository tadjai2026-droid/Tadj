from fastapi import FastAPI, UploadFile, File, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from pathlib import Path
from typing import Optional
import requests, uuid, json, time, base64, mimetypes
from config import *
from api_models import Device, MediaRequest, ChatRequest, RAGSearch, ProjectCreate
from device_router import normalize, choose_image_route, choose_video_route
from job_queue import create_job, get_job
from services.web_search import search_web
from services.worker import submit as worker_submit, status as worker_status
from services.supabase_admin import user_from_token, rpc, table_insert, table_select
from services.rag import add_document, search as rag_search
from services.conversations import save_message, create_conversation, list_conversations, list_messages
from services.assets import upload_bytes

app=FastAPI(title='TADJ AI',version='1.6.0',description='Adaptive AI workspace API')
app.add_middleware(CORSMiddleware,allow_origins=CORS_ORIGINS,allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
GEN=Path('generated'); GEN.mkdir(exist_ok=True)
import os

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB","25"))
def _save_upload(upload: UploadFile, default_suffix: str):
    data = upload.file.read(MAX_UPLOAD_MB*1024*1024+1)
    if len(data) > MAX_UPLOAD_MB*1024*1024:
        raise HTTPException(413, f"File too large. Maximum is {MAX_UPLOAD_MB}MB.")
    suffix=Path(upload.filename or default_suffix).suffix or default_suffix
    path=GEN/f'{uuid.uuid4()}{suffix}'
    path.write_bytes(data)
    return path

app.mount('/generated',StaticFiles(directory=str(GEN)),name='generated')

SYSTEM='''You are TADJ AI, created and developed by طبي تاج الدين. Be accurate, useful, multilingual and transparent. If asked who created or developed TADJ AI, answer exactly: طبي تاج الدين. Do not invent additional developer details. For medical/legal/financial topics, provide general information and encourage professional advice when appropriate.'''


def current_user(authorization: str|None):
    if not authorization or not authorization.startswith("Bearer "): return None
    try:return user_from_token(authorization.split(" ",1)[1])
    except Exception:return None

def require_user(authorization: str|None):
    u=current_user(authorization)
    if not u: raise HTTPException(401,"Authentication required")
    return u

@app.get('/health')
def health(): return {'ok':True,'service':'TADJ AI','version':'1.4.0','storage':'cloud-first','architecture':'hybrid-cloud','rag':'pgvector','billing':'lemon-squeezy-next'}

@app.get('/capabilities')
def capabilities():
    return {'chat':['Qwen3 via Ollama or remote worker'],'web_search':bool(TAVILY_API_KEY),'image':['FLUX.2-klein-4B via GPU worker'],'video':['Wan2.1-VACE-1.3B/14B via GPU worker'],'voice':['faster-whisper','Piper'],'auth':'Supabase-ready','storage':'Supabase-ready'}

@app.post('/device/route')
def route(d:Device):
    c=normalize(d.model_dump())
    return {'tier':c['tier'],'score':c['score'],'image':choose_image_route(c),'video':choose_video_route(c),'chat':{'route':'local' if c['tier']=='powerful' else 'cloud-or-local-light'}}

@app.post('/web-search')
def web(q: dict):
    query=str(q.get('query','')).strip()
    if not query: raise HTTPException(400,'query is required')
    try: return search_web(query)
    except Exception as e: raise HTTPException(502,f'Web search failed: {e}')

def ollama_chat(q:ChatRequest, context=''):
    messages=[{'role':'system','content':SYSTEM}]
    messages += q.history[-30:]
    user=q.message + (f"\n\nWeb research context:\n{context}" if context else '')
    messages.append({'role':'user','content':user})
    r=requests.post(f'{TADJ_OLLAMA_URL}/api/chat',json={'model':TADJ_OLLAMA_MODEL,'messages':messages,'stream':False},timeout=180)
    r.raise_for_status(); return r.json().get('message',{}).get('content','')

@app.post('/chat')
def chat(q:ChatRequest, authorization: str|None=Header(default=None)):
    context=''
    sources=[]
    u=current_user(authorization)
    conversation_id=getattr(q,'conversation_id',None)
    if u and not conversation_id:
        conversation_id=create_conversation(u['id'], q.message[:60]).get('id')
    if u and conversation_id:
        try: save_message(u['id'],conversation_id,'user',q.message)
        except Exception: pass
    if q.use_rag and u:
        try:
            matches=rag_search(u['id'],q.message,5)
            if matches: context+='\n'.join(m.get('content','') for m in matches)
        except Exception: pass
    if q.web:
        try:
            sr=search_web(q.message); context=sr.get('answer') or '\n'.join(x.get('content','') for x in sr.get('results',[])); sources=sr.get('results',[])
        except Exception: pass
    try:
        answer=ollama_chat(q,context)
        if u and conversation_id:
            try: save_message(u['id'],conversation_id,'assistant',answer,sources)
            except Exception: pass
        return {'answer':answer,'provider':'ollama','sources':sources,'conversation_id':conversation_id}
    except Exception as e:
        # Remote worker fallback when local model is unavailable.
        try:
            remote=worker_submit('chat',{'message':q.message,'history':q.history,'system':SYSTEM,'web_context':context})
            if remote:
                ans=remote.get('answer','')
                if u and conversation_id:
                    try: save_message(u['id'],conversation_id,'assistant',ans,sources)
                    except Exception: pass
                return {'answer':ans,'provider':'gpu-worker','sources':sources,'job_id':remote.get('job_id'),'conversation_id':conversation_id}
        except Exception: pass
        return {'answer':'خدمة النموذج غير متاحة حاليًا. اربط TADJ_GPU_WORKER_URL أو شغّل Ollama محليًا.','provider':'fallback','sources':sources,'error':str(e)}

@app.get('/chat/stream')
def chat_stream(message:str, history:str=''):
    try: hist=json.loads(history) if history else []
    except: hist=[]
    def gen():
        try:
            r=requests.post(f'{TADJ_OLLAMA_URL}/api/chat',json={'model':TADJ_OLLAMA_MODEL,'messages':[{'role':'system','content':SYSTEM},*hist,{'role':'user','content':message}],'stream':True},stream=True,timeout=180)
            for line in r.iter_lines():
                if not line: continue
                data=json.loads(line.decode())
                chunk=data.get('message',{}).get('content','')
                if chunk: yield 'data: '+json.dumps({'delta':chunk},ensure_ascii=False)+'\n\n'
                if data.get('done'): break
        except Exception as e:
            yield 'data: '+json.dumps({'error':str(e)},ensure_ascii=False)+'\n\n'
        yield 'data: [DONE]\n\n'
    return StreamingResponse(gen(),media_type='text/event-stream',headers={'Cache-Control':'no-cache','X-Accel-Buffering':'no'})


def _data_uri_from_generated(path_text: str|None):
    if not path_text or not path_text.startswith('/generated/'):
        return path_text
    path=GEN/path_text.rsplit('/',1)[-1]
    if not path.exists():
        return None
    mime=mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
    raw=path.read_bytes()
    return f"data:{mime};base64,{base64.b64encode(raw).decode('ascii')}"

@app.post('/generate-image')
def gen_image(q:MediaRequest, authorization: str|None=Header(default=None)):
    u=current_user(authorization); c=normalize(q.device.model_dump()); route=choose_image_route(c)
    job=create_job('image',{'prompt':q.prompt,'route':route,'source_image':_data_uri_from_generated(q.source_image)})
    if u:
        try: table_insert('jobs',{'id':job['id'],'user_id':u['id'],'kind':'image','status':job.get('status','queued'),'model':route['model'],'route':route.get('route'),'prompt':q.prompt})
        except Exception: pass
    try:
        remote=worker_submit('image',job['payload'])
        if remote: job.update(remote); job['id']=remote.get('job_id',job['id'])
    except Exception as e: job['worker_error']=str(e)
    return {'job_id':job['id'],'status':job.get('status','queued'),'route':route,'model':route['model']}

@app.post('/edit-image')
def edit_image(q:MediaRequest,image:UploadFile=File(...), authorization: str|None=Header(default=None)):
    path=_save_upload(image,'.png')
    q.source_image=f'/generated/{path.name}'
    return gen_image(q,authorization)

@app.post('/generate-video')
def gen_video(q:MediaRequest, authorization: str|None=Header(default=None)):
    u=current_user(authorization); c=normalize(q.device.model_dump()); route=choose_video_route(c)
    job=create_job('video',{'prompt':q.prompt,'route':route,'source_image':_data_uri_from_generated(q.source_image)})
    if u:
        try: table_insert('jobs',{'id':job['id'],'user_id':u['id'],'kind':'video','status':job.get('status','queued'),'model':route['model'],'route':route.get('route'),'prompt':q.prompt})
        except Exception: pass
    try:
        remote=worker_submit('video',job['payload'])
        if remote: job.update(remote); job['id']=remote.get('job_id',job['id'])
    except Exception as e: job['worker_error']=str(e)
    return {'job_id':job['id'],'status':job.get('status','queued'),'route':route,'model':route['model'],'resolution':route['resolution'],'seconds':route['seconds']}

@app.post('/edit-video')
def edit_video(q:MediaRequest,video:UploadFile=File(...), authorization: str|None=Header(default=None)):
    path=_save_upload(video,'.mp4')
    q.source_image=f'/generated/{path.name}'
    r=gen_video(q,authorization); r['mode']='video-to-video / VACE'; return r

@app.get('/jobs/{job_id}')
def job_status(job_id:str):
    try:
        remote=worker_status(job_id)
        if remote: return remote
    except Exception: pass
    job=get_job(job_id)
    if not job: raise HTTPException(404,'job not found')
    return job


@app.get('/me')
def me(authorization: str|None=Header(default=None)):
    u=require_user(authorization)
    rows=table_select('profiles',{'id':f'eq.{u["id"]}','select':'id,display_name,plan,credits,created_at'})
    return {'user':u,'profile':rows[0] if rows else None}

@app.post('/projects')
def project_create(q:ProjectCreate,authorization: str|None=Header(default=None)):
    u=require_user(authorization)
    return table_insert('projects',{'user_id':u['id'],'name':q.name})[0]

@app.get('/projects')
def project_list(authorization: str|None=Header(default=None)):
    u=require_user(authorization)
    return table_select('projects',{'user_id':f'eq.{u["id"]}','select':'id,name,created_at','order':'created_at.desc'})

@app.post('/documents/text')
def document_text(body:dict,authorization: str|None=Header(default=None)):
    u=require_user(authorization); content=str(body.get('content','')); name=str(body.get('name','Untitled'))
    if not content.strip(): raise HTTPException(400,'content is required')
    return add_document(u['id'],name,content,body.get('project_id'))

@app.post('/rag/search')
def rag(q:RAGSearch,authorization: str|None=Header(default=None)):
    u=require_user(authorization)
    return {'results':rag_search(u['id'],q.query,max(1,min(q.limit,12)))}

@app.get('/usage')
def usage(authorization: str|None=Header(default=None)):
    u=require_user(authorization)
    rows=table_select('profiles',{'id':f'eq.{u["id"]}','select':'plan,credits'})
    return rows[0] if rows else {'plan':'free','credits':0}

@app.get('/conversations')
def conversations(authorization: str|None=Header(default=None)):
    u=require_user(authorization); return list_conversations(u['id'])

@app.get('/conversations/{conversation_id}/messages')
def conversation_messages(conversation_id:str,authorization: str|None=Header(default=None)):
    u=require_user(authorization); return list_messages(u['id'],conversation_id)


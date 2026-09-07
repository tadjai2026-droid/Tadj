import os, uuid, time, threading, traceback, base64, io
from pathlib import Path
from typing import Any, Dict
from fastapi import FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app=FastAPI(title="TADJ GPU Worker",version="1.6.0")

TOKEN=os.getenv("TADJ_GPU_WORKER_TOKEN","")
OUT=Path(os.getenv("OUTPUT_DIR","/outputs")); OUT.mkdir(parents=True,exist_ok=True)
MODEL_CACHE=Path(os.getenv("HF_HOME","/models"))
IMAGE_MODEL=os.getenv("FLUX_MODEL","black-forest-labs/FLUX.2-klein-4B")
WAN_MODEL=os.getenv("WAN_MODEL","Wan-AI/Wan2.1-T2V-1.3B-Diffusers")
VACE_MODEL=os.getenv("VACE_MODEL","Wan-AI/Wan2.1-VACE-1.3B-diffusers")
DEVICE=os.getenv("TORCH_DEVICE","cuda")
IMAGE_STEPS=int(os.getenv("FLUX_STEPS","4"))
IMAGE_GUIDANCE=float(os.getenv("FLUX_GUIDANCE","1.0"))
VIDEO_STEPS=int(os.getenv("WAN_STEPS","30"))
JOBS:dict[str,dict[str,Any]]={}
LOCK=threading.Lock()
GPU_LOCK=threading.Lock()
IMAGE_PIPE=None
VIDEO_PIPE=None
VACE_PIPE=None

class Job(BaseModel):
    type:str
    payload:Dict[str,Any]

def auth(a):
    if TOKEN and a!=f"Bearer {TOKEN}":
        raise HTTPException(401,"Unauthorized")

def setjob(jid,**kw):
    with LOCK:
        if jid in JOBS:
            JOBS[jid].update(kw)

def _decode_data_uri(value):
    if not value: return None
    if isinstance(value,str) and value.startswith("data:"):
        return base64.b64decode(value.split(",",1)[1])
    if isinstance(value,str):
        return Path(value).read_bytes()
    return None

def _pil_from_data(value):
    from PIL import Image
    raw=_decode_data_uri(value)
    return Image.open(io.BytesIO(raw)).convert("RGB") if raw else None

def _video_frames_from_data(value):
    raw=_decode_data_uri(value)
    if not raw: return []
    import imageio.v3 as iio
    from PIL import Image
    return [Image.fromarray(frame).convert("RGB") for frame in iio.imread(raw, index=None)]

def _cleanup():
    import gc, torch
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

def _load_image_pipe():
    global IMAGE_PIPE
    if IMAGE_PIPE is None:
        import torch
        from diffusers import Flux2KleinPipeline
        IMAGE_PIPE=Flux2KleinPipeline.from_pretrained(
            IMAGE_MODEL, torch_dtype=torch.bfloat16, cache_dir=str(MODEL_CACHE)
        )
        IMAGE_PIPE.to(DEVICE)
    return IMAGE_PIPE

def _load_video_pipe():
    global VIDEO_PIPE
    if VIDEO_PIPE is None:
        import torch
        from diffusers import AutoencoderKLWan, WanPipeline
        from diffusers.schedulers.scheduling_unipc_multistep import UniPCMultistepScheduler
        vae=AutoencoderKLWan.from_pretrained(WAN_MODEL, subfolder="vae", torch_dtype=torch.float32, cache_dir=str(MODEL_CACHE))
        VIDEO_PIPE=WanPipeline.from_pretrained(WAN_MODEL, vae=vae, torch_dtype=torch.bfloat16, cache_dir=str(MODEL_CACHE))
        VIDEO_PIPE.scheduler=UniPCMultistepScheduler.from_config(VIDEO_PIPE.scheduler.config, flow_shift=3.0)
        VIDEO_PIPE.to(DEVICE)
    return VIDEO_PIPE

def _load_vace_pipe():
    global VACE_PIPE
    if VACE_PIPE is None:
        import torch
        from diffusers import AutoencoderKLWan, WanVACEPipeline
        from diffusers.schedulers.scheduling_unipc_multistep import UniPCMultistepScheduler
        vae=AutoencoderKLWan.from_pretrained(VACE_MODEL, subfolder="vae", torch_dtype=torch.float32, cache_dir=str(MODEL_CACHE))
        VACE_PIPE=WanVACEPipeline.from_pretrained(VACE_MODEL, vae=vae, torch_dtype=torch.bfloat16, cache_dir=str(MODEL_CACHE))
        VACE_PIPE.scheduler=UniPCMultistepScheduler.from_config(VACE_PIPE.scheduler.config, flow_shift=3.0)
        VACE_PIPE.to(DEVICE)
    return VACE_PIPE

def image_task(jid,p):
    try:
        with GPU_LOCK:
            setjob(jid,status="running",progress=5,model=IMAGE_MODEL)
            pipe=_load_image_pipe()
            setjob(jid,progress=25)
            prompt=p.get("prompt","").strip()
            source=_pil_from_data(p.get("source_image"))
            height=int(p.get("height",1024)); width=int(p.get("width",1024))
            kwargs=dict(prompt=prompt,height=height,width=width,
                        num_inference_steps=int(p.get("steps",IMAGE_STEPS)),
                        guidance_scale=float(p.get("guidance",IMAGE_GUIDANCE)))
            if source is not None:
                kwargs["image"]=source
            image=pipe(**kwargs).images[0]
            path=OUT/f"{jid}.png"; image.save(path)
            setjob(jid,status="completed",progress=100,output_path=str(path),output_url=f"/outputs/{path.name}")
    except Exception as e:
        setjob(jid,status="failed",progress=100,error=str(e),trace=traceback.format_exc())
    finally:
        _cleanup()

def _blank_vace_conditions(first, last, width, height, frames):
    from PIL import Image
    first=first.resize((width,height)); last=(last or first).resize((width,height))
    video=[first]+[Image.new("RGB",(width,height),(128,128,128)) for _ in range(frames-2)]+[last]
    mask=[Image.new("L",(width,height),0)]+[Image.new("L",(width,height),255) for _ in range(frames-2)]+[Image.new("L",(width,height),0)]
    return video,mask

def video_task(jid,p):
    try:
        with GPU_LOCK:
            mode=p.get("mode","t2v")
            setjob(jid,status="running",progress=5,model=VACE_MODEL if mode=="vace" else WAN_MODEL)
            import torch
            from diffusers.utils import export_to_video
            prompt=p.get("prompt","").strip()
            height=int(p.get("height",480)); width=int(p.get("width",832))
            frames=int(p.get("frames",81)); fps=int(p.get("fps",16))

            if mode=="vace":
                pipe=_load_vace_pipe()
                source_video=p.get("source_video")
                source_image=p.get("source_image")
                if source_video:
                    video=_video_frames_from_data(source_video)
                    if not video:
                        raise ValueError("Unable to decode source video")
                    video=[f.resize((width,height)) for f in video[:frames]]
                    while len(video)<frames: video.append(video[-1].copy())
                    # Black = preserve source; white = generate. Default edits the whole clip.
                    from PIL import Image
                    mask=[Image.new("L",(width,height),255) for _ in video]
                    ref=_pil_from_data(source_image) if source_image else None
                    kwargs={"video":video,"mask":mask,"prompt":prompt,
                            "height":height,"width":width,"num_frames":len(video),
                            "num_inference_steps":int(p.get("steps",VIDEO_STEPS)),
                            "guidance_scale":float(p.get("guidance",5.0))}
                    if ref: kwargs["reference_images"]=ref
                else:
                    ref=_pil_from_data(source_image)
                    if ref is None: raise ValueError("VACE requires source_image or source_video")
                    video,mask=_blank_vace_conditions(ref,ref,width,height,frames)
                    kwargs={"video":video,"mask":mask,"reference_images":ref,"prompt":prompt,
                            "height":height,"width":width,"num_frames":frames,
                            "num_inference_steps":int(p.get("steps",VIDEO_STEPS)),
                            "guidance_scale":float(p.get("guidance",5.0))}
                setjob(jid,progress=30)
                out=pipe(**kwargs).frames[0]
            else:
                pipe=_load_video_pipe()
                setjob(jid,progress=25)
                out=pipe(prompt=prompt,negative_prompt=p.get("negative_prompt",""),
                         height=height,width=width,num_frames=frames,
                         num_inference_steps=int(p.get("steps",VIDEO_STEPS)),
                         guidance_scale=float(p.get("guidance",5.0))).frames[0]

            path=OUT/f"{jid}.mp4"; export_to_video(out,str(path),fps=fps)
            setjob(jid,status="completed",progress=100,output_path=str(path),output_url=f"/outputs/{path.name}")
    except Exception as e:
        setjob(jid,status="failed",progress=100,error=str(e),trace=traceback.format_exc())
    finally:
        _cleanup()

def run(jid):
    j=JOBS[jid]
    if j["type"]=="image": image_task(jid,j["payload"])
    elif j["type"]=="video": video_task(jid,j["payload"])
    else: setjob(jid,status="failed",progress=100,error="Unsupported worker job type")

@app.get("/health")
def health():
    return {"ok":True,"worker":"tadj-gpu","version":"1.6.0",
            "image_model":IMAGE_MODEL,"video_model":WAN_MODEL,"vace_model":VACE_MODEL,
            "device":DEVICE,"hf_home":str(MODEL_CACHE)}

@app.get("/models")
def models(authorization:str|None=Header(default=None)):
    auth(authorization)
    return {"image":IMAGE_MODEL,"video":WAN_MODEL,"vace":VACE_MODEL}

@app.post("/jobs")
def create(job:Job,authorization:str|None=Header(default=None)):
    auth(authorization)
    jid=str(uuid.uuid4())
    JOBS[jid]={"job_id":jid,"type":job.type,"payload":job.payload,"status":"queued","progress":0,"created_at":time.time()}
    threading.Thread(target=run,args=(jid,),daemon=True).start()
    return JOBS[jid]

@app.get("/jobs/{jid}")
def status(jid:str,authorization:str|None=Header(default=None)):
    auth(authorization)
    if jid not in JOBS: raise HTTPException(404,"job not found")
    return JOBS[jid]

app.mount("/outputs",StaticFiles(directory=str(OUT)),name="outputs")

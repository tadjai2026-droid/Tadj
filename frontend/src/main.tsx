
import React,{useEffect,useRef,useState}from'react';
import{createRoot}from'react-dom/client';
import{Sparkles,Image as Img,Video,BrainCircuit,Send,Mic,Upload,ShieldCheck,Globe2,Plus,LogIn,LogOut,Settings2,Paperclip,CheckCircle2,Loader2,Menu,X}from'lucide-react';
import'./styles.css';
import{post,upload,get}from'./lib/api';
import{detectDevice}from'./lib/device';
import{signInGoogle,signOut,supabase}from'./lib/supabase';

type Msg={role:'user'|'ai',text:string,sources?:any[]};
const STORAGE='tadj-ai-local-session';

function App(){
 const[d,setD]=useState<any>({}),[r,setR]=useState<any>(),[mode,setMode]=useState('chat'),[p,setP]=useState(''),[usage,setUsage]=useState<any>(),
 [msgs,setMsgs]=useState<Msg[]>([]),[conversationId,setConversationId]=useState<string>(),[busy,setBusy]=useState(false),[web,setWeb]=useState(false),[jobs,setJobs]=useState<any[]>([]),
 [user,setUser]=useState<any>(null),[authError,setAuthError]=useState(''),[mobile,setMobile]=useState(false);
 const fileRef=useRef<HTMLInputElement>(null);

 useEffect(()=>{
   detectDevice().then(async x=>{setD(x);try{setR(await post('/device/route',x))}catch{}});
   if(supabase) get('/usage').then(setUsage).catch(()=>{});
   try{const saved=localStorage.getItem(STORAGE);if(saved)setMsgs(JSON.parse(saved))}catch{}
   if(supabase){
     supabase.auth.getSession().then(({data})=>setUser(data.session?.user??null));
     const {data}=supabase.auth.onAuthStateChange((_e,s)=>setUser(s?.user??null));
     return()=>data.subscription.unsubscribe();
   }
 },[]);
 useEffect(()=>{localStorage.setItem(STORAGE,JSON.stringify(msgs.slice(-80)))},[msgs]);

 async function send(){
   if(!p.trim()||busy)return;
   const text=p;setP('');setMsgs(x=>[...x,{role:'user',text}]);setBusy(true);
   try{
    if(mode==='chat'){
      const a=await post('/chat',{message:text,history:msgs.slice(-30).map(m=>({role:m.role==='ai'?'assistant':'user',content:m.text})),web,device:d,use_rag:true,conversation_id:conversationId});
      setConversationId(a.conversation_id||conversationId);setMsgs(x=>[...x,{role:'ai',text:a.answer||'لا يوجد رد.',sources:a.sources}]);
    }else{
      const a=await post(mode==='image'?'/generate-image':'/generate-video',{prompt:text,device:d});
      setJobs(x=>[a,...x]);setMsgs(x=>[...x,{role:'ai',text:`تم إطلاق مهمة ${mode==='image'?'صورة':'فيديو'} عبر ${a.model}. سأتابع حالتها تلقائيًا.`}]);
      poll(a.job_id);
    }
   }catch(e:any){setMsgs(x=>[...x,{role:'ai',text:'تعذر تنفيذ الطلب: '+e.message}])}finally{setBusy(false)}
 }
 async function poll(id:string){
   for(let i=0;i<90;i++){
     await new Promise(r=>setTimeout(r,2500));
     try{const j=await get(`/jobs/${id}`);setJobs(x=>x.map(v=>v.job_id===id?{...v,...j}:v));if(['completed','failed','error'].includes(j.status))break}catch{}
   }
 }
 async function pickFile(e:React.ChangeEvent<HTMLInputElement>){
   const f=e.target.files?.[0]; if(!f)return;
   try{
    setBusy(true);
    const endpoint=mode==='video'?'/edit-video':'/edit-image';
    const a=await upload(endpoint,f,{prompt:p||'تحسين وتعديل الملف المرفق',device:JSON.stringify(d)});
    setJobs(x=>[a,...x]);setMsgs(x=>[...x,{role:'ai',text:`تم رفع ${f.name} وإطلاق مهمة تعديل. الحالة: ${a.status}.`}]);poll(a.job_id);
   }catch(e:any){setMsgs(x=>[...x,{role:'ai',text:'فشل رفع الملف: '+e.message}])}finally{setBusy(false);if(fileRef.current)fileRef.current.value=''}
 }

 return <div className="app">
  <aside className={mobile?'mobile-open':''}>
   <div className="logo"><div className="mark"><Sparkles/></div><b>TADJ AI<small>Adaptive Intelligence</small></b><button className="close-mobile" onClick={()=>setMobile(false)}><X/></button></div>
   <button className={mode==='chat'?'on':''}onClick={()=>{setMode('chat');setMobile(false)}}><BrainCircuit/>المحادثة</button>
   <button className={mode==='image'?'on':''}onClick={()=>{setMode('image');setMobile(false)}}><Img/>استوديو الصور</button>
   <button className={mode==='video'?'on':''}onClick={()=>{setMode('video');setMobile(false)}}><Video/>استوديو الفيديو</button>
   <div className="side-sep"/>
   <button onClick={()=>{setMsgs([]);setConversationId(undefined);localStorage.removeItem(STORAGE)}}><Plus/>محادثة جديدة</button>
   <button><Settings2/>الإعدادات</button>
   <div className="device"><ShieldCheck/><span>التكيف التلقائي<br/><strong>{r?.tier||'detecting...'}</strong></span></div>
   <div className="account">{user?<><div className="avatar">{(user.email||'U')[0].toUpperCase()}</div><div><b>{user.user_metadata?.full_name||user.email}</b><small>حساب TADJ AI</small></div><button onClick={signOut}><LogOut size={16}/></button></>:<button className="login-side" onClick={()=>signInGoogle().catch(e=>setAuthError(e.message))}><LogIn/>تسجيل الدخول بـ Google</button>}</div>
   {authError&&<small className="error">{authError}</small>}
  </aside>
  {mobile&&<div className="scrim" onClick={()=>setMobile(false)}/>}
  <main>
   <header><button className="mobile-menu" onClick={()=>setMobile(true)}><Menu/></button><div><div className="eyebrow"><Sparkles size={14}/> TADJ AI WORKSPACE</div><h1>{mode==='chat'?'ماذا تريد أن تنجز اليوم؟':mode==='image'?'Visual Studio':'Video Studio'}</h1><p>مسار ذكي يختار أفضل تنفيذ لجهازك، مع تخزين خفيف وتشغيل سحابي عند الحاجة.</p></div><div className="top-actions"><button title="تسجيل الدخول" onClick={()=>user?signOut():signInGoogle().catch(e=>setAuthError(e.message))}>{user?<CheckCircle2/>:<LogIn/>}</button><div className="score">{usage?.credits??'—'} cr</div></div></header>
   <section className="messages">
    {!msgs.length&&<div className="hero"><div className="orb"><Sparkles size={38}/></div><h2>ذكاء واحد لكل الأجهزة.</h2><p>من هاتف بسيط إلى محطة عمل قوية. TADJ AI يقرر أين تنفذ المهمة بدل أن يحمّل جهازك نماذج ضخمة.</p><div className="cards"><div onClick={()=>setMode('image')}><Img/><b>AI Image</b><span>توليد وتعديل</span></div><div onClick={()=>setMode('video')}><Video/><b>AI Video</b><span>توليد وتعديل</span></div><div onClick={()=>setWeb(!web)} className={web?'active':''}><Globe2/><b>Web Research</b><span>بحث ومصادر</span></div></div></div>}
    {msgs.map((m,i)=><div className={'msg '+m.role}key={i}><div>{m.text}</div>{m.sources?.length>0&&<div className="sources">{m.sources.slice(0,4).map((s:any,j:number)=><a key={j} href={s.url} target="_blank">{s.title||s.url}</a>)}</div>}</div>)}
    {jobs.length>0&&<div className="jobs"><b>المهام</b>{jobs.slice(0,5).map((j,i)=><div key={i}><span>{j.model}</span><small>{j.status} · {j.job_id}</small>{j.output_url&&<a href={j.output_url} target="_blank">فتح النتيجة</a>}{j.status==='running'&&<Loader2 className="spin" size={15}/>}</div>)}</div>}
   </section>
   <div className="composer"><div className="tabs"><span className={mode==='chat'?'sel':''}onClick={()=>setMode('chat')}>Chat</span><span className={mode==='image'?'sel':''}onClick={()=>setMode('image')}>Image</span><span className={mode==='video'?'sel':''}onClick={()=>setMode('video')}>Video</span><button className={web?'tool-on':''}onClick={()=>setWeb(!web)}><Globe2 size={15}/> Web</button></div>
    <textarea value={p}onChange={e=>setP(e.target.value)}onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}}}placeholder={mode==='chat'?'اكتب أي شيء...':mode==='image'?'صف الصورة التي تريدها...':'صف الفيديو الذي تريد إنشاءه...'}/>
    <div className="actions"><input ref={fileRef} type="file" hidden accept={mode==='video'?'video/*,image/*':'image/*'} onChange={pickFile}/><button onClick={()=>fileRef.current?.click()} title="رفع ملف"><Paperclip/></button><button title="الصوت"><Mic/></button><button className="send"onClick={send}disabled={busy}>{busy?<Loader2 className="spin"/>:<Send/>}</button></div>
   </div>
   <footer><button className="pro" onClick={()=>alert('الاشتراك المدفوع سيتم تفعيله عبر Lemon Squeezy بعد اكتمال واختبار GPU Worker.')}>ترقية Pro</button>وضع خفيف: لا يتم تنزيل أوزان النماذج الثقيلة على جهازك. تسجيل الدخول اختياري أثناء التطوير.</footer>
  </main>
 </div>
}
createRoot(document.getElementById('root')!).render(<App/>);

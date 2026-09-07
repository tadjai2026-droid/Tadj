import { supabase } from './supabase';
export const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';
async function headers(){
  const h:any={'Content-Type':'application/json'};
  if(supabase){const {data}=await supabase.auth.getSession(); if(data.session?.access_token) h.Authorization=`Bearer ${data.session.access_token}`;}
  return h;
}
export async function post(path:string, body:any){const r=await fetch(`${API}${path}`,{method:'POST',headers:await headers(),body:JSON.stringify(body)});if(!r.ok)throw new Error(await r.text());return r.json()}
export async function upload(path:string,file:File,fields:Record<string,string>={}){const fd=new FormData();fd.append('file',file);Object.entries(fields).forEach(([k,v])=>fd.append(k,v));let h:any={};if(supabase){const {data}=await supabase.auth.getSession();if(data.session?.access_token)h.Authorization=`Bearer ${data.session.access_token}`}const r=await fetch(`${API}${path}`,{method:'POST',headers:h,body:fd});if(!r.ok)throw new Error(await r.text());return r.json()}
export async function get(path:string){const r=await fetch(`${API}${path}`,{headers:await headers()});if(!r.ok)throw new Error(await r.text());return r.json()}

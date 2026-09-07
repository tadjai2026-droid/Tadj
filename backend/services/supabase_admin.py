import requests
from config import SUPABASE_URL,SUPABASE_SERVICE_ROLE_KEY,SUPABASE_ANON_KEY

def headers(service=True):
    key=SUPABASE_SERVICE_ROLE_KEY if service else SUPABASE_ANON_KEY
    h={"apikey":key,"Content-Type":"application/json"}
    if key: h["Authorization"]=f"Bearer {key}"
    return h

def user_from_token(token):
    if not SUPABASE_URL or not token: return None
    r=requests.get(f"{SUPABASE_URL}/auth/v1/user",headers={"apikey":SUPABASE_ANON_KEY,"Authorization":f"Bearer {token}"},timeout=15)
    if r.status_code!=200:return None
    return r.json()

def rpc(name,payload):
    r=requests.post(f"{SUPABASE_URL}/rest/v1/rpc/{name}",headers=headers(),json=payload,timeout=30); r.raise_for_status(); return r.json()

def table_insert(table,row):
    r=requests.post(f"{SUPABASE_URL}/rest/v1/{table}",headers={**headers(),"Prefer":"return=representation"},json=row,timeout=30); r.raise_for_status(); return r.json()

def table_select(table,params):
    r=requests.get(f"{SUPABASE_URL}/rest/v1/{table}",headers=headers(),params=params,timeout=30); r.raise_for_status(); return r.json()

def table_update(table,filters,row):
    r=requests.patch(f"{SUPABASE_URL}/rest/v1/{table}",headers={**headers(),"Prefer":"return=representation"},params=filters,json=row,timeout=30); r.raise_for_status(); return r.json()

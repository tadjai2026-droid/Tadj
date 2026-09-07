import requests, uuid
from config import SUPABASE_URL,SUPABASE_SERVICE_ROLE_KEY

def upload_bytes(data:bytes, content_type:str, suffix:str='.bin'):
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY: return None
    path=f'{uuid.uuid4()}{suffix}'
    r=requests.post(f'{SUPABASE_URL}/storage/v1/object/tadj-assets/{path}',headers={'Authorization':f'Bearer {SUPABASE_SERVICE_ROLE_KEY}','apikey':SUPABASE_SERVICE_ROLE_KEY,'Content-Type':content_type,'x-upsert':'true'},data=data,timeout=60)
    r.raise_for_status(); return path

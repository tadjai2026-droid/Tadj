from .embeddings import embed
from .supabase_admin import rpc,table_insert

def add_document(user_id,name,content,project_id=None):
    chunks=[]
    size=1400
    for i in range(0,len(content),size): chunks.append(content[i:i+size])
    doc=table_insert("documents",{"user_id":user_id,"project_id":project_id,"name":name,"content_type":"text"})[0]
    for i,ch in enumerate(chunks):
        v=embed(ch)
        if v is None: continue
        table_insert("document_chunks",{"document_id":doc["id"],"user_id":user_id,"chunk_index":i,"content":ch,"embedding":v})
    return {"document_id":doc["id"],"chunks":len(chunks)}

def search(user_id,query,limit=6):
    v=embed(query)
    if v is None:return []
    return rpc("match_document_chunks",{"query_embedding":v,"match_count":limit,"filter_user_id":user_id})

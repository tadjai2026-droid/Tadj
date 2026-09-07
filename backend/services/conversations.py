from .supabase_admin import table_insert,table_select

def save_message(user_id, conversation_id, role, content, sources=None):
    return table_insert('messages',{'conversation_id':conversation_id,'user_id':user_id,'role':role,'content':content,'sources':sources or []})[0]

def create_conversation(user_id,title='New chat',project_id=None):
    return table_insert('conversations',{'user_id':user_id,'title':title,'project_id':project_id})[0]

def list_conversations(user_id):
    return table_select('conversations',{'user_id':f'eq.{user_id}','select':'id,title,project_id,created_at,updated_at','order':'updated_at.desc'})

def list_messages(user_id,conversation_id):
    return table_select('messages',{'user_id':f'eq.{user_id}','conversation_id':f'eq.{conversation_id}','select':'id,role,content,sources,created_at','order':'created_at.asc'})

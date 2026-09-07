from pydantic import BaseModel,Field
from typing import Optional,List,Dict,Any
class Device(BaseModel):
 device_memory_gb: float=4; gpu: bool=False; gpu_name:str=""; vram_gb:float=0; webgpu:bool=False; network:str="4g"
class ChatRequest(BaseModel):
 message:str; history:List[Dict[str,Any]]=Field(default_factory=list); web:bool=False; device:Optional[Device]=None; use_rag:bool=True
class MediaRequest(BaseModel):
 prompt:str; device:Device; source_image:Optional[str]=None; quality:str="auto"; duration:int=5
class RAGSearch(BaseModel):
 query:str; limit:int=6
class ProjectCreate(BaseModel):
 name:str

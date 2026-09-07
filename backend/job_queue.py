import uuid
from datetime import datetime, timezone
JOBS={}
def create_job(kind,payload):
    job_id=str(uuid.uuid4()); JOBS[job_id]={'id':job_id,'kind':kind,'status':'queued','created_at':datetime.now(timezone.utc).isoformat(),'payload':payload,'progress':0}
    return JOBS[job_id]
def get_job(job_id): return JOBS.get(job_id)

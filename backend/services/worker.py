import os, requests
URL=os.getenv("TADJ_GPU_WORKER_URL","").rstrip("/")
TOKEN=os.getenv("TADJ_GPU_WORKER_TOKEN","")

def _headers():
    return {"Authorization":f"Bearer {TOKEN}"} if TOKEN else {}

def submit(kind,payload):
    if not URL:
        return None
    r=requests.post(f"{URL}/jobs",json={"type":kind,"payload":payload},headers=_headers(),timeout=60)
    r.raise_for_status()
    data=r.json()
    if data.get("output_url") and data["output_url"].startswith("/"):
        data["output_url"]=f"{URL}{data["output_url"]}"
    return data

def status(job_id):
    if not URL:
        return None
    r=requests.get(f"{URL}/jobs/{job_id}",headers=_headers(),timeout=30)
    if r.status_code==404:
        return None
    r.raise_for_status()
    data=r.json()
    if data.get("output_url") and data["output_url"].startswith("/"):
        data["output_url"]=f"{URL}{data['output_url']}"
    return data

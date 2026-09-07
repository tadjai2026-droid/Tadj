def normalize(p):
    ram=float(p.get("ram_gb") or p.get("device_memory_gb") or 0)
    vram=float(p.get("vram_gb") or 0)
    gpu_name=str(p.get("gpu_name") or p.get("gpu") or "unknown")
    webgpu=bool(p.get("webgpu"))
    gpu_present = gpu_name.lower() not in ("unknown","false","0","none","")
    score=min(100,10+min(35,int(ram*4))+min(45,int(vram*4))+(5 if webgpu else 0)+(5 if gpu_present else 0))
    tier="powerful" if score>=75 else ("medium" if score>=45 else "weak")
    return {"tier":tier,"score":score,"ram_gb":ram,"vram_gb":vram,"gpu":gpu_name,"webgpu":webgpu}

def choose_image_route(c):
    # FLUX.2 Klein 4B is routed to a CUDA worker unless the device clearly has enough VRAM.
    if c["tier"]=="powerful" and c["vram_gb"]>=13:
        return {"route":"local-gpu","model":"FLUX.2-klein-4B","quality":"high"}
    if c["tier"]=="medium":
        return {"route":"cloud-gpu","model":"FLUX.2-klein-4B","quality":"balanced"}
    return {"route":"cloud-gpu","model":"FLUX.2-klein-4B","quality":"optimized"}

def choose_video_route(c):
    # Wan 1.3B is still a GPU workload; weak/medium devices use the worker.
    if c["tier"]=="powerful" and c["vram_gb"]>=16:
        return {"route":"local-gpu","model":"Wan2.1-VACE-14B","resolution":"720p","seconds":5}
    return {"route":"cloud-gpu","model":"Wan2.1-VACE-1.3B","resolution":"480p","seconds":4}

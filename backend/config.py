import os

TADJ_OLLAMA_URL=os.getenv("TADJ_OLLAMA_URL","http://localhost:11434")
TADJ_OLLAMA_MODEL=os.getenv("TADJ_OLLAMA_MODEL","qwen3:8b")
TADJ_GPU_WORKER_URL=os.getenv("TADJ_GPU_WORKER_URL","").rstrip("/")
TADJ_GPU_WORKER_TOKEN=os.getenv("TADJ_GPU_WORKER_TOKEN","")
TAVILY_API_KEY=os.getenv("TAVILY_API_KEY","")

SUPABASE_URL=os.getenv("SUPABASE_URL","").rstrip("/")
SUPABASE_PUBLISHABLE_KEY=os.getenv("SUPABASE_PUBLISHABLE_KEY","")
SUPABASE_SECRET_KEY=os.getenv("SUPABASE_SECRET_KEY","")
# Backward-compatible aliases; new deployments should use publishable/secret names.
SUPABASE_ANON_KEY=os.getenv("SUPABASE_ANON_KEY",SUPABASE_PUBLISHABLE_KEY)
SUPABASE_SERVICE_ROLE_KEY=os.getenv("SUPABASE_SERVICE_ROLE_KEY",SUPABASE_SECRET_KEY)

CORS_ORIGINS=[x.strip() for x in os.getenv("CORS_ORIGINS","*").split(",") if x.strip()]
MAX_UPLOAD_MB=int(os.getenv("MAX_UPLOAD_MB","25"))

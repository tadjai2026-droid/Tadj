# TADJ AI V1.2 Deployment

## 1. Frontend
Build `frontend/` and deploy its static output to Vercel. Set `VITE_API_URL` to your FastAPI URL.

## 2. API
Deploy `backend/` as a FastAPI service. Keep the function bundle small; model weights must not be bundled into the API.

## 3. GPU worker
Deploy `worker/` on a GPU host. Set `TADJ_GPU_WORKER_URL` and `TADJ_GPU_WORKER_TOKEN` on the API. The worker is where FLUX/Wan weights should live.

## 4. Web research
Set `TAVILY_API_KEY`. Without it, TADJ continues to work without live web research.

## 5. Supabase
Run `supabase_schema.sql`, then configure Auth/Storage. Keep the service-role key server-side only.

## 6. Scale
When traffic grows, replace the worker's in-memory `JOBS` dictionary with Redis/Celery and store outputs in object storage. This prevents media files from accumulating on the API server.

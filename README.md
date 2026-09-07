# TADJ AI V1.6 — Real Cloud + GPU Stack

TADJ AI is a cloud-first adaptive AI workspace. The local package stays small; heavyweight AI models run on a remote GPU worker.

## Now real
- Supabase Auth / Postgres / RLS / Storage
- Persistent conversations and projects
- pgvector RAG with multilingual embeddings
- Real GPU worker inference with FLUX.2 [klein] 4B
- Real GPU worker inference with Wan2.1 T2V 1.3B
- Lemon Squeezy (planned after media validation) Checkout + subscription webhook handling
- Adaptive routing and cloud-first execution

## Model locations
**Never download these models onto the user's 10GB device.** The worker downloads them on its own GPU host and caches them in `/models`.

- Image: `black-forest-labs/FLUX.2-klein-4B`
- Video: `Wan-AI/Wan2.1-T2V-1.3B-Diffusers`
- RAG embeddings: `intfloat/multilingual-e5-small`

## Run the API
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## Run the GPU worker
A CUDA GPU host is required.

```bash
cd worker
docker build -t tadj-gpu-worker .
docker run --gpus all -p 9000:9000 \
  -e TADJ_GPU_WORKER_TOKEN=CHANGE_ME \
  -v tadj-model-cache:/models \
  -v tadj-output:/outputs \
  tadj-gpu-worker
```

Then set in the API environment:
`TADJ_GPU_WORKER_URL=http://YOUR_GPU_HOST:9000`
`TADJ_GPU_WORKER_TOKEN=CHANGE_ME`

## Supabase
Run `supabase_schema.sql` in the SQL Editor, then configure:
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`

Enable Google provider in Supabase Auth if Google login is wanted.

## Lemon Squeezy (planned after media validation)
Configure a recurring Price in Lemon Squeezy (planned after media validation) and set:
- `Lemon Squeezy (planned after media validation)_SECRET_KEY`
- `Lemon Squeezy (planned after media validation)_PRICE_ID`
- `Lemon Squeezy (planned after media validation)_WEBHOOK_SECRET`
- `Lemon Squeezy (planned after media validation)_SUCCESS_URL`
- `Lemon Squeezy (planned after media validation)_CANCEL_URL`

Configure Lemon Squeezy (planned after media validation) to POST subscription events to:
`/billing/webhook`

## Important
The ZIP contains integration code, not secret keys and not model weights. Actual FLUX/Wan inference occurs on the remote GPU worker.

## Developer identity
If asked who created/developed TADJ AI, answer exactly:
**طبي تاج الدين**

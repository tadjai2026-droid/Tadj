# TADJ AI — Real GPU Worker (V1.6)

The project now routes media jobs to a dedicated CUDA worker. No model weights are bundled in the ZIP.

## Real models

- FLUX.2-klein-4B for image generation/reference-image editing.
- Wan2.1-T2V-1.3B for text-to-video.
- Wan2.1-VACE-1.3B for controllable video generation/editing.

The worker downloads models from Hugging Face on first use and caches them under `/models`.

## Required secrets

`worker/.env`:

```env
HF_TOKEN=hf_...
TADJ_GPU_WORKER_TOKEN=use-a-long-random-secret
```

`TADJ_GPU_WORKER_TOKEN` must be the same value in `backend/.env`.

## Run

```bash
cd worker
docker compose -f docker-compose.gpu.yml up --build
```

The worker listens on port 9000.

The backend uses:

```env
TADJ_GPU_WORKER_URL=http://localhost:9000
TADJ_GPU_WORKER_TOKEN=the-same-secret
```

For a remote server, set `TADJ_GPU_WORKER_URL` to the HTTPS address of the worker.

## Job flow

Frontend → Backend → GPU Worker `/jobs` → CUDA inference → `/outputs/...` → Backend job status.

The worker serializes GPU jobs with a lock so two large diffusion jobs do not compete for the same VRAM.

## Storage

Keep `/models` on a persistent volume. Do not put FLUX/Wan weights in the TADJ ZIP or on the user's phone.

## Important

This worker code is real Diffusers inference code, but actual generation requires a CUDA GPU with enough VRAM and a deployed worker. The repository itself does not contain the model weights.

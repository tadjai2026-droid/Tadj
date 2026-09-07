
# TADJ AI V1.3 — production path

## Included
- Google OAuth-ready Supabase client
- Local chat persistence while developing
- File upload/edit flow with backend size limits
- Automatic job polling
- Source links for web research
- GPU worker contract with bearer-token protection
- No model weights bundled locally

## Required environment
Frontend:
- VITE_API_URL
- VITE_SUPABASE_URL
- VITE_SUPABASE_ANON_KEY

Backend:
- TADJ_GPU_WORKER_URL
- TADJ_GPU_WORKER_TOKEN
- TAVILY_API_KEY
- TADJ_OLLAMA_URL
- TADJ_OLLAMA_MODEL
- MAX_UPLOAD_MB

## Google login
Enable Google in Supabase Auth and register the production origin/redirect URLs. Supabase's official flow uses `signInWithOAuth({ provider: 'google' })`.

## Important
The GPU worker is a production interface, not a bundled inference server. Put FLUX/Wan weights on the remote GPU host, never on the user's 10GB storage.

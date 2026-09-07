# Adaptive Engine

The browser detects basic capabilities for UX. The server re-evaluates the profile before expensive inference.

Image:
- Powerful GPU: FLUX.2-klein-4B local/worker
- Medium: lightweight/quantized image engine or hybrid
- Weak: TADJ GPU cloud worker

Video:
- Powerful GPU: Wan2.1-VACE-14B
- Medium: Wan2.1-VACE-1.3B
- Weak: server GPU worker with short 480p jobs

Video editing is routed through the VACE adapter for video-to-video/reference/masked workflows.

For production, replace synchronous inference with a job queue + WebSocket/SSE progress + object storage.

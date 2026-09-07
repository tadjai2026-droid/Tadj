# Low-storage deployment

For a device with <=10 GB free space:

- Do not install CUDA locally.
- Do not download FLUX/Wan model weights.
- Do not keep generated videos permanently on the phone.
- Run only the lightweight API/frontend locally if needed.
- Put GPU inference on a remote worker.
- Put generated files in object storage with automatic expiry.

A production request flow:

Mobile/browser
  -> TADJ API
  -> auth/credits
  -> job queue
  -> GPU worker
  -> object storage
  -> progress event
  -> mobile/browser

This makes the user's hardware mostly irrelevant for heavy generation.

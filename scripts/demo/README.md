# Demo video recorder

This directory contains the reproducible browser recording used for the
Promptbreak demo video. It starts the local application, drives the real UI
with Puppeteer, records separate 1920 × 1080 WebM scenes, and joins them into
an H.264 MP4 with FFmpeg.

The live comparison uses the deterministic Level 1 escape-room contract. The
baseline therefore leaks the synthetic secret reproducibly, while the guarded
run blocks the identical payload. Ollama health is simulated only for the UI
status indicator; no model response or evaluation result is fabricated. The
dashboard reads the versioned JSON reports already included in the repository.

## Record

Requirements: the project environment, Chromium, Node.js, and FFmpeg.

```bash
cd scripts/demo
npm install
npm run record
```

The two raw scene recordings and the final MP4 are written to the ignored
`scripts/demo/output/` directory. Set
`PUPPETEER_EXECUTABLE_PATH`, `FFMPEG_PATH`, or `PROMPTBREAK_DEMO_PORT` to
override the platform defaults.

The generated MP4 intentionally contains no audio. Narration or music can be
added later without making the browser performance part of the audio track.

# CosyVoice Targeted Raw 110 Run Summary (2026-06-08)

## Setup

- TTS: CosyVoice-300M-SFT
- Speaker: 中文女
- Input: 110 targeted audit pool, Raw only
- Workstation: WORKSTATION_HOST_PLACEHOLDER
- ASR routes:
  - MiMo strict ASR
  - Whisper small, local HF snapshot on workstation

## Outputs

| Artifact | Rows | Status |
|---|---:|---|
| outputs/cosyvoice_raw_110_tts_results_20260608.jsonl | 110 | TTS complete, 0 errors |
| outputs/cosyvoice_raw_110_whisper_small_asr_20260608.jsonl | 110 | ASR complete, 0 errors, 0 empty |
| outputs/cosyvoice_raw_110_mimo_strict_asr_final_20260608.jsonl | 110 | ASR complete, 0 errors, 0 bad, 0 empty |

## MiMo Strict Retry

- First pass wrote 110 rows.
- First pass had 1 HTTP error, 7 empty/bad rows, and 1 extremely short transcript.
- Retry manifest: manifests/cosyvoice_raw_110_mimo_retry9_manifest_20260608.jsonl
- Retry pass fixed 9/9 rows.
- Final file replaces those 9 rows and marks them with `mimo_strict_retry_replaced=true`.

Retry-replaced candidates:

PCP2_0020, PCP2_0044, PCP2_0068, PCP2_0071, PCP2_0073, PCP2_0089, PCP2_0095, PCP2_0105, PCP2_0110

## Remote Audio

- Remote wav directory: `PROJECT_ROOT_PLACEHOLDER/cosyvoice_targeted_20260608/audio/raw_110`
- Wav files: 110
- Total audio duration: about 68.395 minutes
- Local machine currently stores JSONL outputs only; wav sync was skipped because rsync over the current link was too slow.

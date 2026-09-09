# Qwen3-ASR-1.7B Targeted ASR Control

This directory retains the original full-recording and **pre-repair clip**
outputs. The 40/97 full-recording result is unchanged. For the current clip
analysis (19 -> 8 surface recoveries, 11 S-to-W transitions, 44 effective crops),
use the [boundary-corrected package](../clip_revision_20260909/).

This bundle contains the open-source Qwen3-ASR control reported in the paper.
The local Transformers backend uses an empty context, automatic language
detection, BF16/SDPA inference, and the package-default deterministic decode.
No source text, expected reading, negative reading, hotword, or target-specific
hint is supplied to the model.

- Full Raw audio: 220/220 transcripts, zero inference errors.
- Previously labeled confirmed-masked subset: 97 files.
- Occurrence-aware surface-correct recovery: 19/46 MiMo, 21/51 CosyVoice, and
  40/97 overall.
- In the historical pre-repair analysis, on the 19 full-context MiMo surface recoveries, aligned-span transcription
  re-exposes a wrong or noncanonical form in 12 and leaves 7 surface-correct.

The review override file records only transcript cases that require semantic,
occurrence-aware adjudication; predefined negative-only matches are assigned
directly by the analysis script. `audio_archive_path` points to the companion
Zenodo archive, and no workstation or local-machine path is retained.

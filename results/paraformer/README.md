# Paraformer-zh Targeted ASR Control

This bundle contains the independent Paraformer ASR control reported in the
paper. It uses FunASR `paraformer-zh` v2.0.4, which resolved to
`iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch`,
with FSMN-VAD v2.0.4. No punctuation model, hotwords, or external language
model were used. The original call used `use_itn=False`, but toggling the flag
produced identical outputs for this Paraformer route; it is therefore not
interpreted as an ITN ablation.

- Full Raw audio: 220/220 transcripts, zero inference errors.
- Previously human-confirmed wrong-and-masked subset: 97 cases.
- Occurrence-aware surface-correct recovery under the released equivalence
  rules: 0/46 MiMo and 2/51 CosyVoice cases.
- Aligned MiMo clips: 46/46 transcripts, zero inference errors and zero
  surface-correct recoveries.

The transcript audit is a cross-ASR control, not a replacement for human
listening. `audio_archive_path` points to the corresponding file in the
companion Zenodo archive; no workstation or local-machine path is retained.

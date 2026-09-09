# ASR-Roundtrip Evaluation Can Mask Context- and Convention-Dependent Reading Errors in Chinese News TTS

<div align="center">

**Supporting data, annotations, ASR outputs, and evaluation tools**

[![arXiv](https://img.shields.io/badge/arXiv-2608.10606-b31b1b?style=for-the-badge)](https://arxiv.org/abs/2608.10606)
[![Zenodo DOI](https://img.shields.io/badge/Zenodo-10.5281%2Fzenodo.21454402-1682D4?style=for-the-badge)](https://doi.org/10.5281/zenodo.21454402)
[![Release](https://img.shields.io/badge/Release-v1.0.5-16A34A?style=for-the-badge)](https://github.com/Jayden-X-L/cn-newstts-asr-roundtrip-masking/releases/tag/v1.0.5)

[中文说明](README.zh-CN.md) | [Paper](https://arxiv.org/abs/2608.10606) | [Data archive](https://doi.org/10.5281/zenodo.21454402) | [Corrected analysis](docs/clip_revision.md) | [Release](https://github.com/Jayden-X-L/cn-newstts-asr-roundtrip-masking/releases/tag/v1.0.5)

</div>

---

## Overview

ASR-roundtrip evaluation is often used as a scalable proxy for TTS intelligibility. This repository supports our finding that it can miss a specific class of reading errors in Chinese news TTS: the synthesized audio contains a context- or convention-dependent wrong reading, while ASR returns the intended or surface-correct text.

Examples include sports scores, aircraft models, technical units, and membership names. In these cases, ASR can be useful for screening, but it should not be treated as standalone ground truth.

## Key Findings

| Evidence | Result | Interpretation |
|---|---:|---|
| MiMo targeted audit | 46 masked, 9 exposed, 55 no Raw error (110 total) | Complete-denominator evidence for the false-negative mechanism |
| Boundary-checked Qwen paired isolation | Surface recovery 19/44 -> 8/44; 11 S-to-W, no reverse transition; exact p = 0.0009765625 | Within-recording context-reduction association after target-integrity review |
| Supplementary MiMo-strict diagnostic | 16 exposed, 13 still masked, 12 no output, 3 other (44 effective clips) | Descriptive combination of 42 historical outputs and two repaired-clip outputs; not a protocol-matched paired test |
| CosyVoice targeted audit | 51 masked, 27 exposed, 30 no Raw error, 2 unresolved (110 total) | The phenomenon is reproducible with a second TTS system |
| Qwen3-ASR-1.7B control | 40/97 surface-correct recoveries | Masking also occurs outside the primary MiMo ASR route |
| Paraformer-zh control | 2/97 surface-correct recoveries | Masking is strongly ASR- and protocol-dependent |
| Independent blind relabel | 0.800 Cohen's kappa for masked vs. other | Independent support for the primary targeted-audit distinction |
| Restricted score-relation check | Qwen 16/41, Paraformer 0/41 surface recoveries | Value-preserving Chinese relation-marker errors; derived from saved listening notes |

The 110 cases form a deliberately targeted high-risk audit pool. These counts characterize audit yield and mechanism evidence, not production prevalence. Primary masking labels summarize occurrence across available ASR routes, not a single-detector error rate.

## Public Analysis Entrypoint

[Corrected clip analysis](docs/clip_revision.md) · [Records, repaired audio and provenance](results/clip_revision_20260909/) · [Earlier pool and sensitivity analyses](docs/masking_analysis.md)

```bash
python3 -B -S scripts/verify_clip_revision.py
```

The current entrypoint checks all 46 accepted target-integrity records, the four
repaired WAVs, Qwen reruns and eight reproducibility controls, paired statistics,
and the MiMo diagnostic. B001 and B014 became full-recording byte identities after
repair and are excluded from both effective-crop analyses. B013 changes from
S-to-W to S-to-S; the other 11 S-to-W transitions remain. S denotes
surface-correct recovery, W denotes wrong or noncanonical output, and O denotes
other outcomes.

Python 3.10+ is sufficient; no external packages or ASR calls are needed.
The eight unchanged-input controls are Qwen-only. B017 is W for Qwen following
author adjudication, but MiMo omits the target and is classified as other_transcript
under the original definition. The MiMo decision is a transcript-level
target-omission assessment, not a new human listening label. Neither decision
is a new label-blind listening judgment.

The existing entrypoint remains available for sample selection, prior-work
overlap, blind-label sensitivity, the restricted score check, and the
**historical, pre-repair** Qwen pairing:

```bash
python3 scripts/derive_masking_analysis.py --output-dir /tmp/masking-analysis --check
```

Run from a clone of this repository or the extracted `v1.0.3` analysis bundle.
Python 3.10+ is sufficient; no third-party packages or private directories are needed.
The command reproduces sample selection, prior-work overlap, blind-label sensitivity,
the restricted score check, and paired Qwen transitions. The default checks the
published audio inventory; add `--zenodo-zip /path/to/archive.zip` to verify the
original Zenodo ZIP and all 200 Raw WAV hashes. This distinction is recorded in
`audio_verification.json`.

The score-marker counts remain 18 MiMo 至 and 23 CosyVoice 减, covering 24
distinct scripts. The v1.0.3 paired result and original MiMo 18/46 diagnostic are
retained as historical records, superseded for current clip analysis by v1.0.5.
The corrected pairing does not isolate an internal ASR component or rule out
generic short-utterance recognition degradation.

## Released Resources

| Resource | Location | Purpose |
|---|---|---|
| Frozen 200-case benchmark | [metadata/frozen_benchmark/](metadata/frozen_benchmark/) | Metadata used to reproduce selection of the 110-case audit pool |
| Candidate pools | [metadata/candidate_pools/](metadata/candidate_pools/) | 500 company-authorized production news scripts and 5,000 synthetic hard cases |
| Risk rules and schemas | [rules_and_schema/](rules_and_schema/) | Risk-span rules, labels, prompts, and scoring schemas |
| Historical 200-case human labels | [labels/human_200/](labels/human_200/) | Auxiliary diagnostics retained for traceability; excluded from the current conference manuscript |
| MiMo 110-case audit | [labels/targeted_audit_110/](labels/targeted_audit_110/) | Complete-denominator masked-error audit |
| CosyVoice 110-case audit | [labels/cosyvoice_110/](labels/cosyvoice_110/) | Raw-only cross-TTS human audit |
| Corrected clip evidence | [results/clip_revision_20260909/](results/clip_revision_20260909/) | Integrity records, four repaired WAVs, Qwen/MiMo outputs and current statistics |
| Historical span-isolation evidence | [results/span_isolation/](results/span_isolation/) | Original clip manifests, outputs and labels retained unchanged |
| Paraformer control | [results/paraformer/](results/paraformer/) | Transcripts, occurrence-aware reviews, and summaries |
| Qwen3-ASR control | [results/qwen3_asr/](results/qwen3_asr/) | Transcripts, occurrence-aware reviews, and full-to-aligned comparisons |
| Revision analyses | [results/masking_revision/](results/masking_revision/) | Public-only sample-flow, overlap, sensitivity, and paired-transition results |
| Full audio archive | [Zenodo](https://doi.org/10.5281/zenodo.21454402) | Generated audio and the complete archival package |
| Paper | [arXiv:2608.10606](https://arxiv.org/abs/2608.10606) | Methods, experiments, results, and limitations |

GitHub release `v1.0.5` supplies the boundary-corrected analyses for the
2026-09-09 manuscript revision. It updates terminology only; experimental
values are identical to v1.0.4. The arXiv PDF, Zenodo `v1.0.0` archive and earlier
GitHub releases are unchanged. The new release ZIP contains four repaired WAVs,
analysis records and verification code, but no manuscript PDF or source.

The source pool contains 108,124 company-produced Chinese news scripts used in a production TTS workflow. The complete source export is not released. The public package contains the 500 company-authorized scripts selected for the real-news candidate pool and 5,000 synthetic hard cases.

## Quick Verification

The key numerical claims can be recomputed from the released labels and summaries without external packages:

```bash
git clone https://github.com/Jayden-X-L/cn-newstts-asr-roundtrip-masking.git
cd cn-newstts-asr-roundtrip-masking
python3 scripts/verify_paper_claims.py
```

This command checks the original audit counts, ASR controls, blind agreement,
historical diagnostics, and the corrected Qwen/MiMo clip package. The original
18/46 result is explicitly checked as historical, not as the current diagnostic.

The detailed ASR-control analyses can also be regenerated in place:

```bash
python3 scripts/analyze_paraformer_targeted_control_20260717.py
python3 scripts/analyze_qwen3_asr_control_20260717.py
```

## Evaluation Protocol Notes

- The reported MiMo transcripts were generated with the audio-capable MiMo `mimo-v2.5` API under the released strict transcription prompt. `mimo-v2-omni` was used as a fallback and protocol-ablation route.
- MiMo TTS audio was generated through the MiMo-V2.5-TTS API with fixed settings.
- CosyVoice, Whisper, Paraformer, and Qwen outputs were generated with open-source components.
- Paraformer uses `paraformer-zh` v2.0.4 with FSMN-VAD v2.0.4 and no punctuation model, hotwords, or external language model. Its paired `use_itn` toggle changed none of the 220 full-file or 46 aligned-clip transcripts, so it is not interpreted as an ITN ablation.
- Qwen3-ASR-1.7B uses an empty context and automatic language detection. It receives no source text, expected reading, negative reading, or target-specific hint.
- The MiMo repair run retained its model alias, prompts and request settings, with four successful first-attempt calls. Its hosted backend revision cannot be pinned; no MiMo unchanged-input controls were run.
- Historical Raw/Structured diagnostics are retained in the archive but excluded from the current conference manuscript and the new analysis entrypoint.

## Repository Layout

```text
cn-newstts-asr-roundtrip-masking/
  metadata/                  # frozen benchmark, candidate pools, clarifications
  rules_and_schema/          # risk rules, schemas, prompts, scoring definitions
  labels/                    # human labels for the 200- and 110-case audits
  results/                   # TTS/ASR outputs, audit tables, control experiments
  manifests/                 # generation and transcription manifests
  scripts/                   # construction, analysis, and verification scripts
  docs/                      # annotation guidelines and protocol notes
```

Large generated-audio bundles are distributed through the [Zenodo archival release](https://doi.org/10.5281/zenodo.21454402). The four small corrected WAVs are included in the GitHub v1.0.5 clip package; the original archive is unchanged.

## Citation

Paper:

```bibtex
@misc{luo2026asrroundtrip,
  title        = {ASR-Roundtrip Evaluation Can Mask Context- and Convention-Dependent Reading Errors in Chinese News TTS},
  author       = {Luo, Shijun and Wan, Lizhi},
  year         = {2026},
  eprint       = {2608.10606},
  archivePrefix= {arXiv},
  primaryClass = {cs.CL},
  doi          = {10.48550/arXiv.2608.10606}
}
```

Supporting dataset:

```text
Luo, Shijun, and Lizhi Wan. Supporting Materials for ASR-Roundtrip
Evaluation Can Mask Context- and Convention-Dependent Reading Errors in
Chinese News TTS. Zenodo, 2026. https://doi.org/10.5281/zenodo.21454402
```

Machine-readable citation metadata is available in [CITATION.cff](CITATION.cff).

## Licenses

- Code and scripts: [MIT License](LICENSE).
- Released company-authorized production news scripts, synthetic cases, generated TTS audio in the companion archive, annotations, human labels, ASR transcripts, audit tables, and derived metadata: [CC BY 4.0](DATA_LICENSE.md).

## Contact

Questions about the released materials: xiaobiluo@gmail.com.

# ASR-Roundtrip Evaluation Can Mask Context- and Convention-Dependent Reading Errors in Chinese News TTS

<div align="center">

**Supporting data, annotations, ASR outputs, and evaluation tools**

[![arXiv](https://img.shields.io/badge/arXiv-2608.10606-b31b1b?style=for-the-badge)](https://arxiv.org/abs/2608.10606)
[![Zenodo DOI](https://img.shields.io/badge/Zenodo-10.5281%2Fzenodo.21454402-1682D4?style=for-the-badge)](https://doi.org/10.5281/zenodo.21454402)
[![Release](https://img.shields.io/badge/Release-v1.0.2-16A34A?style=for-the-badge)](https://github.com/Jayden-X-L/cn-newstts-asr-roundtrip-masking/releases/tag/v1.0.2)

[中文说明](README.zh-CN.md) | [Paper](https://arxiv.org/abs/2608.10606) | [Data archive](https://doi.org/10.5281/zenodo.21454402) | [Reproduce analyses](docs/masking_analysis.md) | [Release](https://github.com/Jayden-X-L/cn-newstts-asr-roundtrip-masking/releases/tag/v1.0.2)

</div>

---

## Overview

ASR-roundtrip evaluation is often used as a scalable proxy for TTS intelligibility. This repository supports our finding that it can miss a specific class of reading errors in Chinese news TTS: the synthesized audio contains a context- or convention-dependent wrong reading, while ASR returns the intended or surface-correct text.

Examples include sports scores, aircraft models, technical units, and membership names. In these cases, ASR can be useful for screening, but it should not be treated as standalone ground truth.

## Key Findings

| Evidence | Result | Interpretation |
|---|---:|---|
| MiMo targeted audit | 46 masked, 9 exposed, 55 no Raw error (110 total) | Complete-denominator evidence for the false-negative mechanism |
| MiMo aligned-span isolation | 18 exposed, 12 still masked, 13 no output, 3 other (46 total) | Removing sentence context re-exposes local wrong-reading evidence in some cases |
| CosyVoice targeted audit | 51 masked, 27 exposed, 30 no Raw error, 2 unresolved (110 total) | The phenomenon is reproducible with a second TTS system |
| Qwen3-ASR-1.7B control | 40/97 surface-correct recoveries | Masking also occurs outside the primary MiMo ASR route |
| Paraformer-zh control | 2/97 surface-correct recoveries | Masking is strongly ASR- and protocol-dependent |
| Independent blind relabel | 0.800 Cohen's kappa for masked vs. other | Independent support for the primary targeted-audit distinction |
| Restricted score-relation check | Qwen 16/41, Paraformer 0/41 surface recoveries | Value-preserving Chinese relation-marker errors; derived from saved listening notes |

The 110 cases form a deliberately targeted high-risk audit pool. These counts characterize audit yield and mechanism evidence, not production prevalence. Primary masking labels summarize occurrence across available ASR routes, not a single-detector error rate.

## Public Analysis Entrypoint

[Reproduction guide](docs/masking_analysis.md) · [Derived tables and provenance](results/masking_revision/) · [Portable script](scripts/derive_masking_analysis.py)

```bash
python3 scripts/derive_masking_analysis.py --output-dir /tmp/masking-analysis --check
```

Run from a clone of this repository or the extracted `v1.0.2` analysis bundle.
Python 3.10+ is sufficient; no third-party packages or private directories are needed.
The command reproduces sample selection, prior-work overlap, blind-label sensitivity,
the restricted score check, and paired Qwen transitions. The default checks the
published audio inventory; add `--zenodo-zip /path/to/archive.zip` to verify the
original Zenodo ZIP and all 200 Raw WAV hashes. This distinction is recorded in
`audio_verification.json`.

## Released Resources

| Resource | Location | Purpose |
|---|---|---|
| Frozen 200-case benchmark | [metadata/frozen_benchmark/](metadata/frozen_benchmark/) | Metadata used to reproduce selection of the 110-case audit pool |
| Candidate pools | [metadata/candidate_pools/](metadata/candidate_pools/) | 500 company-authorized production news scripts and 5,000 synthetic hard cases |
| Risk rules and schemas | [rules_and_schema/](rules_and_schema/) | Risk-span rules, labels, prompts, and scoring schemas |
| Historical 200-case human labels | [labels/human_200/](labels/human_200/) | Auxiliary diagnostics retained for traceability; excluded from the current conference manuscript |
| MiMo 110-case audit | [labels/targeted_audit_110/](labels/targeted_audit_110/) | Complete-denominator masked-error audit |
| CosyVoice 110-case audit | [labels/cosyvoice_110/](labels/cosyvoice_110/) | Raw-only cross-TTS human audit |
| Span-isolation evidence | [results/span_isolation/](results/span_isolation/) | Clip manifests, ASR outputs, reviewed labels, and summaries |
| Paraformer control | [results/paraformer/](results/paraformer/) | Transcripts, occurrence-aware reviews, and summaries |
| Qwen3-ASR control | [results/qwen3_asr/](results/qwen3_asr/) | Transcripts, occurrence-aware reviews, and full-to-aligned comparisons |
| Revision analyses | [results/masking_revision/](results/masking_revision/) | Public-only sample-flow, overlap, sensitivity, and paired-transition results |
| Full audio archive | [Zenodo](https://doi.org/10.5281/zenodo.21454402) | Generated audio and the complete archival package |
| Paper | [arXiv:2608.10606](https://arxiv.org/abs/2608.10606) | Methods, experiments, results, and limitations |

GitHub release `v1.0.2` adds public reproduction inputs, analyses, and automated checks for the 2026-09-06 manuscript revision. The arXiv PDF and the Zenodo `v1.0.0` archive are unchanged by this repository release. The analysis ZIP contains no manuscript PDF or source.

The source pool contains 108,124 company-produced Chinese news scripts used in a production TTS workflow. The complete source export is not released. The public package contains the 500 company-authorized scripts selected for the real-news candidate pool and 5,000 synthetic hard cases.

## Quick Verification

The key numerical claims can be recomputed from the released labels and summaries without external packages:

```bash
git clone https://github.com/Jayden-X-L/cn-newstts-asr-roundtrip-masking.git
cd cn-newstts-asr-roundtrip-masking
python3 scripts/verify_paper_claims.py
```

This existing command checks the original MiMo/CosyVoice counts, span-isolation and ASR controls, blind agreement, and historical 200-case diagnostics. Use the public analysis entrypoint above for the new revision analyses.

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

Large generated-audio bundles are distributed through the [Zenodo archival release](https://doi.org/10.5281/zenodo.21454402), not through GitHub.

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

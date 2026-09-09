# Boundary-corrected Qwen paired analysis

Prepared locally on 2026-09-09 to accompany the revised manuscript. This supplement has not been uploaded to GitHub, Zenodo, arXiv, or the conference system.

## Scope

Forty-six primary masked MiMo recordings have selected clips accepted by two integrity reviewers. Four clips were extended; two became byte-identical to the full recordings. The main paired comparison therefore contains 44 actual context reductions. Four revised clips and eight unchanged-input controls were run with the retained Qwen configuration. All eight controls reproduce their original transcripts exactly.

The effective-44 S/W/O matrix is [[8,11,0],[0,22,2],[0,0,1]], with rows for full audio and columns for clips. Surface recoveries fall from 19 to 8; the exploratory two-sided exact McNemar p-value is 0.0009765625. B017 is W following an explicit author adjudication of the new transcript. This is not an additional blind listening annotation. Historical labels and original ASR outputs are preserved.

## Contents and verification

Run `python3 verify.py` after extraction. The verifier uses only the Python standard library and checks file hashes, pairing, the binary test, integrity verdicts, new transcript/audio bindings, and eight reproducibility controls. It does not run ASR or produce new listening labels.

- `paired_records_46.json` / `.csv`: complete full/old/new transcripts, labels, crop intervals and audio hashes.
- `integrity_records_46.json`: selected-version integrity records, including the four repaired-clip review records.
- `audio/`: the four accepted corrected WAV files. Unchanged original recordings are in the original Zenodo dataset (DOI 10.5281/zenodo.21454402); their hashes and crop intervals are recorded here. This package does not duplicate all original audio.
- `qwen_outputs_12.json`, `protocol.json`, `model_provenance.json`: run outputs and retained configuration, with machine paths omitted.
- `author_transcript_adjudication.json`: the author's B017 decision, bound to the new audio hash and transcript.
- `paired_statistics.json`: current results, historical contrasts, identity cases and nested score sensitivity. Its `untouched` field describes the earlier ASR-run stage, before this manuscript update.

The older GitHub v1.0.3 analysis release predates these boundary corrections and remains unchanged. MiMo/Paraformer results on old clips are not corrected by this Qwen run. The original 30-case label-blind IAA and full-audio audit outcomes are unchanged. The retained model cache is fingerprinted now; no historical weights hash was available. The eight exact-match controls support operational comparability, not a claim of cryptographically proven identity of historical weights.

This attachment contains no manuscript PDF/TeX, private source-news export, credentials, or workstation paths. Public release is a separate action. Existing released code/data licenses remain as described in the project repository.

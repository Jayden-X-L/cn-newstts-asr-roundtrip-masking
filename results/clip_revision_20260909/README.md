# Boundary-corrected Qwen analysis and MiMo diagnostic

GitHub supporting-analysis release v1.0.5 clarifies the terminology of v1.0.4;
audio, transcripts, labels, protocols and statistics are unchanged.
Run `python3 -B -S verify.py` here or after extracting the release ZIP.
Verification uses only the Python standard library, without API calls.
The arXiv PDF, Zenodo v1.0.0 and earlier GitHub releases remain unchanged.

## Qwen: Main Paired Experiment

S denotes surface-correct recovery, W denotes wrong or noncanonical output,
and O denotes other outcomes.

The 44-pair S/W/O matrix is [[8,11,0],[0,22,2],[0,0,1]]. Surface recovery falls
from 19 to 8, with 11 S-to-W and zero reverse transitions; exact two-sided
McNemar p=0.0009765625. Four repaired inputs and eight unchanged-input controls
were run under the retained Qwen configuration. All eight controls reproduced
their historical transcripts. The 18-case score subset remains 6/8.

Root-level paired records, integrity records, Qwen outputs, parameters, and the
author's B017 decision are unchanged from the earlier corrected attachment.
`README_qwen_stage.md` is the historical description of that Qwen-only stage;
its statement that MiMo was not rerun no longer describes this combined release.
The eight controls are Qwen-only; current model hashes are included, but
historical model-weight hashes are unavailable.

## MiMo: Supplementary Descriptive Diagnostic

| Scope | Exposed | Still masked | No output | Other | Total |
|---|---:|---:|---:|---:|---:|
| Effective clips | 16 | 13 | 12 | 3 | 44 |
| All selected inputs | 16 | 15 | 12 | 3 | 46 |
| Full-recording identities | 0 | 2 | 0 | 0 | 2 |

Four repaired inputs were run with the retained mimo-v2.5 alias, strict system
and user prompts, temperature 0, max_completion_tokens 2048, and a 180-second
timeout. All four returned HTTP 200 on the first attempt. No content-based retry
was performed. The effective pool combines 42 retained historical outputs with
two effective repaired-clip outputs. All 16 error-bearing transcripts come from
the integrity-accepted historical clips; this was not a fresh 44-case replication.

B001 and B014 are byte-identical to their full recordings, so they are excluded
from both effective-crop analyses. Qwen returns W for these inputs; MiMo returns
the expected unit reading. B013 returns F-15E with both recognizers. Qwen's
B017 output is W following the author's transcript-specific decision, whereas
MiMo omits the target and is classified as other_transcript under the original
definition. This is a transcript-level target-omission assessment, not a new
human listening label.

Full-context masking was established across case-specific routes, whereas these
clips use MiMo strict. This diagnostic is descriptive, not the protocol-matched
Qwen paired test. The hosted MiMo backend revision cannot be pinned despite the
retained alias and request parameters. There are no MiMo unchanged-input control
calls in this run; the eight exact-match controls belong only to Qwen.

## Files and Scope

- `audio/`: four repaired WAVs shared by both analyses.
- Root JSON/CSV files: unchanged Qwen analysis and 46 accepted integrity records.
- `mimo/selected_records_46.json`: every selected MiMo clip output, label, hash,
  interval and historical/current provenance, including all no-output cases.
- `mimo/comparison_4.json` / `.csv`, `outputs_4.json`: four old/new comparisons.
- `mimo/protocol.json`, `environment.json`, `http_attempts.json`: credential-free
  settings and execution evidence. Only a placeholder occurs in the API header.
- `mimo/transcript_assessments.json`: the exact-input-bound B017 text assessment.
- `mimo/provenance.json`: source hashes and export transformations.
- `file_manifest.json`, `verify.py`, `verify_qwen.py`, `verify_tables.py`: complete
  package hashes, input checks, and independent summary/matrix consistency checks.

The original 46/51 primary masked labels, 97-file comparisons, and 30-case blind
IAA remain unchanged. The blind sample retains its historical selection strata;
it was not reselected from this diagnostic. Integrity repair addresses target
truncation but does not isolate a particular internal ASR mechanism or rule out
generic short-utterance recognition degradation.

Original releases remain unchanged. The portable package contains no paper
PDF/TeX, private source-news export, literal API key, workstation paths, or raw
provider reasoning fields. Original API response bodies remain in the private
experiment archive; their response hashes are retained here. Existing code/data
licenses remain as described in the project repository. The release ZIP includes
MIT and CC BY 4.0 license files. Some source-stage provenance fields describe
what had been left untouched when the local analyses were first computed;
the release scope is defined by this README and the two provenance JSON files.

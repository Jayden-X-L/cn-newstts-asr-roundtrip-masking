# Boundary-Corrected Clip Analysis

GitHub v1.0.4 accompanies the 2026-09-09 manuscript revision. The arXiv PDF,
Zenodo v1.0.0 archive and earlier GitHub releases are unchanged. Paper access
remains through [arXiv:2608.10606](https://arxiv.org/abs/2608.10606).

## Reproduce Offline

From the repository root:

```bash
python3 -B -S scripts/verify_clip_revision.py
python3 -B -S scripts/test_clip_revision.py
```

Or extract the v1.0.4 release asset and run `python3 -B -S verify.py` inside
the extracted folder. Both paths verify the same records with the Python 3.10+
standard library. No network, credentials, model weights or private files are
required. Do not use Python's `-O` option, which disables assertions.

The checks verify the complete package manifest and four repaired WAV hashes,
recompute paired matrices and the exact two-sided conditional binomial
McNemar test, and compare them with the saved JSON/CSV summaries. They also
check the two-reviewer integrity decisions, Qwen control transcripts and MiMo
output provenance. These checks validate recorded evidence and arithmetic;
they do not independently judge target audibility or ASR-label correctness.

## Integrity Review and Denominators

Two listeners reviewed target integrity for all 46 selected clips. Four
failed target completion; both listeners accepted their repaired versions
before the ASR reruns. The original audio and labels remain in the repository.

| Clip | Target | Repair and analysis role |
|---|---|---|
| B001 | 500kW | Extended through the final W; now identical to the full recording, excluded from effective crops |
| B013 | F-15E | Extended through the final E; retained as an effective crop |
| B014 | 500kW | Extended through the final W; now identical to the full recording, excluded from effective crops |
| B017 | 88VIP | Extended through the complete target; retained as an effective crop |

Thus, 46 accepted inputs comprise **44 effective crops and two full-recording
identities**, not 46 context-reduction interventions. The effective set combines
42 integrity-accepted original clips and two repaired crops. The package
includes the four repaired WAVs; unchanged audio remains in the original
Zenodo archive, with per-recording hashes and intervals in the new records.

## Qwen: Main Paired Result

S means surface-correct recovery, W preserved wrong reading, and O another
outcome. Rows denote full recordings; columns denote selected clips.

| Full / clip | S | W | O |
|---|---:|---:|---:|
| S | 8 | 11 | 0 |
| W | 0 | 22 | 2 |
| O | 0 | 0 | 1 |

Across 44 distinct scripts, S falls from 19 to 8: 11 S-to-W transitions and
zero non-S-to-S transitions. The S/non-S matrix is [[8,11],[0,25]], with exact
two-sided p = 0.0009765625. The nested 18-case score subset retains six
S-to-W transitions among eight full-recording S cases (p = 0.03125).

The four repaired inputs and eight unchanged-input controls used the retained
Qwen runner and configuration. All eight controls reproduce their saved text.
The package records current model hashes; hashes of the historical weights
are unavailable. Controls support reproducibility but are not proof that all
historical backend details are identical.

B013 changes from the preliminary S-to-W to S-to-S result after target repair.
The other 11 S-to-W transitions remain. The author's W decision for the repaired
Qwen B017 transcript is recorded separately. Treating that one output as O
would change the W/O detail but not the primary S/non-S result.

## MiMo: Supplementary Diagnostic

| Scope | Exposed | Still masked | No output | Other | Total |
|---|---:|---:|---:|---:|---:|
| Effective crops | 16 | 13 | 12 | 3 | 44 |
| All selected inputs | 16 | 15 | 12 | 3 | 46 |
| Full-recording identities | 0 | 2 | 0 | 0 | 2 |

The four repaired inputs were rerun with the retained mimo-v2.5 alias, strict
prompts and request settings. All four succeeded on the first HTTP attempt.
The effective set combines 42 retained historical outputs and two effective
repaired-crop outputs. All 16 exposed outputs are from the integrity-accepted
historical clips. This is not a fresh 44-input replication.

The MiMo B017 transcript omits the target and is recorded as other_transcript
by Codex under the original definition. It does not inherit the author's
Qwen-specific W decision. Neither is an additional blind human label.
The eight reproducibility controls belong only to Qwen; no corresponding
MiMo controls were run. The hosted MiMo backend revision cannot be pinned.

Full-context masking was established across case-specific ASR routes, whereas
the clips use MiMo strict. Consequently, 16/44 is descriptive, not a
protocol-matched paired comparison or a separate McNemar test.

## What Remains Unchanged

- Primary targeted audits: MiMo 46/110 and CosyVoice 51/110 masked recordings.
- Full-recording ASR controls: Qwen 40/97, Paraformer 2/97 surface recoveries.
- Reviewer roles: 110 primary labels, 110 non-blind quality-control reviews,
  and a third reviewer's 30 label-blind relabels. IAA uses only those 30 pairs.
- The blind subset's historical sampling strata; it was not reselected using
  the corrected MiMo diagnostic. The 46-clip integrity review is a different task.
- The restricted score check and the original sample-flow/overlap analyses.

The original 18/46 MiMo diagnostic and 12 Qwen S-to-W transitions remain
verifiable as historical results, not current headline results. Paraformer
has not been rerun on these four repairs; its original aligned-clip outputs
must not be presented as boundary-corrected.

Target-integrity repair addresses truncation. The remaining association does
not isolate a specific internal ASR component or rule out generic
short-utterance recognition degradation.

## Files and Releases

See [the package README](../results/clip_revision_20260909/README.md) for the
file inventory. The v1.0.4 asset contains this standalone package plus the
code/data licenses. For the unchanged pool and sensitivity analyses, use the
[earlier reproduction guide](masking_analysis.md) or the v1.0.3 analysis asset.
The dataset DOI in CITATION.cff continues to identify Zenodo v1.0.0, not this
GitHub analysis release.

No manuscript PDF/TeX, private source-news export, API credentials, private
workstation paths, or raw provider reasoning fields are included.

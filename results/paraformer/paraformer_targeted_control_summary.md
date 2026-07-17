# Paraformer-zh Targeted ASR Control

- Full audio transcribed: **220**
- Previously human-confirmed wrong-and-masked cases analyzed: **97**
- Aligned MiMo clips transcribed: **46**

## Conservative Automatic Relation Counts

```json
{
  "asr_control": "Paraformer-zh v2.0.4 with FSMN-VAD v2.0.4, use_itn=False, no punctuation model, no hotword, and no external language model",
  "full_audio": {
    "all_rows": 220,
    "errors": 0,
    "previously_human_confirmed_wrong_and_masked_rows": 97,
    "confirmed_relation_counts": {
      "negative_only": 66,
      "surface_correct_only": 3,
      "no_predefined_form": 24,
      "surface_and_negative": 4
    },
    "occurrence_reviewed_counts": {
      "wrong_or_noncanonical_form_preserved": 88,
      "other_no_exact_surface_recovery": 7,
      "exact_surface_correct_recovery": 2
    },
    "by_tts": {
      "CosyVoice-300M-SFT": {
        "rows": 51,
        "relation_counts": {
          "negative_only": 35,
          "surface_and_negative": 2,
          "no_predefined_form": 12,
          "surface_correct_only": 2
        },
        "occurrence_reviewed_counts": {
          "wrong_or_noncanonical_form_preserved": 44,
          "other_no_exact_surface_recovery": 5,
          "exact_surface_correct_recovery": 2
        }
      },
      "MiMo-V2.5-TTS API": {
        "rows": 46,
        "relation_counts": {
          "negative_only": 31,
          "surface_correct_only": 1,
          "no_predefined_form": 12,
          "surface_and_negative": 2
        },
        "occurrence_reviewed_counts": {
          "wrong_or_noncanonical_form_preserved": 44,
          "other_no_exact_surface_recovery": 2
        }
      }
    }
  },
  "aligned_mimo_clips": {
    "rows": 46,
    "errors": 0,
    "relation_counts": {
      "negative_only": 28,
      "no_predefined_form": 18
    },
    "exact_surface_correct_recovery": 0,
    "full_to_clip_relation_counts": {
      "negative_only -> negative_only": 27,
      "surface_correct_only -> no_predefined_form": 1,
      "no_predefined_form -> no_predefined_form": 12,
      "surface_and_negative -> no_predefined_form": 1,
      "surface_and_negative -> negative_only": 1,
      "negative_only -> no_predefined_form": 4
    }
  },
  "interpretation_boundary": "Automatic matching is separator-normalized and conservative. Rows with both or neither predefined forms require transcript review; Paraformer output is not treated as audio ground truth."
}
```

The automatic relation is an audit aid, not a replacement for human listening.

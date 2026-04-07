# inquiry_question_generator calibration notes

## Intent
This prompt creates operator-facing questions that are:
- narrow,
- bounded,
- answerable quickly,
- safe to ignore without breaking the system.

## Why one question only
Multi-part operator tasks dramatically lower response quality and response rates.
One task should resolve one decision.

## Recommended schema patterns by inquiry kind

### pretrade_decision
```json
{
  "decision": "approve|reject|wait|need_more_info",
  "reason_codes": ["string"],
  "notes": "short rationale"
}
```

### position_reassessment
```json
{
  "action": "hold|reduce|exit|wait|need_more_info",
  "reason_codes": ["string"],
  "notes": "short rationale"
}
```

### source_gap_resolution
```json
{
  "resolution": "proceed_without|wait_for_source|add_source_candidate|need_more_info",
  "notes": "short rationale"
}
```

### benchmark_selection
```json
{
  "benchmark": "SPY|QQQ|sector_etf|need_more_info",
  "notes": "short rationale"
}
```

### postmortem_review
```json
{
  "label": "confirm_failure_code|relabel|insufficient",
  "failure_codes": ["string"],
  "notes": "short rationale"
}
```

## SLA guidance
- fast: pretrade, time-sensitive near-threshold decisions
- normal: position reassessment, source gap, benchmark selection
- slow: postmortem review

## Bounded evidence
The operator should not be asked to conduct fresh research unless the system explicitly opens a separate research workflow.

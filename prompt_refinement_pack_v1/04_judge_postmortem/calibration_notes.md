# judge_postmortem calibration notes

## Intent
This prompt is meant to create usable learning signals, not vague retrospective prose.

## Direction vs magnitude
Separate these two:
- Direction asks whether the sign of the edge was right.
- Magnitude asks whether the forecast interval was reasonable.

A forecast can be directionally right but still poorly calibrated on magnitude, which should produce `mixed`, not `correct`.

## Neutral band
A small realized relative return should not be over-interpreted.
Suggested neutral bands:
- 1d: 30 bps
- 5d: 100 bps

These are deliberately simple and can be tuned later.

## Failure code usage
Choose the smallest set of root-cause labels that best explains the miss.
Do not spray many codes.

Good:
- `macro_override`
- `already_priced`

Bad:
- five loosely related codes

## Actionable lessons
Every lesson should be phrased so that someone could:
- update the prompt,
- update a threshold,
- update routing,
- or add a missing evidence requirement.

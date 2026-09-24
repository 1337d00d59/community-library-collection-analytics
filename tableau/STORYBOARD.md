# Tableau story storyboard

| Point | Headline | Primary view | Interaction | Accurate takeaway |
|---|---|---|---|---|
| 1 | The collection changed across the year | Validated network trend + monthly flows | Metric selector; hover exact counts | October 262,466 → September 264,019 observed items; endpoint provisional |
| 2 | Missing data changes what can be claimed | April gap + exception strip | Click April; inspect Echo Meadow | No complete April network total; do not fill or interpolate it |
| 3 | A board report should invite investigation | Community/family heatmap + issue detail | Select Goldleaf Quay, youth print | September observed closing is 19 higher than flow-derived closing |

The story should remain understandable without clicking: provide plain text captions and show the missing/provisional states next to the measures. Interactivity supplies additional evidence for an interested viewer.

Matplotlib's role in this repository is reproducible PNG production directly from the Python validation result. Tableau's role is controlled discovery on separately exported, validated CSVs. Use the same factual definitions in both, and reconcile the displayed totals before linking the two artifacts publicly.

# Presentation and poster outline

## Slide 1 — One question
Does one frozen MAMMAL vector improve a strong conventional molecular baseline for drug-level DILI concern?

## Slide 2 — Evidence flow
1,336 FDA records → 982 non-ambiguous records reviewed → 809 eligible → 675 development + 134 untouched update drugs.

## Slide 3 — Matched experiment
Show Models A–D. Emphasise that B versus D changes only the added MAMMAL block.

## Slide 4 — Leakage controls
Show chemical grouping, repeated nested validation, training-fold-only preprocessing, and the outcome-blind representation lock.

## Slide 5 — Primary answer
Display `primary_effect.svg`: ΔAUROC -0.080, 95% CI -0.114 to -0.042. State the locked interpretation verbatim: The expanded model performs worse under the locked procedure.

## Slide 6 — More than AUROC
Show PR-AUROC, Brier score, calibration, threshold performance, and `repeat_stability.svg`.

## Slide 7 — Robustness and transport
Compare vMost-vNo, balanced-class, optimistic random-split, and untouched update results. Keep the random split explicitly non-primary.

## Slide 8 — Important false negatives
Show persistence below both Youden and sensitivity-prioritised thresholds with curation context. Do not use errors to alter the fitted pipeline.

## Slide 9 — Boundaries
Drug is not patient; concern is not perfect truth; structure omits exposure and host biology; pretraining overlap is unknown; one frozen recipe is not the model family.

## Slide 10 — Reproducibility
Show the protocol/config/code locks, G2/G3/G4/G5 hashes, public reproduction path, and the final scope statement.

## Poster arrangement
Use a three-column flow: question/design → primary effect and metrics → robustness/errors/limitations. Keep the primary effect directly below the B-versus-D diagram and reserve the largest visual area for the answer, not the technology branding.

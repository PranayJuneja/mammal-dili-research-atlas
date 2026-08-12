# Pre-performance precision assessment decision

Date: 2026-08-13 (Asia/Calcutta)
Status: Accepted for estimation-focused execution; no protocol setting changed.

This simulation was completed before any empirical model-performance result was inspected. It used the current 810-row cohort's observed 569-group size vector, including the largest 74-drug scaffold group, and generated five paired prediction sets per experiment.

Across 16 scenarios, the smallest observed interval-coverage estimate was 0.875 and the largest mean 95% interval width was 0.04534 AUROC. The largest endpoint movement between a 100-resample prefix and the locked 2,000-resample whole-group bootstrap was 0.00502 AUROC.

The coverage screen uses only 40 Monte Carlo experiments per scenario and is therefore an imprecise diagnostic, not a guarantee of nominal coverage. The maximum width also shows that this dataset may not distinguish small gains precisely. This limitation is accepted because the study is explicitly estimation-focused: it will report the paired effect estimate, its interval, the 0.03 practical benchmark, and an inconclusive result when the interval spans both no gain and a meaningful gain. The simulation did not select a more favourable method, and it does not justify a binary superiority claim.

Locked execution remains unchanged: five repeated five-fold scaffold-grouped nested cross-validation runs and 2,000 whole-group paired bootstrap resamples.

Evidence: `audit/qc/precision_simulation.csv` and `audit/qc/precision_simulation.summary.json`.

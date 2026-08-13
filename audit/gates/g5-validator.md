# G5 independent validator acceptance

Date: 2026-08-13 (Asia/Calcutta)

Status: PASS

Report manifest SHA-256: 7d0ae540646b575325863d4b0a13bb730abc58ddf1251ef7afd975df92bc0466

Download manifest SHA-256: 690d8c3755bdac68ba2654bf6391e18288c03e6efc68b5c637cc220248dd6f2c

## Review boundary

This independent review covers the five locked statistical result sets, their uncertainty companions, the generated report and website bridge, the public reporting bundle, the false-negative audit, and the final TRIPOD+AI disposition addendum. It does not establish patient-level validity, clinical utility, causal attribution, or general performance of other MAMMAL checkpoints, representations, learners, cohorts, or prompts.

## Locked lineage and numerical reproduction

All five result manifests bind the accepted G4 prediction-lock SHA-256 `26908c6a723a1e912bd1d16184a39978eacc2b4d78d2ab5e7b2781ce5eb6791e` and their exact G4-frozen prediction inputs. Result JSON, prediction, repeat-metrics, and bootstrap companion hashes match their manifests. The development analyses retain the accepted G3 and protocol-lock lineage; the update analysis remains the one-time added-drug transport evaluation.

The validator independently recalculated every model metric and repeat-level metric from the frozen prediction rows. Model summaries, five paired repeat differences, point estimates, convergence counts, and reported intervals match. Every analysis contains exactly 2,000 finite saved bootstrap values. Independent whole-scaffold bootstrap replay using the locked seeds reproduced the saved arrays to floating-point roundoff; the maximum absolute discrepancy over all five analyses was `3.3306690738754696e-16`.

The reproduced paired changes in AUROC were:

- Primary nested scaffold analysis: `-0.08041505349485874` (95% CI `-0.11421817722498152` to `-0.041996801860668634`).
- `vMost` versus `vNo`: `-0.07576007931262403` (95% CI `-0.11803816360612275` to `-0.0401582545748089`).
- Optimistic stratified-random split: `-0.06575704591815497` (95% CI `-0.09369597603344472` to `-0.03577565436449559`).
- Class-balanced learner: `-0.07781732650597402` (95% CI `-0.11135856729603545` to `-0.039209481774350984`).
- Untouched added-drug transport: `-0.02929292929292926` (95% CI `-0.10926688443135801` to `0.046678747892178525`).

The primary interpretation that the expanded model performed worse under this locked procedure follows the prespecified interval rule. The update result is reported as uncertain exploratory transport evidence and does not replace the primary result. No convergence warning was omitted.

## Reporting, error audit, and public bundle

The report and generated website data agree byte-for-byte on the research summary. All files named by the public download manifest exist and match its hashes. The report manifest accurately distinguishes the complete internal report companions from the smaller public download bundle. Citations and scope statements remain consistent with the previously reviewed seven-reference evidence set, and the report does not extend the result to patient risk, prescribing, causality, or the MAMMAL model family.

The public important-false-negative table contains exactly 277 model-drug rows representing 113 unique drugs. It is an exact copy of the generated primary out-of-fold error audit except for the disclosed presentation substitutions `none` and `not applicable` in otherwise blank curation fields. The final addendum states both denominators prominently and provides the complete analysis population/event table.

The final reporting addendum resolves all 13 previously pending TRIPOD+AI dispositions. It provides a structured abstract, explicit unavailable upstream assessor/blinding information, dated governance status, honest funding/conflict/registration availability statements, availability and public-involvement dispositions, predictor/missingness and development-versus-update tables, per-analysis event counts, and a justified statement that there is no single deployable fitted model to export. The accompanying resolution CSV maps each former pending item to its final disposition and evidence location.

## Gate decision and limits

G5 passes. The locked estimates, uncertainty arrays, repeat summaries, robustness analyses, exploratory transport result, false-negative audit, scientific interpretation, report bundle, and public website bridge are internally consistent and reproducible from the accepted G4 artifacts.

This acceptance is bound to the hashes above and remediation commit `7a381a9c08931dbfc54f01fec11682949ec5744d`. Any later change to a prediction, result, bootstrap, repeat companion, report manifest, download manifest, or substantive scientific conclusion requires renewed scope-appropriate validation. Administrative submission fields and private identifying governance records remain the responsibility of their human custodians.

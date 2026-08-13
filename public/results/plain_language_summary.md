# Plain-language research summary

## The question

We tested whether adding one fixed numerical description made by the MAMMAL molecular foundation model improves a strong conventional chemistry model for ranking medicines by established drug-induced liver-injury concern.

## What we did

The comparison was deliberately matched. Model B used ordinary physicochemical measurements plus a Morgan fingerprint. Model D used exactly the same information and learner, then added one frozen 768-number MAMMAL vector. Related molecular cores stayed together during validation so close chemical relatives could not make performance look unrealistically good.

The primary analysis used 675 eligible drugs from the original DILIrank list. Another 134 eligible drugs added in DILIrank 2.0 were held aside until development was finished.

## The answer

Adding MAMMAL changed AUROC by **-0.080**. The 95% confidence interval was **-0.114 to -0.042**. The expanded model performs worse under the locked procedure.

In the untouched added-drug cohort, the corresponding exploratory difference was -0.029 (95% CI -0.109 to +0.047). This secondary result does not replace the primary answer.

## What this does not mean

This is a drug-level research benchmark. It does not estimate one patient's chance of liver injury, prove causality for a medicine, or recommend prescribing. Dose, exposure, metabolism, genetics, illness, immune response, and co-medications are outside the primary structure-only model.

## Why the result is credible

The checkpoint, tokenizer, prompt, pooling rule, molecule set, comparator, folds, learner, metric, practical benchmark, resampling method, and interpretation wording were frozen before performance was opened. Independent gates checked curation, extraction, feature/fold lineage, prediction coverage, and report regeneration.

# Anonymised KUHS submission protocol

## Title

Incremental value of frozen MAMMAL molecular embeddings for drug-level liver-injury concern classification

*Word count: 12 / 25*

## Introduction

Drug-induced liver injury is a clinically important and mechanistically diverse safety problem. DILIrank 2.0 organises FDA-approved drugs by established concern using regulatory labelling and causality evidence. Traditional molecular prediction uses physicochemical descriptors and substructure fingerprints, while foundation models can encode broader learned regularities. A fair test must ask whether a frozen representation adds information beyond a strong conventional baseline, without allowing related chemical scaffolds or outcome-guided engineering to exaggerate performance. This study therefore compares matched logistic-regression models under repeated nested scaffold-grouped validation, with one primary contrast and a prospectively defined practical-gain benchmark.

*Word count: 92 / 300*

## Objectives

Primary: estimate the paired change in AUROC when one frozen MAMMAL embedding is added to descriptors and a Morgan fingerprint. Secondary: describe calibration, precision-recall performance, threshold behaviour, important vMost false negatives, pre-specified robustness analyses, and transport to drugs added in DILIrank 2.0.

*Word count: 42 / 100*

## Methodology

Public DILIrank 2.0 records were parsed and checked against fixed counts. Ambiguous labels were excluded. Chemical identities, active moieties, parent structures, stereochemistry, duplicate parents, conflicts, biologics, mixtures and unsupported complexes were adjudicated under a versioned rule set. Of 1,336 records, 809 were structurally eligible. The primary development population comprised 675 original-list drugs; 134 added drugs were isolated before grouping and retained for one exploratory transport evaluation. Model A used pre-specified physicochemical descriptors. Model B added 2,048-bit radius-2 chirality-aware Morgan fingerprints. Model C used a frozen 768-dimensional MAMMAL vector. Model D combined Model B with MAMMAL. All models used the same L2-regularised logistic-regression family and tuning grid. MAMMAL weights, checkpoint revision, tokenizer files, checkpoint-native prompt, final encoder state, attention-mask-aware mean pooling, L2 normalisation, length rule and CPU runtime were frozen after a label-blind technical pilot. Ring-containing drugs were grouped by Bemis–Murcko scaffold and acyclic drugs by fingerprint similarity. The primary analysis used five repeats of nested five-fold scaffold-grouped cross-validation. Imputation, scaling, regularisation and thresholds were selected inside training partitions. The primary estimand was the arithmetic mean of repeat-level AUROC(Model D) minus AUROC(Model B). A 95% interval used 2,000 paired complete-scaffold bootstrap resamples and was interpreted against zero and a +0.03 practical benchmark. Secondary measures included PR-AUROC, Brier score, calibration, sensitivity, specificity, precision and balanced accuracy. Pre-specified sensitivity analyses examined vMost versus vNo, class weighting and an explicitly optimistic random split. All stages were hash-bound and independently gated before result narration.

*Word count: 239 / 800*

## Implications

The observed paired AUROC change was -0.080 with a 95% confidence interval from -0.114 to -0.042. The expanded model performs worse under the locked procedure. The result concerns one frozen representation and one drug-level benchmark. It does not estimate patient risk, prove drug-specific causality, or guide prescribing.

*Word count: 47 / 100*

## References

1. US Food and Drug Administration. Drug-Induced Liver Injury Rank (DILIrank) 2.0 Dataset. 2. Shoshan Y, Raboh M, Ozery-Flato M, et al. MAMMAL - Molecular Aligned Multi-Modal Architecture and Language for biomedical discovery. npj Drug Discov. 2026;3:14. doi:10.1038/s44386-026-00047-4. 3. Rogers D, Hahn M. Extended-connectivity fingerprints. J Chem Inf Model. 2010;50:742-754. 4. Collins GS, et al. TRIPOD+AI statement. BMJ. 2024;385:e078378.

*Word count: 59 / 300*

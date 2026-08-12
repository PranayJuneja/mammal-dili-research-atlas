# Glossary

## Clinical and regulatory terms

**Drug-induced liver injury (DILI):** Liver injury associated with exposure to a medicine, herbal product, or dietary supplement. This study concerns drug-level evidence categories, not diagnosis in a patient.

**DILI concern:** The level of established liver-injury concern assigned to a drug by DILIrank from labelling and published evidence.

**`vMost-DILI-concern`:** DILIrank 2.0 category with the strongest established concern under its curation framework.

**`vLess-DILI-concern`:** Category with established but lesser concern under that framework.

**`vNo-DILI-concern`:** Category with no established DILI concern under the dataset's rules. It does not mean zero biological risk.

**Ambiguous:** DILIrank category where causality is undetermined. Excluded from the primary binary outcome.

**Rule of Two:** A published heuristic in which an oral medication has higher DILI concern when daily dose is at least 100 mg and logP is at least 3.

**Hepatotoxicity:** Capacity to damage the liver. In this project, avoid treating the term as interchangeable with an adjudicated patient event.

**Pharmacovigilance:** Detection, assessment, understanding, and prevention of adverse effects after medicines are used.

## Chemical representation terms

**SMILES:** A line notation that represents atoms, bonds, branches, rings, charge, and sometimes stereochemistry as text.

**Canonical SMILES:** A software-generated consistent SMILES for a structure. Canonicalisation is toolkit- and version-dependent.

**Isomeric SMILES:** SMILES that retains available stereochemical/isotopic information.

**InChIKey:** A fixed-length hashed identifier derived from a chemical structure, useful for matching and duplicate checks.

**Parent structure:** The selected active molecular component after removing counterions or formulation components under defined rules.

**Salt:** An ionic form containing an active ion and counterion. Different salts can collapse to the same parent active structure.

**Stereochemistry:** Three-dimensional arrangement of atoms that can distinguish molecules with the same connectivity.

**Tautomer:** One of several rapidly interconvertible bonding/proton arrangements of a molecule.

**Physicochemical descriptor:** Calculated numeric property such as molecular weight, logP, polar surface area, or hydrogen-bond count.

**logP:** Logarithm of the partition coefficient between octanol and water for the neutral species; a measure related to lipophilicity.

**Morgan fingerprint:** Circular fingerprint encoding local atom neighbourhoods. Here it is a chirality-aware radius-2 vector of 2,048 binary bits.

**Bemis–Murcko scaffold:** A core ring-and-linker framework used to group structurally related molecules.

**Tanimoto similarity:** A similarity score commonly used for binary molecular fingerprints; 0 means no shared on-bits and 1 means identical bit sets.

**Butina clustering:** A method that groups items around high-connectivity centres using a similarity/distance threshold.

## MAMMAL terms

**Foundation model:** A large pretrained model intended to provide reusable representations or capabilities across tasks.

**MAMMAL:** Molecular Aligned Multi-Modal Architecture and Language, an IBM biomedical model family spanning small molecules, proteins, and gene-expression data.

**Checkpoint:** A stored set of model weights and configuration at a specific revision.

**Tokenizer:** Software that turns a formatted text/molecular prompt into integer tokens for the model.

**Prompt:** The exact formatted input, including modality and special tokens, supplied to MAMMAL.

**Embedding:** A fixed-length numerical representation extracted from an internal model state.

**Frozen weights:** Pretrained parameters that are not updated during this study.

**Fine-tuning:** Updating pretrained parameters or attached task parameters using labelled examples. Full MAMMAL fine-tuning is out of scope.

**Hidden layer/state:** An internal vector representation produced at a specified model layer for each token.

**Pooling:** A rule that converts token-level hidden states into one vector, for example mask-aware mean pooling.

**Truncation:** Removing input tokens beyond a length limit. Silent truncation is prohibited.

## Modelling terms

**Feature/predictor:** Input variable supplied to a statistical model.

**Outcome/label:** The value being predicted; here, a binary transformation of DILIrank concern.

**Logistic regression:** A model that estimates the probability of a binary outcome from weighted predictors.

**L2 regularisation:** A penalty that shrinks coefficients to reduce instability and overfitting, especially with many predictors.

**Hyperparameter:** A setting selected outside ordinary coefficient fitting, such as regularisation strength.

**Training set:** Data used to fit preprocessing and model parameters.

**Validation set:** Ambiguous term. In this project, use “inner validation fold” for hyperparameter selection and “outer test fold” for performance estimation.

**Nested cross-validation:** Outer folds estimate performance; inner folds select hyperparameters without touching outer test outcomes.

**Scaffold split:** Evaluation grouping that keeps structurally related molecular cores together.

**Out-of-fold prediction:** Prediction for a drug made by a model that was not trained on that drug's outer test fold.

**Information leakage:** Test information influencing training, preprocessing, tuning, threshold choice, or feature engineering.

**Class imbalance:** Unequal counts of positive and negative outcomes.

## Statistical terms

**AUROC:** Area under the receiver operating characteristic curve. It is the probability that a randomly selected positive is ranked above a randomly selected negative.

**ROC curve:** Sensitivity plotted against false-positive rate across thresholds.

**Precision-recall AUROC:** Summary of precision versus recall across thresholds; depends on positive-class prevalence.

**Sensitivity/recall:** Fraction of outcome-positive drugs classified positive.

**Specificity:** Fraction of outcome-negative drugs classified negative.

**Precision/positive predictive value:** Fraction of positive predictions that are outcome-positive.

**Balanced accuracy:** Average of sensitivity and specificity.

**Brier score:** Mean squared error of predicted probabilities; lower is better.

**Calibration:** Agreement between predicted probabilities and observed outcome frequencies.

**Calibration intercept:** Measures systematic over- or under-prediction; ideal value is 0.

**Calibration slope:** Measures whether predictions are too extreme or too weak; ideal value is 1.

**Estimand:** The exact quantity the study seeks to estimate.

**`ΔAUROC`:** Paired AUROC difference between expanded Model D and conventional Model B.

**Confidence interval:** Range expressing uncertainty in an estimate under the stated method.

**Bootstrap:** Resampling method used to approximate an estimate's uncertainty. Here complete scaffold groups, not isolated drugs, are resampled.

**Minimum practically important difference:** Pre-specified improvement large enough to matter for the study's intended use; proposed as 0.03 AUROC.

**Superiority:** Evidence that the difference is greater than zero.

**Equivalence:** Evidence that the difference lies within pre-defined equivalence margins. Failure to show superiority is not equivalence.

**Youden's index:** `sensitivity + specificity - 1`, used here to select a descriptive threshold within training data.

**Complete-case analysis:** Analysis restricted to records with all required variables, used only for the dose subset.

## Governance terms

**IEC:** Institutional Ethics Committee.

**Protocol lock:** Point after which pre-specified methods cannot change without formal documentation.

**Amendment:** Approved prospective change to the locked protocol.

**Deviation:** Departure from the locked protocol that occurred during conduct and must be reported.

**TRIPOD+AI:** Current reporting guidance for studies developing or evaluating prediction models using regression or machine-learning methods.


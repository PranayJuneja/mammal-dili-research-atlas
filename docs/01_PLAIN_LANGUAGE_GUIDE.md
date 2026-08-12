# Plain-Language Guide

## The problem

Some medicines can injure the liver. This is called drug-induced liver injury, or DILI. It is difficult to predict because the outcome depends on more than the molecule alone. Dose, metabolism, immune reactions, other illnesses, and individual susceptibility can all matter.

This study does not follow patients. It starts with a public list of approved drugs and asks whether their molecular structures contain enough information to help distinguish drugs with established liver-injury concern from drugs with no established concern in that list.

## What DILIrank 2.0 is

DILIrank 2.0 is a United States Food and Drug Administration resource containing 1,336 approved drugs. It assigns each drug to one of four concern categories based on approved labelling and published causality evidence:

- 217 `vMost-DILI-concern`
- 351 `vLess-DILI-concern`
- 414 `vNo-DILI-concern`
- 354 `Ambiguous-DILI-concern`

The ambiguous records are not used in the main binary analysis. That leaves 982 records before removing drugs whose chemical structures cannot be used reliably.

These labels describe the level of established concern around a drug. They are not records of individual patients and are not perfect truth. In particular, `vNo` means no established concern under the dataset's method; it does not prove that liver injury is impossible.

## How a computer sees a molecule

A small molecule can be written as a string of characters called SMILES. The string records atoms, bonds, branches, rings, charges, and sometimes stereochemistry. Before modelling, each drug must be linked to the correct structure and processed consistently so that salts, mixtures, duplicates, and alternate representations do not create false differences.

The study turns each cleaned structure into three kinds of numbers:

1. **Physicochemical descriptors:** calculated properties such as molecular weight, fat solubility (`logP`), polar surface area, hydrogen-bond counts, charge, rings, and flexibility.
2. **Morgan fingerprint:** 2,048 yes/no indicators summarising local chemical patterns around atoms.
3. **MAMMAL embedding:** a long numerical representation taken from the internal state of a large pretrained biomedical model.

## What “frozen MAMMAL” means

MAMMAL has already learned from a very large biomedical pretraining collection. “Frozen” means this study will not change those pretrained weights. The cleaned drug structure is passed through the model and a fixed-length numerical vector is extracted.

The difficult part is that an embedding is not automatically defined by the checkpoint name. The result can change depending on the prompt, tokenizer revision, hidden layer, pooling rule, sequence limit, truncation rule, and software version. Those choices must be fixed in a label-blind pilot before any DILI model is evaluated.

## The four models

| Model | What it receives | Why it exists |
|---|---|---|
| A | Descriptors only | Shows what simple calculated chemistry contributes |
| B | Morgan fingerprint + descriptors | Strong conventional baseline |
| C | MAMMAL only | Shows how the frozen representation performs by itself |
| D | Morgan + descriptors + MAMMAL | Expanded model used in the primary comparison |

All four use the same statistical prediction method: L2-regularised logistic regression. This makes the comparison mainly about the molecular representations rather than about giving one representation a more powerful algorithm.

## The actual test

The primary comparison is Model D versus Model B. Because D contains everything in B and adds only MAMMAL, their difference estimates MAMMAL's incremental value.

The main measure is AUROC. Imagine selecting one concern-positive drug and one `vNo` drug at random. AUROC is the probability that the model ranks the concern-positive drug higher. A value of 0.50 is chance ranking; 1.00 is perfect ranking.

The study calculates:

`delta AUROC = AUROC(Model D) - AUROC(Model B)`

A positive number favours adding MAMMAL. A negative number favours the conventional model. The estimate alone is not enough; its 95% confidence interval shows how uncertain it is.

## Why structurally related drugs are separated

If close chemical relatives appear in both training and testing data, the model may appear impressive merely because it has seen a near-twin. The primary evaluation groups drugs by their core chemical framework, called a scaffold. Related scaffolds stay in one evaluation group, making the test harder and more relevant to unfamiliar chemistry.

## Why the Rule of Two is not the primary baseline

The Rule of Two marks an oral drug as higher concern when the daily dose is at least 100 mg and `logP` is at least 3. It is clinically understandable and biologically plausible.

However, reliable daily dose is unavailable or ambiguous for some drugs, depends on indication and regimen, and does not apply naturally to every route. Requiring dose for the primary cohort would remove drugs for reasons related to exposure data rather than molecular structure. The Rule of Two is therefore retained in a clearly labelled oral-drug subset analysis.

## What the possible answers mean

- **Confidence interval wholly above 0.03:** evidence supports a practically meaningful gain under this study design.
- **Wholly above 0 but overlapping 0.03:** evidence of some improvement, but practical importance remains uncertain.
- **Crosses 0 and 0.03:** inconclusive.
- **Upper limit below 0.03:** the study excludes the pre-specified practically important gain, even if a tiny benefit remains possible.
- **Wholly below 0:** the selected MAMMAL representation performs worse.
- **Pilot failure:** the proposed frozen representation was not reproducibly extractable under the stated environment and rules.

## What this study will never show

It cannot predict whether a named patient will develop liver injury. It cannot establish causality, replace an ethics or regulatory process, prove that a `vNo` drug is safe, prove that MAMMAL never contains useful DILI information, or establish that another MAMMAL layer/prompt/fine-tuning strategy would behave the same way.


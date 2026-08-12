# Evidence Ledger and References

## Purpose

This ledger separates verified source facts from protocol decisions and claims that still need confirmation. Evidence was checked on 12 August 2026. A live source can change; acquisition revisions and access dates must be recorded again when analysis begins.

## Verified core sources

### DILIrank 2.0

The [FDA DILIrank 2.0 page](https://www.fda.gov/science-research/liver-toxicity-knowledge-base-ltkb/drug-induced-liver-injury-rank-dilirank-20-dataset) states that the dataset contains 1,336 FDA-approved drugs, expands the original 1,036 list by 300 drugs approved from 2010–2021, and contains 217 `vMost`, 351 `vLess`, 414 `vNo`, and 354 `Ambiguous` records. It also notes 49 reclassifications among original drugs and provides the complete-list download.

The peer-reviewed update is indexed by [PubMed](https://pubmed.ncbi.nlm.nih.gov/41005561/) as Drug Discovery Today 2025;30(11):104485, DOI `10.1016/j.drudis.2025.104485`.

**Supports:** source population, category counts, update membership, label provenance, citation.

**Does not support:** treating labels as patient outcomes or perfect biological truth.

### MAMMAL

The [peer-reviewed MAMMAL article on PubMed](https://pubmed.ncbi.nlm.nih.gov/42380594/) and DOI `10.1038/s44386-026-00047-4` describe pretraining on more than two billion samples across protein/antibody sequences, small molecules, and gene-expression profiles.

The [IBM Hugging Face model card](https://huggingface.co/ibm-research/biomed.omics.bl.sm.ma-ted-458m) identifies the public 458M/approximately 0.5B checkpoint, Apache-2.0 licence, code repository, and basic model/tokenizer loading example. The [official GitHub repository](https://github.com/BiomedSciAI/biomed-multi-alignment) documents installation, task prompts, generation, and fine-tuning examples.

**Supports:** model availability, scale, modalities, software source, and need to pin revisions.

**Does not by itself support:** one uniquely correct generic molecular embedding, selected layer/pooling rule, absence of DILIrank molecules from pretraining, or DILI performance.

### Conventional chemical representation

Rogers and Hahn's [extended-connectivity fingerprint article](https://pubmed.ncbi.nlm.nih.gov/20426451/) supports circular fingerprints for molecular characterisation and structure–activity modelling. DOI: `10.1021/ci100050t`.

Bemis and Murcko introduced molecular frameworks in J Med Chem. 1996;39(15):2887–2893. DOI: [`10.1021/jm9602928`](https://doi.org/10.1021/jm9602928).

**Supports:** the conventional fingerprint comparator and scaffold-grouping rationale.

**Protocol choices, not source facts:** radius 2, 2,048 bits, chirality, exact descriptor list, and the acyclic Butina threshold.

### Dose and lipophilicity

Chen, Borlak, and Tong's [Rule-of-Two article](https://pubmed.ncbi.nlm.nih.gov/23258593/) reports elevated hepatotoxicity association when oral daily dose is at least 100 mg and logP is at least 3. Hepatology. 2013;58(1):388–396. DOI `10.1002/hep.26208`.

The DILI-Context publication is linked through DOI [`10.1093/toxsci/kfag077`](https://doi.org/10.1093/toxsci/kfag077). Its exact version, coverage, licence, and extraction fields must be checked before it is adopted as the dose source.

**Supports:** rationale for the exploratory Rule-of-Two analysis.

**Does not support:** requiring dose in the primary structure-only cohort or assuming one unambiguous therapeutic daily dose per drug.

### Reporting guidance

The [TRIPOD+AI statement](https://www.bmj.com/content/385/bmj-2023-078378) supersedes TRIPOD 2015 and provides a 27-item checklist for transparent reporting of prediction-model studies using regression or machine-learning methods. BMJ. 2024;385:e078378. DOI `10.1136/bmj-2023-078378`.

**Supports:** transparent reporting, open-science details, model evaluation terminology, and disclosure.

**Does not prescribe:** the correct model-development or confidence-interval method for this dataset. It is a reporting guideline, not a quality or risk-of-bias tool.

### KUHS pathway

The [official KUHS Research Appreciation Award guideline](https://www2.kuhs.ac.in/kuhs_new/images/uploads/pdf/research/2024/Guidelines---KUHS-Research-Appreciation-Award.pdf) supports the guide eligibility/one-student rules, mandatory Application Attestation Form and IEC letter, protocol section limits, Vancouver references, research-integrity requirements, and institutional plagiarism threshold described in the ethics document.

The official host currently presents a TLS certificate mismatch to direct command-line retrieval, although the indexed official document text is searchable. Download the current guideline through the live KUHS portal/browser and archive it before submission.

## Claims requiring pre-analysis verification

| Claim/choice | Current status | Required action |
|---|---|---|
| Current KUHS deadline and application window | Unknown | Check live call/portal |
| Proposal-specific anonymity fields | Conservative assumption | Confirm against live call and preview upload |
| Exact MAMMAL hidden-state extraction | Undefined | Expert-reviewed label-blind pilot |
| `0.03` as practically important AUROC gain | Protocol proposal | Statistical and domain rationale/sign-off |
| Five repeats provide adequate precision | Unknown | Outcome-blind simulation after scaffold lock |
| Bootstrap interval has adequate coverage | Provisional | Simulation and adviser review |
| ≥90% full-cohort embedding coverage | Feasibility convention | Justify/sign off before outcomes |
| DILI-Context is usable and licensable for linkage | Not yet checked in implementation | Acquire, inspect fields/licence/version |
| Expected CI half-width below 0.04 | Unsupported draft assertion | Do not repeat; replace with simulation |
| No prior MAMMAL-on-DILIrank benchmark exists | Not established | Complete structured novelty review before submission |

## Vancouver-style working references

1. Shoshan Y, Raboh M, Ozery-Flato M, Ratner V, Golts A, Weber JK, et al. MAMMAL—Molecular Aligned Multi-Modal Architecture and Language for biomedical discovery. npj Drug Discov. 2026;3:14. doi:10.1038/s44386-026-00047-4.
2. Olubamiwa AO, Qu Y, Connor S, Tong W, Li D, Chen M. DILIrank 2.0: an updated and expanded database for drug-induced liver injury risk based on FDA labeling and a literature review. Drug Discov Today. 2025;30(11):104485. doi:10.1016/j.drudis.2025.104485.
3. Fontana RJ, Liou I, Reuben A, Suzuki A, Fiel MI, Lee W, et al. AASLD practice guidance on drug, herbal, and dietary supplement-induced liver injury. Hepatology. 2023;77(3):1036–1065. doi:10.1002/hep.32689.
4. Chen M, Suzuki A, Borlak J, Andrade RJ, Lucena MI. Drug-induced liver injury: interactions between drug properties and host factors. J Hepatol. 2015;63(2):503–514. doi:10.1016/j.jhep.2015.04.016.
5. Rogers D, Hahn M. Extended-connectivity fingerprints. J Chem Inf Model. 2010;50(5):742–754. doi:10.1021/ci100050t.
6. Ancuceanu R, Hovanet MV, Anghel AI, Furtunescu F, Neagu M, Constantin C, et al. Computational models using multiple machine learning algorithms for predicting drug hepatotoxicity with the DILIrank dataset. Int J Mol Sci. 2020;21(6):2114. doi:10.3390/ijms21062114.
7. Kim S, Chen J, Cheng T, Gindulyte A, He J, He S, et al. PubChem 2023 update. Nucleic Acids Res. 2023;51(D1):D1373–D1380. doi:10.1093/nar/gkac956.
8. Zandie R, Betancort R, Khodaee F. DILI-Context: a dose- and exposure-enriched knowledge base for translational liver safety assessment. Toxicol Sci. 2026;209(7):kfag077. doi:10.1093/toxsci/kfag077.
9. Bemis GW, Murcko MA. The properties of known drugs. 1. Molecular frameworks. J Med Chem. 1996;39(15):2887–2893. doi:10.1021/jm9602928.
10. Chen M, Borlak J, Tong W. High lipophilicity and high daily dose of oral medications are associated with significant risk for drug-induced liver injury. Hepatology. 2013;58(1):388–396. doi:10.1002/hep.26208.
11. Collins GS, Moons KGM, Dhiman P, Riley RD, Beam AL, Van Calster B, et al. TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use regression or machine learning methods. BMJ. 2024;385:e078378. doi:10.1136/bmj-2023-078378.

Bibliographic formatting must be checked once more against the journal/PubMed record when the final KUHS reference list is produced.


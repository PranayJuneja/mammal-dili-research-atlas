export type Phase = {
  id: string;
  gate: string;
  period: string;
  title: string;
  question: string;
  summary: string;
  work: string[];
  evidence: string[];
  stopRule: string;
  status: "cleared" | "next" | "planned";
};

export const studyStats = [
  { value: "1,336", label: "approved drugs in DILIrank 2.0", tone: "blue" },
  { value: "809", label: "independently reviewed eligible drugs", tone: "teal" },
  { value: "568", label: "locked chemical groups", tone: "amber" },
  { value: "675 + 134", label: "development plus untouched update drugs", tone: "purple" },
];

export const labelCounts = [
  { label: "vMost concern", value: 217, color: "var(--coral)" },
  { label: "vLess concern", value: 351, color: "var(--amber)" },
  { label: "vNo concern", value: 414, color: "var(--teal)" },
  { label: "Ambiguous", value: 354, color: "var(--mist-strong)" },
];

export const models = [
  {
    id: "A",
    name: "Descriptors only",
    blocks: ["Physicochemical descriptors"],
    role: "Shows what compact, interpretable chemistry contributes.",
    accent: "teal",
  },
  {
    id: "B",
    name: "Conventional baseline",
    blocks: ["Physicochemical descriptors", "Morgan fingerprint"],
    role: "The strong chemical comparator used in the primary contrast.",
    accent: "blue",
  },
  {
    id: "C",
    name: "MAMMAL only",
    blocks: ["Frozen MAMMAL embedding"],
    role: "Reveals how the pretrained representation behaves by itself.",
    accent: "purple",
  },
  {
    id: "D",
    name: "Expanded model",
    blocks: ["Physicochemical descriptors", "Morgan fingerprint", "Frozen MAMMAL embedding"],
    role: "Adds exactly one information block to Model B. This is the primary test.",
    accent: "amber",
  },
];

export const phases: Phase[] = [
  {
    id: "governance",
    gate: "G0–G1",
    period: "Month 1",
    title: "Governance & protocol lock",
    question: "Are we authorised, and are all choices fixed before results can influence them?",
    summary: "Align the IEC, KUHS, protocol, curation, and statistical decisions. This protects the study from outcome-guided redesign.",
    work: [
      "Retain the project-specific IEC determination outside the public repository.",
      "Align the exact title across the protocol, IEC record, and KUHS submission.",
      "Sign off the 0.03 practical-gain benchmark, resampling plan, thresholds, and curation rules.",
      "Freeze a protocol version, configuration hash, and outcome-access boundary.",
    ],
    evidence: ["Signed lock declaration", "Decision record", "Named reviewers", "KUHS requirements record"],
    stopRule: "No technical pilot or outcome analysis without the written institutional determination.",
    status: "next",
  },
  {
    id: "pilot",
    gate: "G2",
    period: "Month 1",
    title: "Label-blind MAMMAL pilot",
    question: "Can one exact frozen representation be generated repeatably before DILI labels are used?",
    summary: "Twenty deliberately difficult molecules test the full extraction contract: checkpoint, prompt, tokenizer, layer, pooling, limits, device, and tolerance.",
    work: [
      "Pin immutable model and tokenizer revisions and calculate checksums.",
      "Repeat vector extraction in a fresh process and a different batch order.",
      "Record token counts, truncation, vector shape, norms, runtime, and peak memory.",
      "Estimate the full-cohort compute requirement with a safety margin.",
    ],
    evidence: ["At least 18/20 finite vectors", "Fixed dimension", "Tolerance met", "No hidden truncation"],
    stopRule: "One correction cycle is allowed. A second failure is reported as technical infeasibility.",
    status: "next",
  },
  {
    id: "curation",
    gate: "G3",
    period: "Month 2",
    title: "Identity, structure & cohort lock",
    question: "Does every included drug map to one defensible molecular structure with no duplicate leakage?",
    summary: "Resolve names to PubChem identities, standardise parent structures, preserve justified stereochemistry, adjudicate conflicts, and group related chemistry.",
    work: [
      "Keep raw sources immutable and retain every candidate identity considered.",
      "Remove counterions under a reviewed parent rule; never invent stereochemistry.",
      "Resolve duplicate parents and exclude unresolved label conflicts.",
      "Assign Bemis–Murcko scaffolds and similarity clusters for acyclic molecules.",
    ],
    evidence: ["Identity crosswalk", "Exclusion audit", "Duplicate report", "Signed cohort lock"],
    stopRule: "Unresolved identities, duplicate conflicts, or invalid groups block modelling.",
    status: "cleared",
  },
  {
    id: "features",
    gate: "Feature lock",
    period: "Month 3",
    title: "Representation generation",
    question: "Can all three feature blocks be regenerated from the same locked parent structure?",
    summary: "Create descriptors, chirality-aware Morgan bits, and frozen MAMMAL vectors with complete manifests and coverage checks.",
    work: [
      "Calculate the pre-specified descriptor set and 2,048 radius-2 Morgan bits.",
      "Generate the pilot-locked embedding without changing MAMMAL weights.",
      "Validate dimensions, finite values, norms, token lengths, and truncation flags.",
      "Recompute a fixed verification sample in a clean process.",
    ],
    evidence: ["Feature manifests", "Checksums", "Coverage report", "5% repeat sample"],
    stopRule: "Coverage below 90% triggers a pause and adviser review before outcomes are examined.",
    status: "planned",
  },
  {
    id: "validation",
    gate: "G4",
    period: "Month 4",
    title: "Nested scaffold validation",
    question: "Does MAMMAL add information when close chemical relatives cannot cross the train–test boundary?",
    summary: "All four representation sets use the same L2 logistic regression, drugs, folds, preprocessing discipline, and tuning opportunities.",
    work: [
      "Generate five repeats of nested five-fold scaffold-grouped validation.",
      "Fit imputation, scaling, regularisation, and thresholds inside training data only.",
      "Write one out-of-fold probability for every drug, model, repeat, and fold.",
      "Run leakage, pairing, convergence, and update-cohort isolation tests.",
    ],
    evidence: ["Immutable folds", "Long-form predictions", "Leakage tests", "Convergence log"],
    stopRule: "A split scaffold, mismatched B/D rows, or unresolved leakage defect invalidates the prediction artefact.",
    status: "planned",
  },
  {
    id: "results",
    gate: "G5",
    period: "Months 5–6",
    title: "Estimation, interpretation & reporting",
    question: "Is the paired gain positive, practically important, too uncertain, worse—or technically unevaluable?",
    summary: "Estimate paired ΔAUROC with scaffold-group resampling, examine calibration and important errors, then report every result within the drug-level scope.",
    work: [
      "Calculate mean repeat-level Model D minus Model B AUROC.",
      "Construct the locked 95% confidence interval from 2,000 complete-scaffold resamples.",
      "Report PR-AUROC, Brier score, calibration, thresholds, and vMost false negatives.",
      "Complete pre-specified sensitivity analyses, TRIPOD+AI mapping, and reproducibility archive.",
    ],
    evidence: ["Primary effect figure", "Calibration plots", "Error review", "Reproducible report"],
    stopRule: "No conclusion may outrun the interval, the locked 0.03 benchmark, or the drug-level study scope.",
    status: "planned",
  },
];

export const safeguards = [
  { title: "Paired by design", text: "Models B and D predict the same held-out drugs in the same folds, so the contrast isolates the added representation block." },
  { title: "Scaffold separated", text: "Related chemical cores stay together. Random splitting appears only as an explicitly optimistic robustness analysis." },
  { title: "Training-fold only", text: "Imputation, scaling, tuning, threshold selection, and any recalibration never learn from an outer test fold." },
  { title: "Outcome-blind engineering", text: "The MAMMAL recipe is frozen on technical evidence, not chosen because a layer or prompt gives a better DILI result." },
  { title: "One primary claim", text: "The confirmatory question is Model D minus Model B on AUROC. Secondary metrics explain it; they do not replace it." },
  { title: "Failure is evidence", text: "Extraction failures, exclusions, negative results, and deviations stay visible in the archive and final report." },
];

export const outcomes = [
  {
    id: "meaningful",
    label: "Meaningful gain",
    range: "95% CI wholly above +0.03",
    headline: "The selected frozen representation adds a practically important gain.",
    detail: "The study may support incremental improvement under this exact cohort, comparator, classifier, and validation design.",
    caution: "It still does not establish clinical utility or patient-level prediction.",
    position: 82,
    width: 18,
  },
  {
    id: "some",
    label: "Some gain",
    range: "95% CI above 0, overlapping +0.03",
    headline: "Discrimination improves, but practical importance remains uncertain.",
    detail: "A positive effect is supported, yet the data do not prove the gain reaches the locked operational benchmark.",
    caution: "Do not compress this into a binary claim that “MAMMAL works.”",
    position: 64,
    width: 25,
  },
  {
    id: "inconclusive",
    label: "Inconclusive",
    range: "95% CI crosses both 0 and +0.03",
    headline: "The estimate is not precise enough to choose between no gain and an important gain.",
    detail: "The correct answer is uncertainty. More precision or a different study would be needed.",
    caution: "A non-significant result is not evidence of equivalence.",
    position: 48,
    width: 50,
  },
  {
    id: "exclude",
    label: "Important gain excluded",
    range: "Upper CI below +0.03; interval may cross 0",
    headline: "The pre-specified important improvement is excluded under this design.",
    detail: "A small benefit may remain possible, but the observed precision argues against a meaningfully larger gain in this setting.",
    caution: "This applies to the selected representation—not every MAMMAL strategy.",
    position: 36,
    width: 30,
  },
  {
    id: "worse",
    label: "Expanded model worse",
    range: "95% CI wholly below 0",
    headline: "Adding the selected MAMMAL vector reduces discrimination.",
    detail: "The conventional model is preferred for this benchmark under the locked evaluation procedure.",
    caution: "Do not generalise to other checkpoints, prompts, layers, or fine-tuning.",
    position: 18,
    width: 16,
  },
  {
    id: "infeasible",
    label: "Extraction infeasible",
    range: "Pilot fails after one correction cycle",
    headline: "Predictive incremental value is not evaluated.",
    detail: "The engineering result is that this pre-specified extraction contract could not meet its repeatability or coverage gate.",
    caution: "Technical infeasibility is not a negative predictive-performance result.",
    position: 8,
    width: 0,
  },
];

export const limitations = [
  ["Drug ≠ patient", "DILIrank records concern assigned to medicines, not a person’s dose, genetics, comorbidities, co-medications, immune state, or clinical course."],
  ["Concern ≠ perfect truth", "Labels reflect regulatory and published evidence. vNo means no established concern under the dataset method—not biological impossibility."],
  ["Structure is partial", "Dose, exposure, reactive metabolism, immune effects, and host susceptibility are outside the primary molecule-only representation."],
  ["Pretraining overlap is unknown", "Scaffold separation prevents downstream analogue leakage, but it cannot prove that MAMMAL never encountered a study molecule during pretraining."],
  ["One recipe, not a model family", "A result applies to one frozen checkpoint, prompt, layer, pooling rule, classifier, cohort, and validation procedure."],
];

export const glossary = [
  ["AUROC", "The probability that a randomly selected concern-positive drug is ranked above a vNo drug."],
  ["Calibration", "Agreement between predicted probabilities and observed concern frequencies in this dataset."],
  ["DILI", "Drug-induced liver injury. This project studies drug-level concern categories, not patient diagnosis."],
  ["Embedding", "A fixed-length numerical representation extracted from a specified internal MAMMAL state."],
  ["Frozen weights", "Pretrained parameters that are not updated using DILIrank labels."],
  ["Information leakage", "Test information influencing preprocessing, tuning, threshold choice, or feature engineering."],
  ["Morgan fingerprint", "A 2,048-bit summary of local atom neighbourhoods, generated here with radius 2 and chirality."],
  ["Nested cross-validation", "Inner folds select hyperparameters; untouched outer folds estimate performance."],
  ["Out-of-fold prediction", "A probability produced for a drug by a model that did not train on its outer test fold."],
  ["Practical-gain benchmark", "The proposed +0.03 AUROC improvement that must be signed off before results are inspected."],
  ["Scaffold", "A molecule’s core ring-and-linker framework, used to keep related chemistry in one evaluation group."],
  ["vNo", "No established DILI concern under DILIrank’s rules; it is not proof of absolute safety."],
] as const;

export const sources = [
  { name: "FDA · DILIrank 2.0", note: "Dataset definition, category counts, and update membership", href: "https://www.fda.gov/science-research/liver-toxicity-knowledge-base-ltkb/drug-induced-liver-injury-rank-dilirank-20-dataset" },
  { name: "MAMMAL · npj Drug Discovery", note: "Foundation-model architecture, modalities, and pretraining scale", href: "https://pubmed.ncbi.nlm.nih.gov/42380594/" },
  { name: "IBM · public checkpoint", note: "458M checkpoint, model card, licence, and loading surface", href: "https://huggingface.co/ibm-research/biomed.omics.bl.sm.ma-ted-458m" },
  { name: "TRIPOD+AI · BMJ", note: "Transparent reporting guidance for prediction-model studies", href: "https://www.bmj.com/content/385/bmj-2023-078378" },
  { name: "Rogers & Hahn", note: "Extended-connectivity fingerprint method", href: "https://pubmed.ncbi.nlm.nih.gov/20426451/" },
  { name: "Rule of Two", note: "Dose and lipophilicity rationale for the exploratory oral-drug analysis", href: "https://pubmed.ncbi.nlm.nih.gov/23258593/" },
];

import {
  ArrowDown,
  ArrowRight,
  Check,
  Database,
  Flask,
  GitBranch,
  LockKey,
  ShieldCheck,
  Warning,
} from "@phosphor-icons/react/dist/ssr";

import { DatasetDistribution } from "@/components/dataset-distribution";
import { GlossarySearch } from "@/components/glossary-search";
import { MoleculeField } from "@/components/molecule-field";
import { OutcomeExplorer } from "@/components/outcome-explorer";
import { SiteHeader } from "@/components/site-header";
import { StudySpine } from "@/components/study-spine";
import { limitations, models, safeguards, sources, studyStats } from "@/data/research";
import generatedResults from "@/data/generated-results.json";

type PrimaryResult = {
  delta_auroc: number;
  ci95: [number, number];
  interpretation: string;
};

export default function HomePage() {
  const complete = generatedResults.status === "complete";
  const primary = generatedResults.primary as PrimaryResult | null;
  return (
    <>
      <a className="skip-link" href="#main-content">Skip to main content</a>
      <SiteHeader />
      <main id="main-content">
        <section className="hero section-shell" id="top">
          <div className="hero-copy">
            <div className="status-line">
              <span className="live-dot" />
              {complete ? "Frozen analysis complete" : "Study execution underway"}
              <span aria-hidden="true">·</span>
              Governance clearance reported
            </div>
            <p className="hero-kicker">One question. Four matched models. No shortcuts.</p>
            <h1>
              Does a frozen molecular foundation model see <em>more</em> liver-injury signal?
            </h1>
            <p className="hero-deck">
              We are testing whether a pre-specified MAMMAL embedding improves prediction of established DILI concern beyond a strong conventional chemical model—on unfamiliar scaffolds, with every decision traceable.
            </p>
            <div className="hero-actions">
              <a className="button button--primary" href="#question">Understand the study <ArrowDown weight="bold" /></a>
              <a className="button button--ghost" href="#phases">Trace every phase <ArrowRight weight="bold" /></a>
            </div>
            <div className="scope-stamp">
              <ShieldCheck weight="duotone" />
              <span><strong>Research benchmark only</strong>Not a patient-risk calculator, diagnostic tool, or prescribing guide.</span>
            </div>
          </div>
          <MoleculeField />
        </section>

        <section className="stat-ribbon" aria-label="Study at a glance">
          <div className="section-shell stat-grid">
            {studyStats.map((stat) => (
              <div className={`stat stat--${stat.tone}`} key={stat.label}>
                <strong>{stat.value}</strong>
                <span>{stat.label}</span>
              </div>
            ))}
          </div>
        </section>

        <section className="section section-shell" id="question">
          <div className="section-heading split-heading">
            <div>
              <span className="eyebrow">The research question</span>
              <h2>Incremental value—not “AI versus chemistry.”</h2>
            </div>
            <p>The expanded model receives everything the conventional model sees, then adds one frozen MAMMAL vector. Their paired difference is the answer.</p>
          </div>
          <div className="question-grid">
            <article className="thesis-card">
              <span className="card-index">PRIMARY ESTIMAND</span>
              <div className="equation" aria-label="Delta AUROC equals AUROC of model D minus AUROC of model B">
                <span>ΔAUROC</span><b>=</b><span>AUROC<sub>D</sub></span><b>−</b><span>AUROC<sub>B</sub></span>
              </div>
              <p>A positive estimate favours adding MAMMAL. Its 95% confidence interval tells us whether the gain is convincing, practically important, or still uncertain.</p>
              <div className="benchmark-line">
                <span>0</span><i /><span className="benchmark-marker">+0.03<small>proposed practical benchmark</small></span>
              </div>
            </article>
            <article className="answer-card" id="status">
              <span className="eyebrow">The research answer</span>
              {complete && primary ? (
                <>
                  <h3>Adding frozen MAMMAL changed AUROC by {primary.delta_auroc >= 0 ? "+" : ""}{primary.delta_auroc.toFixed(3)}.</h3>
                  <p>95% CI {primary.ci95[0] >= 0 ? "+" : ""}{primary.ci95[0].toFixed(3)} to {primary.ci95[1] >= 0 ? "+" : ""}{primary.ci95[1].toFixed(3)}. {primary.interpretation}</p>
                </>
              ) : (
                <>
                  <h3>The protocol is answer-ready; the performance answer is being computed.</h3>
                  <p>{generatedResults.answer}</p>
                </>
              )}
              <ul className="check-list">
                <li><Check weight="bold" />Primary comparison locked</li>
                <li><Check weight="bold" />FDA source captured and validated</li>
                <li><Check weight="bold" />Official MAMMAL revisions pinned</li>
                <li>{complete ? <Check weight="bold" /> : <Flask weight="fill" />}{complete ? "Frozen results generated and validated" : "Embedding and modelling run in progress"}</li>
              </ul>
            </article>
          </div>
        </section>

        <section className="section section-shell dataset-section">
          <div className="dataset-copy">
            <span className="eyebrow">The evidence base</span>
            <h2>Every approved drug starts as evidence, not a clean row.</h2>
            <p>DILIrank 2.0 assigns 1,336 FDA-approved drugs to four concern categories derived from approved labelling and causality evidence. The 354 ambiguous records leave the main binary analysis before structural eligibility and duplicate resolution.</p>
            <div className="definition-pair">
              <div><strong>Positive</strong><span>vMost + vLess concern</span></div>
              <div><strong>Negative</strong><span>vNo concern—not “safe”</span></div>
            </div>
          </div>
          <DatasetDistribution />
        </section>

        <section className="section models-section" id="design">
          <div className="section-shell">
            <div className="section-heading centered-heading">
              <span className="eyebrow eyebrow--light">The matched experiment</span>
              <h2>Four views of the same molecule.</h2>
              <p>Every model uses L2-regularised logistic regression. Changing the representation—not the power of the algorithm—is the experiment.</p>
            </div>
            <div className="model-grid">
              {models.map((model) => (
                <article className={`model-card model-card--${model.accent}`} key={model.id}>
                  <div className="model-id">{model.id}</div>
                  <div className="model-content">
                    <h3>{model.name}</h3>
                    <div className="feature-blocks">
                      {model.blocks.map((block) => <span key={block}>{block}</span>)}
                    </div>
                    <p>{model.role}</p>
                  </div>
                </article>
              ))}
            </div>
            <div className="primary-contrast">
              <span className="contrast-model">B</span>
              <span>conventional evidence</span>
              <ArrowRight />
              <span className="contrast-plus">+ frozen MAMMAL</span>
              <ArrowRight />
              <span className="contrast-model contrast-model--warm">D</span>
              <strong>The only primary contrast</strong>
            </div>
          </div>
        </section>

        <section className="section section-shell" id="phases">
          <div className="section-heading split-heading">
            <div>
              <span className="eyebrow">The study spine</span>
              <h2>Six phases. Each one earns the next.</h2>
            </div>
            <p>Click a phase to inspect its work, evidence gate, and stop rule. Time alone never moves the study forward.</p>
          </div>
          <StudySpine />
        </section>

        <section className="section safeguards-section">
          <div className="section-shell">
            <div className="section-heading centered-heading compact-heading">
              <span className="eyebrow">Bias controls</span>
              <h2>The result is only as credible as the boundaries around it.</h2>
            </div>
            <div className="safeguard-grid">
              {safeguards.map((item, index) => (
                <article key={item.title}>
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <h3>{item.title}</h3>
                  <p>{item.text}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="section section-shell scaffold-explainer">
          <div className="section-heading split-heading">
            <div>
              <span className="eyebrow">Why scaffold separation matters</span>
              <h2>A near-twin in training can make a weak model look brilliant.</h2>
            </div>
            <p>Core ring-and-linker frameworks stay in one group. Acyclic drugs are similarity-clustered so related chemistry cannot quietly cross the boundary.</p>
          </div>
          <div className="split-visual">
            <div className="visual-panel visual-panel--bad">
              <div className="visual-label"><Warning weight="fill" />Random split · optimistic check only</div>
              <div className="molecule-pairs">
                <span className="mini-molecule m1">⌬—OH</span><span className="boundary" />
                <span className="mini-molecule m2">⌬—NH₂</span>
              </div>
              <p>Close analogues can land on both sides.</p>
            </div>
            <div className="visual-panel visual-panel--good">
              <div className="visual-label"><LockKey weight="fill" />Scaffold split · primary</div>
              <div className="molecule-pairs">
                <span className="molecule-cluster"><span className="mini-molecule m1">⌬—OH</span><span className="mini-molecule m2">⌬—NH₂</span></span>
                <span className="boundary" />
                <span className="mini-molecule m3">⬡—N</span>
              </div>
              <p>Related cores travel as one indivisible group.</p>
            </div>
          </div>
        </section>

        <section className="section outcomes-section" id="outcomes">
          <div className="section-shell">
            <div className="section-heading split-heading">
              <div>
                <span className="eyebrow eyebrow--light">How the answer will be read</span>
                <h2>Every possible result already has a rule.</h2>
              </div>
              <p>The confidence interval is interpreted against zero and +0.03. That keeps the conclusion from changing to fit the observed result.</p>
            </div>
            <OutcomeExplorer />
          </div>
        </section>

        <section className="section section-shell boundaries-section">
          <div className="boundaries-intro">
            <span className="eyebrow">Interpretation boundary</span>
            <h2>A molecular benchmark can be useful without pretending to be a clinic.</h2>
            <p>These limits are not footnotes. They define the most the result can honestly mean.</p>
          </div>
          <div className="limitation-stack">
            {limitations.map(([title, text], index) => (
              <article key={title}>
                <span>{index + 1}</span>
                <div><h3>{title}</h3><p>{text}</p></div>
              </article>
            ))}
          </div>
        </section>

        <section className="section evidence-section" id="evidence">
          <div className="section-shell">
            <div className="section-heading split-heading">
              <div>
                <span className="eyebrow">Primary-source trail</span>
                <h2>Claims should have somewhere to go.</h2>
              </div>
              <p>Source facts, protocol choices, and unresolved claims are kept separate. Live revisions and checksums are captured again at execution.</p>
            </div>
            <div className="source-list">
              {sources.map((source, index) => (
                <a href={source.href} target="_blank" rel="noreferrer" key={source.href}>
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <div><strong>{source.name}</strong><small>{source.note}</small></div>
                  <ArrowRight aria-hidden="true" />
                </a>
              ))}
            </div>
            <div className="repro-strip">
              <div><Database weight="duotone" /><span><strong>Immutable inputs</strong>URLs, timestamps, licences, byte sizes, SHA-256</span></div>
              <div><GitBranch weight="duotone" /><span><strong>Versioned decisions</strong>Protocol, config, code, cohort, folds, outputs</span></div>
              <div><LockKey weight="duotone" /><span><strong>Frozen predictions</strong>Every headline regenerates from one OOF artefact</span></div>
            </div>
          </div>
        </section>

        <section className="section section-shell glossary-section">
          <div className="section-heading split-heading">
            <div><span className="eyebrow">Plain-language glossary</span><h2>Technical, never mysterious.</h2></div>
            <p>Search the central terms used in the protocol and final interpretation.</p>
          </div>
          <GlossarySearch />
        </section>

        <section className="closing-section">
          <div className="section-shell closing-grid">
            <div>
              <span className="eyebrow eyebrow--light">The standard we are holding</span>
              <h2>A credible null, a clear failure, or a precise gain all count as answers.</h2>
            </div>
            <p>The project succeeds when the answer is traceable, paired, chemically honest, uncertainty-aware, and impossible to confuse with a claim about an individual patient.</p>
          </div>
        </section>
      </main>
      <footer className="site-footer">
        <div className="section-shell footer-grid">
          <div className="brand brand--footer"><span className="brand-mark">M×D</span><span><strong>MAMMAL × DILI</strong><small>research atlas</small></span></div>
          <p>Drug-level DILIrank 2.0 concern classification. Not diagnosis, causality, prescribing advice, or clinical validation.</p>
          <a href="#top">Back to top ↑</a>
        </div>
      </footer>
    </>
  );
}

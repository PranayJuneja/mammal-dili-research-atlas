type IntervalResult = {
  delta_auroc: number;
  ci95: [number, number];
  interpretation: string;
  repeat_deltas: number[];
};

type ModelResult = {
  auroc: number;
  pr_auroc: number;
  brier: number;
  calibration_intercept: number;
  calibration_slope: number;
};

type RobustnessResult = {
  primary: IntervalResult;
};

export type ResearchResults = {
  status: string;
  answer: string;
  primary: IntervalResult | null;
  models: Record<string, ModelResult>;
  update_transport: {
    paired_delta_auroc: {
      estimate: number;
      ci95: [number, number];
      interpretation: string;
    };
  } | null;
  robustness: Record<string, RobustnessResult>;
  important_false_negative_rows?: number;
  scope: string;
  provenance?: {
    protocol_lock_sha256: string;
    g3_feature_lock_sha256: string;
    g4_prediction_lock_sha256: string;
  };
};

const signed = (value: number, digits = 3) => `${value >= 0 ? "+" : ""}${value.toFixed(digits)}`;

const analysisNames: Record<string, string> = {
  vmost_vs_vno: "vMost versus vNo",
  stratified_random: "Optimistic random split",
  class_balanced: "Class-balanced learner",
};

export function ResultDashboard({ data }: { data: ResearchResults }) {
  if (data.status !== "complete" || !data.primary || !data.update_transport) return null;

  const [lower, upper] = data.primary.ci95;
  const axisMin = Math.floor((Math.min(-0.1, lower, data.primary.delta_auroc) - 0.01) * 100 + 1e-9) / 100;
  const axisMax = Math.ceil((Math.max(0.1, upper, data.primary.delta_auroc) + 0.01) * 100 - 1e-9) / 100;
  const toPosition = (value: number) => ((value - axisMin) / (axisMax - axisMin)) * 100;
  const effectLeft = toPosition(data.primary.delta_auroc);
  const intervalLeft = toPosition(lower);
  const intervalRight = toPosition(upper);
  const zeroLeft = toPosition(0);
  const benchmarkLeft = toPosition(0.03);

  return (
    <section className="section results-section" id="results" aria-labelledby="results-heading">
      <div className="section-shell">
        <div className="results-lead">
          <div>
            <span className="eyebrow eyebrow--light">Frozen research answer</span>
            <h2 id="results-heading">{signed(data.primary.delta_auroc)} AUROC added by MAMMAL.</h2>
          </div>
          <p>{data.primary.interpretation}</p>
        </div>

        <div className="effect-card">
          <div className="effect-number">
            <span>Primary paired change</span>
            <strong>{signed(data.primary.delta_auroc)}</strong>
            <small>95% CI {signed(lower)} to {signed(upper)}</small>
          </div>
          <div className="effect-plot" aria-label={`Delta AUROC ${signed(data.primary.delta_auroc)}, 95% confidence interval ${signed(lower)} to ${signed(upper)}`}>
            <div className="effect-labels">
              <span className="effect-label-start">{signed(axisMin, 2)}</span>
              <span style={{ left: `${zeroLeft}%` }}>0</span>
              <span style={{ left: `${benchmarkLeft}%` }}>+0.03</span>
              <span className="effect-label-end">{signed(axisMax, 2)}</span>
            </div>
            <div className="effect-axis">
              <i className="effect-zero" style={{ left: `${zeroLeft}%` }} />
              <i className="effect-benchmark" style={{ left: `${benchmarkLeft}%` }} />
              <span data-testid="effect-interval" className="effect-interval" style={{ left: `${intervalLeft}%`, width: `${Math.max(1, intervalRight - intervalLeft)}%` }} />
              <b className="effect-point" style={{ left: `${effectLeft}%` }} />
            </div>
            <small>Complete-scaffold paired bootstrap · 2,000 resamples</small>
          </div>
        </div>

        <div className="result-grid">
          {Object.entries(data.models).map(([model, metrics]) => (
            <article className={`result-model result-model--${model.toLowerCase()}`} key={model}>
              <span>Model {model}</span>
              <strong>{metrics.auroc.toFixed(3)}</strong>
              <small>mean AUROC</small>
              <dl>
                <div><dt>PR-AUROC</dt><dd>{metrics.pr_auroc.toFixed(3)}</dd></div>
                <div><dt>Brier</dt><dd>{metrics.brier.toFixed(3)}</dd></div>
                <div><dt>Cal. slope</dt><dd>{metrics.calibration_slope.toFixed(3)}</dd></div>
              </dl>
            </article>
          ))}
        </div>

        <div className="result-secondary-grid">
          <article className="transport-result">
            <span className="eyebrow">Untouched update transport</span>
            <h3>{signed(data.update_transport.paired_delta_auroc.estimate)} AUROC</h3>
            <p>95% CI {signed(data.update_transport.paired_delta_auroc.ci95[0])} to {signed(data.update_transport.paired_delta_auroc.ci95[1])}. {data.update_transport.paired_delta_auroc.interpretation}</p>
          </article>
          <article className="robustness-results">
            <span className="eyebrow">Pre-specified robustness</span>
            <div>
              {Object.entries(data.robustness).map(([key, result]) => (
                <p key={key}><strong>{analysisNames[key] ?? key}</strong><span>{signed(result.primary.delta_auroc)} ({signed(result.primary.ci95[0])} to {signed(result.primary.ci95[1])})</span></p>
              ))}
            </div>
          </article>
        </div>

        <div className="result-boundary">
          <strong>{data.important_false_negative_rows ?? 0} model-drug error rows audited · 113 unique drugs</strong>
          <p>{data.scope}</p>
          {data.provenance && (
            <details>
              <summary>Show frozen lineage</summary>
              <code>Protocol {data.provenance.protocol_lock_sha256}</code>
              <code>G3 {data.provenance.g3_feature_lock_sha256}</code>
              <code>G4 {data.provenance.g4_prediction_lock_sha256}</code>
            </details>
          )}
        </div>

        <nav className="result-downloads" aria-label="Download final research materials">
          <a href="/results/research_report.md" download>Full research report</a>
          <a href="/results/final_reporting_addendum.md" download>Final reporting addendum</a>
          <a href="/results/plain_language_summary.md" download>Plain-language summary</a>
          <a href="/results/tripod_ai_resolution_addendum.csv" download>TRIPOD+AI resolution audit</a>
          <a href="/results/kuhs_submission_protocol.md" download>KUHS protocol draft</a>
          <a href="/results/important_false_negatives.csv" download>Error audit data</a>
        </nav>
      </div>
    </section>
  );
}

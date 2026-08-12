"use client";

import { useState } from "react";

import { outcomes } from "@/data/research";

export function OutcomeExplorer() {
  const [selected, setSelected] = useState(outcomes[0].id);
  const outcome = outcomes.find((item) => item.id === selected) ?? outcomes[0];

  return (
    <div className="outcome-explorer">
      <div className="outcome-tabs" role="tablist" aria-label="Possible result interpretations">
        {outcomes.map((item) => (
          <button
            key={item.id}
            type="button"
            role="tab"
            aria-selected={item.id === outcome.id}
            onClick={() => setSelected(item.id)}
          >
            {item.label}
          </button>
        ))}
      </div>
      <div className="outcome-panel" role="tabpanel">
        <div className="interval-figure" aria-label={`Illustrative interval: ${outcome.range}`}>
          <div className="interval-scale">
            <span>− gain</span>
            <span>0</span>
            <span>+0.03</span>
            <span>+ gain</span>
          </div>
          <div className="interval-axis">
            <i className="zero-line" />
            <i className="delta-line" />
            {outcome.width > 0 ? (
              <span
                className="confidence-mark"
                style={{ left: `${outcome.position - outcome.width / 2}%`, width: `${outcome.width}%` }}
              >
                <b style={{ left: "50%" }} />
              </span>
            ) : (
              <span className="failure-mark" style={{ left: `${outcome.position}%` }}>gate failed</span>
            )}
          </div>
          <small>Illustrative logic—not observed study data</small>
        </div>
        <div className="outcome-copy">
          <span className="eyebrow">{outcome.range}</span>
          <h3>{outcome.headline}</h3>
          <p>{outcome.detail}</p>
          <div className="caution-note"><strong>Boundary</strong>{outcome.caution}</div>
        </div>
      </div>
    </div>
  );
}


"use client";

import { ArrowRight, CheckCircle, Circle, Flask } from "@phosphor-icons/react";
import { useState } from "react";

import { phases } from "@/data/research";

export function StudySpine() {
  const [activeId, setActiveId] = useState(phases[0].id);
  const active = phases.find((phase) => phase.id === activeId) ?? phases[0];

  return (
    <div className="study-spine">
      <div className="spine-track" role="tablist" aria-label="Research phases">
        {phases.map((phase) => (
          <button
            key={phase.id}
            type="button"
            role="tab"
            aria-selected={phase.id === active.id}
            aria-controls={`phase-panel-${phase.id}`}
            id={`phase-tab-${phase.id}`}
            className={phase.id === active.id ? "phase-tab is-active" : "phase-tab"}
            onClick={() => setActiveId(phase.id)}
          >
            <span className={`phase-node phase-node--${phase.status}`}>
              {phase.status === "cleared" ? <CheckCircle weight="fill" /> : phase.status === "next" ? <Flask weight="fill" /> : <Circle weight="fill" />}
            </span>
            <span className="phase-tab-copy">
              <small>{phase.gate}</small>
              <strong>{phase.title}</strong>
            </span>
            <ArrowRight className="phase-arrow" aria-hidden="true" />
          </button>
        ))}
      </div>
      <article
        className="phase-panel"
        id={`phase-panel-${active.id}`}
        role="tabpanel"
        aria-labelledby={`phase-tab-${active.id}`}
      >
        <div className="phase-panel-head">
          <span className="eyebrow">{active.period} · {active.gate}</span>
          <span className={`status-pill status-pill--${active.status}`}>
            {active.status === "cleared" ? "Clearance reported" : active.status === "next" ? "Active next gate" : "Planned"}
          </span>
        </div>
        <h3>{active.question}</h3>
        <p className="phase-summary">{active.summary}</p>
        <div className="phase-columns">
          <div>
            <h4>Work performed</h4>
            <ul>
              {active.work.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </div>
          <div>
            <h4>Evidence required to pass</h4>
            <ul className="evidence-list">
              {active.evidence.map((item) => <li key={item}><CheckCircle aria-hidden="true" />{item}</li>)}
            </ul>
          </div>
        </div>
        <div className="stop-rule"><strong>Stop rule</strong><span>{active.stopRule}</span></div>
      </article>
    </div>
  );
}

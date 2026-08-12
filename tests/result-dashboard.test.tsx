import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ResultDashboard } from "../src/components/result-dashboard";
import type { ResearchResults } from "../src/components/result-dashboard";

const pending: ResearchResults = {
  status: "pending",
  answer: "Outcome execution is paused.",
  primary: null,
  models: {},
  update_transport: null,
  robustness: {},
  scope: "Drug-level benchmark only.",
};

const complete: ResearchResults = {
  status: "complete",
  answer: "Frozen answer.",
  primary: {
    delta_auroc: 0.012,
    ci95: [-0.01, 0.035],
    interpretation: "Inconclusive for superiority and practical importance.",
    repeat_deltas: [0.01, 0.02, 0.0, 0.015, 0.015],
  },
  models: {
    B: {
      auroc: 0.72,
      pr_auroc: 0.68,
      brier: 0.21,
      calibration_intercept: 0.01,
      calibration_slope: 0.96,
    },
    D: {
      auroc: 0.732,
      pr_auroc: 0.69,
      brier: 0.2,
      calibration_intercept: 0.0,
      calibration_slope: 0.98,
    },
  },
  update_transport: {
    paired_delta_auroc: {
      estimate: 0.004,
      ci95: [-0.02, 0.03],
      interpretation: "Exploratory transport estimate.",
    },
  },
  robustness: {},
  important_false_negative_rows: 4,
  scope: "Drug-level benchmark only.",
};

describe("ResultDashboard", () => {
  it("does not render performance before a complete result packet exists", () => {
    const { container } = render(<ResultDashboard data={pending} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("renders the frozen answer and report downloads for complete results", () => {
    render(<ResultDashboard data={complete} />);
    expect(screen.getByRole("heading", { name: "+0.012 AUROC added by MAMMAL." })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Full research report" })).toHaveAttribute(
      "href",
      "/results/research_report.md",
    );
  });

  it("expands the effect scale instead of clipping a wide confidence interval", () => {
    const wide = {
      ...complete,
      primary: { ...complete.primary!, ci95: [-0.2, 0.14] as [number, number] },
    };
    const { container } = render(<ResultDashboard data={wide} />);
    const interval = container.querySelector<HTMLElement>("[data-testid='effect-interval']");
    expect(interval).not.toBeNull();
    if (!interval) throw new Error("Effect interval was not rendered");
    expect(interval.style.left).not.toBe("0%");
    expect(interval.style.width).not.toBe("100%");
    expect(container).toHaveTextContent("-0.21");
    expect(container).toHaveTextContent("+0.15");
  });
});

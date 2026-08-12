import { describe, expect, it } from "vitest";

import { labelCounts, models, outcomes, phases } from "../src/data/research";

describe("research narrative invariants", () => {
  it("matches the validated DILIrank 2.0 source counts", () => {
    expect(labelCounts.reduce((sum, item) => sum + item.value, 0)).toBe(1336);
    expect(labelCounts.filter((item) => item.label !== "Ambiguous").reduce((sum, item) => sum + item.value, 0)).toBe(982);
  });

  it("changes exactly one information block in the primary contrast", () => {
    const modelB = models.find((model) => model.id === "B");
    const modelD = models.find((model) => model.id === "D");
    expect(modelB).toBeDefined();
    expect(modelD?.blocks).toEqual([...(modelB?.blocks ?? []), "Frozen MAMMAL embedding"]);
  });

  it("covers the complete gated execution and interpretation map", () => {
    expect(phases).toHaveLength(6);
    expect(new Set(phases.map((phase) => phase.id)).size).toBe(6);
    expect(outcomes.map((outcome) => outcome.id)).toEqual(
      expect.arrayContaining(["meaningful", "inconclusive", "worse", "infeasible"]),
    );
  });
});

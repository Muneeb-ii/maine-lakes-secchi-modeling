import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  EXPLAINABILITY_LAKE_CONTEXT_FEATURES,
  FRIENDLY_FEATURE_LABELS,
  getFriendlyFeatureLabel,
} from "./featureLabels.js";

describe("featureLabels", () => {
  it("covers every editable chemistry feature with a friendly label", () => {
    const editable = ["DOMAX", "DOMIN", "TPEC", "TPBG", "PH", "COLOR", "CONDUCT", "ALK"];
    for (const key of editable) {
      assert.ok(FRIENDLY_FEATURE_LABELS[key], `missing friendly label for ${key}`);
    }
  });

  it("covers lake context explainability features", () => {
    for (const key of EXPLAINABILITY_LAKE_CONTEXT_FEATURES) {
      assert.ok(FRIENDLY_FEATURE_LABELS[key], `missing friendly label for ${key}`);
    }
  });

  it("uses phosphorus wording aligned with sample types", () => {
    assert.match(FRIENDLY_FEATURE_LABELS.TPEC, /bottom/i);
    assert.match(FRIENDLY_FEATURE_LABELS.TPBG, /surface/i);
  });

  it("falls back to API label when no override exists", () => {
    assert.equal(getFriendlyFeatureLabel("year", "Year"), "Year");
  });
});

import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  EXPLAINABILITY_LAKE_CONTEXT_FEATURES,
  FRIENDLY_FEATURE_LABELS,
  LAKE_CHEMISTRY_FEATURES,
  getFriendlyFeatureLabel,
} from "./featureLabels.js";

describe("featureLabels", () => {
  it("covers every editable and locked chemistry feature with a friendly label", () => {
    const editable = ["DOMAX", "DOMIN", "TMAX", "TMIN", "TPEC", "TPBG"];
    for (const key of editable) {
      assert.ok(FRIENDLY_FEATURE_LABELS[key], `missing friendly label for ${key}`);
    }
    for (const key of LAKE_CHEMISTRY_FEATURES) {
      assert.ok(FRIENDLY_FEATURE_LABELS[key], `missing friendly label for ${key}`);
      assert.ok(
        EXPLAINABILITY_LAKE_CONTEXT_FEATURES.includes(key),
        `${key} should be shown as lake context`
      );
    }
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
    assert.match(FRIENDLY_FEATURE_LABELS.TPEC, /surface/i);
    assert.match(FRIENDLY_FEATURE_LABELS.TPBG, /bottom/i);
  });

  it("falls back to API label when no override exists", () => {
    assert.equal(getFriendlyFeatureLabel("year", "Year"), "Year");
  });
});

import assert from "node:assert/strict";
import test from "node:test";

import { formatSignedMeters } from "./formattersCore.js";

test("formatSignedMeters prefixes positive values with plus", () => {
  assert.equal(formatSignedMeters(0.42), "+0.42 m");
});

test("formatSignedMeters keeps negative sign in text-only mode", () => {
  assert.equal(formatSignedMeters(-0.42), "-0.42 m");
});

test("formatSignedMeters absolute mode omits sign for icon pairing", () => {
  assert.equal(formatSignedMeters(-0.42, { absolute: true }), "0.42 m");
  assert.equal(formatSignedMeters(0.42, { absolute: true }), "0.42 m");
});

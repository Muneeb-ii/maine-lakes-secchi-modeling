import test from "node:test";
import assert from "node:assert/strict";

import { formatLakeSearchDisplay, parseLakeSearchInput } from "./copy.js";

test("formatLakeSearchDisplay shows MIDAS id and lake name", () => {
  assert.equal(formatLakeSearchDisplay("c3420", "Crystal Lake"), "C3420, Crystal Lake");
});

test("formatLakeSearchDisplay falls back to id when name is missing", () => {
  assert.equal(formatLakeSearchDisplay("C3420", ""), "C3420");
});

test("parseLakeSearchInput extracts id and name from display label", () => {
  assert.deepEqual(parseLakeSearchInput("C3420, Crystal Lake"), {
    midasId: "C3420",
    nameHint: "Crystal Lake",
  });
});

test("parseLakeSearchInput handles bare MIDAS id", () => {
  assert.deepEqual(parseLakeSearchInput("c3420"), {
    midasId: "C3420",
    nameHint: "",
  });
});

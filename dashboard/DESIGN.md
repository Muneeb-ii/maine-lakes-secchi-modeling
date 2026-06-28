# Maine Lakes Secchi Dashboard — Design Notes

Agent-oriented UI reference for the dashboard frontend. For repo architecture, routes, commands, and API contracts, see `CONTEXT.md` at the repository root.

**Quick map:** `/` landing · `/playground` scenario explorer · `/trends` placeholder · `/contributors` · `/modeling-process` · localStorage snapshots (`dashboardSavedScenarios`) · Claro tour on **playground only**.

---

## Dashboard brand mark (not Claro)

| Asset | Path | Use |
|-------|------|-----|
| Favicon | `app/frontend/public/favicon.svg` | Browser tab |
| Component | `components/brand/DashboardLogo.jsx` | Inline SVG |
| Shell | `components/brand/SiteBrand.jsx` | Logo + optional “Back to home” |

**Motif:** double `lake-accent` ring; **left** = white sky + wavy lake (`#7EB8E8`); **right** = Secchi disk quadrants (blue / white). Separate from the green Claro Secchi-face mascot.

At 16×16 favicon size the thin white separator ring may vanish — acceptable; add a simplified favicon variant later if needed.

**Lake water (left half):** `#7EB8E8` on white sky with a wavy horizon at disk center.

### Where the mark appears

| Surface | Component |
|---------|-----------|
| Landing hero | `DashboardLogo` beside `LANDING_TITLE` |
| Info / inner pages | `SiteBrand` in `InfoPageNav` (“Back to home” + logo) |
| Playground / trends nav | `InfoPageNav` with workspace eyebrow pill (playground uses `Waves` icon) |
| Browser tab | `public/favicon.svg`; `theme-color` `#005AB5` in `index.html` |

Playground `DashboardHeader` no longer repeats the workspace eyebrow — the nav row above it owns that label.

Playground `InfoPageNav` also exposes an **`actions`** slot (right side) for the unit-system toggle beside the workspace eyebrow.

---

## Display unit system

| System | Length | Area | Default |
|--------|--------|------|---------|
| Metric | m | ha | yes |
| Imperial | ft | acres | |

- Stored value: `metric` or `imperial` (`dashboardUnitSystem`). Legacy `us` normalizes to `imperial`.

- **UI only** — sliders, hero, trajectory chart, clarity bands, lake profile fields, and saved-scenario labels convert for display. Chemistry units (ppm, ppb, SPU, µS/cm, pH, alkalinity) are not converted.
- **Canonical model units never change** — Secchi stays meters in state and API payloads; max depth stays feet; area stays acres. Use `toDisplay` / `toCanonical` at input boundaries (`lib/units.js`).
- Toggle: `UnitSystemToggle` in playground nav; persistence key `dashboardUnitSystem` (`UNIT_SYSTEM_KEY` in `lib/constants.js`).
- Clarity band thresholds (`CLARITY_BANDS.max`) stay in meters internally; `getClarityRangeLabel` and chart reference lines render converted labels.

---

## Lake map picker

- **Entry points:** map icon beside lake search plus “Show on map” pin action in search results; opens a centered modal over a scrim (`lake-map-layer`, z-index 270).
- **Data:** `GET /lakes/locations` returns all baseline lakes with finite `latitude` / `longitude` (and optional `area_acres`). Search results use the same `LakeSearchItem` shape.
- **Map:** Leaflet (`leaflet` npm dep); default center Maine `[44.35, -69.2]`, zoom 7; focused lake zoom 12. Pins use `lake-map-pin`; current lake uses `lake-map-pin-current`.
- **Marker labels:** lake names stay hidden while zoomed out and appear only at zoom 11+ via `lake-map-labels-visible`, so the statewide view stays uncluttered.
- **Popup card:** use a compact white card with a `lake-sectionLake`/`lake-accent` rail, MIDAS badge, labeled coordinate/area rows, and a subtle popup-enter motion. Keep radius at `rounded-lg`; do not nest cards inside the popup.
- **Selection:** popup “Use this lake” calls the same `onSelectLake` handler as search.
- **Color rule:** map picker is lake/workspace UI, not Claro. Use `lake-sectionLake` / `lake-accent`; do not use Claro green (`--claro`, `claro-button`) inside map popup cards.
- **Claro tour:** map button anchor `data-claro-target="lake-map-button"`; tour step `lake-map` before lake profile. `ClaroGuide` accepts `onStepExit` so leaving the map step closes an open map modal.

---

## Parameter sensitivity hints

Each editable chemistry slider (`ParameterSlider.jsx`) shows a **local effect** hint below the control after the scenario commits (`featureCommitVersion`).

| Direction | Meaning | Style |
|-----------|---------|-------|
| `clearer` | Nearby increase predicts clearer water | green left rail (`sensitivity-hint-clearer`) |
| `murkier` | Nearby increase predicts murkier water | amber left rail (`sensitivity-hint-murkier`) |
| `flat` | Little effect near current value | neutral rail |
| `mixed` / `range_sensitive` | Effect changes across the slider range | split icon, mixed rail |

- Data from `POST /predict_scenario/sensitivity` via `useScenarioSensitivity` (debounced `DEBOUNCE_MS`, same payload shape as predict).
- Subtext: “At this lake and current scenario” — not global SHAP; complements the drivers panel.
- Excluded measurements show “Measurement not included”; loading and error states use neutral styling.
- Claro tour step `parameter-panel` targets `parameter-slider-control` and mentions sensitivity copy.

---

## Info-page draft state

`lib/siteStatus.js` → `SHOW_INFO_PAGES_IN_PROGRESS_NOTICE` (default `true`).

When enabled, `PageInProgressNotice` renders an amber callout on `/contributors` and `/modeling-process`. Set the flag `false` and remove the component when copy is finalized.

`/modeling-process` content is split into **Playground** (served model narrative) and **Trends** (placeholder section with link to `/trends`).

---

## Color & accent roles

The palette follows Okabe-Ito–inspired hues on a light WCAG-first base. Each color has a **semantic job** — do not reuse a role for a second purpose.

| Token | Hex | Role |
|-------|-----|------|
| `lake-accent` | `#005AB5` | **Primary actions** — filled buttons (Save, CTAs), default links, prediction/parameters/trajectory section badges |
| `lake-sectionLake` | `#0072B2` | Lake profile context |
| `lake-sectionDrivers` | `#009E73` | Explainability / “what influenced this prediction” |
| `lake-sectionCompare` | `#CC79A7` | Save & compare / reference-line compare |
| `lake-amber` | `#E69F00` | Trends workspace, caution callouts |
| `lake-claro` | `#1A9B6E` | **Claro persona** — launcher, tour chrome, assistant identity (filled gradient control) |
| `lake-claro-bright` | `#09ED68` | Gradient highlight + one Secchi disk quadrant in the mascot |
| `lake-claro-text` | `#0F6B4A` | Kicker / labels on white surfaces |
| `delta-up` / `delta-down` | `#00836D` / `#D55E00` | Clearer vs murkier Secchi change (always paired with +/- icons) |

Body copy on tinted surfaces stays `text-slate-900` / `text-slate-700`. Status never relies on color alone.

---

## Claro persona color

**Claro uses mint green — not `lake-accent` blue.** Blue is reserved for workspace CTAs (Save, links). Claro is a **persistent agent presence**: muted white launcher with visible Secchi mascot, soft green tour chrome, and `claro-button` for in-flow actions.

### Implemented palette

| Token | Hex | Use |
|-------|-----|-----|
| `--claro` | `#1A9B6E` | Spotlight ring, prompt left stripe, hover borders |
| `--claro-bright` | `#3ECF8E` | One Secchi quadrant in mascot (muted vs `#09ED68`) |
| `--claro-soft` | `#E8F7F1` | Launcher hover, `claro-button` fill |
| `--claro-text` | `#0F6B4A` | Launcher label, kicker on white |

**Launcher:** white pill + `claro-launcher-mark` (white disk behind mascot) so the Secchi icon stays readable. Sized `h-12` mobile, `h-14` + `text-lg` on `lg+`.

**Footer dock:** `useClaroFooterOffset` lifts the fixed launcher when `#app-footer` enters the viewport so Claro does not cover partner logos.

**First-visit prompt:** centered modal with scrim (`claro-prompt-layer` / `claro-prompt-scrim`, z-index 250–252) instead of a card stacked above the launcher. Session-local open state; dismiss does not persist to `localStorage` (tour completion still does).

### Claro vs workspace buttons

| Element | Class / style | Avoid |
|---------|---------------|-------|
| Fixed launcher | `claro-launcher` — muted white pill, green text, mascot in mark | Loud gradient; `action-button-primary` |
| Start tour / Next / Finish | `claro-button` — soft green fill | `action-button-primary` |
| Tour kicker | `claro-kicker` | `text-lake-accent` |
| Spotlight ring | `rgba(26, 155, 110, 0.65)` | Accent blue |
| Dismiss / Back | `action-button` (neutral outline) | — |

`CLARO_ACCENTS` in `lib/theme.js` centralizes class names for future agent shell.

---

## Claro mascot icon

**Secchi disk with a face on the disk** (not a disk worn as a hat) — `components/claro/ClaroMascot.jsx`.

- Four quadrants: `#1A9B6E`, white (face), `#09ED68`, `#1A9B6E`
- Face (eyes + smile) in the white quadrant
- Rope loop at top
- Full-color SVG so it reads on the green launcher and on white tour cards

**Do not** use generic Lucide glyphs (`LifeBuoy`, `Bot`, `Sparkles`) for Claro identity.

### Persona copy (unchanged)

Claro: calm, plain-spoken water-clarity guide. v1 is a deterministic **playground-only** tour; later agent features reuse the same `data-claro-target` anchors and `CLARO_PERSONA` copy in `lib/claroTourContent.js`. Do not mount `ClaroGuide` on `/trends` or info routes.

---

## Save & compare mental model

| Action | What it does | What it does *not* do |
|--------|----------------|------------------------|
| **Save this scenario** | Bookmarks a snapshot of current sliders, included measurements, and predicted Secchi depth in this browser (`localStorage`); optional label for quick identification | Does not auto-select compare |
| **Compare** | Shows the saved snapshot’s Secchi as a dashed reference line on the trajectory chart and reports delta vs current sliders (automatic when a snapshot is selected) | Does not change slider values |
| **Load snapshot** | Restores the snapshot’s `features` and `includedFeatures`; triggers a new prediction | Does not clear scenario history chart; does not reset to lake baseline |
| **Restore lake defaults** | Resets sliders to the lake baseline and clears trajectory chart history | Does not delete saved snapshots or clear compare selection globally |
| **Delete saved scenario** | Removes the selected snapshot from the menu (with confirmation) | Cannot compare or load after delete |

The action bar is grouped into three sections: **Your current session**, **Save a snapshot**, and **Use a saved snapshot**, each with a short description of what the controls do.

## Saved scenario schema (`schemaVersion: 1`)

Stored under `dashboardSavedScenarios` (`SAVED_SCENARIOS_KEY` in `lib/constants.js`, max 12 entries):

```json
{
  "schemaVersion": 1,
  "id": "1700000000000",
  "lakeId": "C3420",
  "lakeName": "Example Lake",
  "label": "High phosphorus trial",
  "predictionMeters": 4.5,
  "timestamp": "2024-06-01T12:00:00.000Z",
  "features": { "PH": 7.1 },
  "includedFeatures": ["PH"]
}
```

- `label` is optional (max 60 chars, trimmed); empty string when not provided.
- Legacy entries without `includedFeatures` are migrated on read: keys with finite numeric values in `features` are inferred.
- Dropdown display: labeled snapshots show `label (date)`; unlabeled show `date — X.X m`.

## Compare rules

- Compare dropdown lists **only snapshots for the current lake**.
- If other-lake snapshots exist, a helper note shows the count and suggests switching lakes.
- Compare banner and chart reference line appear only when a valid same-lake snapshot is selected and a forecast is available.
- Orphan compare IDs (deleted snapshot, stale tab) are cleared automatically.

## Load rules

- Load is enabled when a same-lake snapshot is selected in the dropdown.
- Confirms before overwriting if current sliders differ from the snapshot.
- Merges snapshot editable values onto the current lake baseline so locked lake-context keys stay correct.

## Playground lower layout

- **Save & compare** and **What influenced this prediction** share the first lower row on desktop. Drivers should size to that row, not stretch beside the full scenario-history area.
- **Changes you tried** sits below as a full-width workspace panel.
- On desktop, Changes you tried uses a two-column body: chart on the left, change-log table on the right.
- The chart and table must be driven by the same `chartHistory` points. The table is a readable row view of the plotted session history, not separate state.
- On mobile and tablet widths, the Changes you tried panel stacks the chart and table vertically.

## Save guard

Save is enabled only when a forecast exists **and** at least one editable measurement differs from the lake baseline (value or include/exclude state).

---

## Save & compare roadmap (deferred)

### C. Multi-overlay on chart

- `compareScenarioIds: string[]` (max 2–3) with Okabe-Ito colors.
- Multiple `ReferenceLine`s + legend entries in `TrajectoryChart`.
- Checkbox list or multi-select instead of single dropdown.

### D. Session vs saved separation

- Trajectory chart = **this session’s path**; saved snapshots = **bookmarks** — consider visual badge on chart when current sliders match a saved snapshot.

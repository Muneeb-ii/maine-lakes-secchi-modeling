import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Gauge } from "lucide-react";
import { formatSignedMeters } from "../../lib/formatters";
import {
  ARIA_CONTRIBUTION_CLEARER,
  ARIA_CONTRIBUTION_MURKIER,
  EXPLAINABILITY_HIDE_ALL,
  EXPLAINABILITY_INTRO,
  EXPLAINABILITY_MISSING,
  EXPLAINABILITY_SHOW_ALL,
  SECTION_LABELS,
} from "../../lib/copy";
import { getFriendlyFeatureLabel } from "../../lib/featureLabels";
import { HELP_CONTENT } from "../../lib/helpContent";
import { useReducedMotion } from "../../lib/useReducedMotion";
import { SectionHelp } from "../ui/SectionHelp";
import { ContributorCard } from "./ContributorCard";

const listVariants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.06 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 8 },
  visible: { opacity: 1, y: 0 },
};

export function ExplainabilityPanel({ forecast, featureConfig }) {
  const [expanded, setExpanded] = useState(false);
  const reducedMotion = useReducedMotion();

  const topExplainability = useMemo(() => {
    if (!forecast?.explainability?.waterfall) return [];
    return [...forecast.explainability.waterfall]
      .sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution))
      .slice(0, 3);
  }, [forecast]);

  const waterfall = forecast?.explainability?.waterfall || [];

  return (
    <div className="panel p-5">
      <h2 className="section-heading">
        <Gauge className="w-4 h-4 text-lake-accent" aria-hidden />
        {SECTION_LABELS.explainability}
        <SectionHelp content={HELP_CONTENT.explainability} />
      </h2>
      <p className="mt-2 text-sm text-slate-600">{EXPLAINABILITY_INTRO}</p>

      {waterfall.length ? (
        <>
          <motion.ul
            className="mt-4 space-y-3 list-none m-0 p-0"
            variants={reducedMotion ? undefined : listVariants}
            initial={reducedMotion ? false : "hidden"}
            animate="visible"
            key={topExplainability.map((i) => i.feature).join("-")}
          >
            {topExplainability.map((item) => (
              <motion.li
                key={item.feature}
                variants={reducedMotion ? undefined : itemVariants}
                className="list-none"
              >
                <ContributorCard
                  item={item}
                  label={featureConfig?.features?.[item.feature]?.label}
                  unit={featureConfig?.features?.[item.feature]?.unit}
                />
              </motion.li>
            ))}
          </motion.ul>

          <button
            type="button"
            className="mt-4 text-base text-lake-accent hover:text-blue-700 transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-lake-accent rounded px-1"
            onClick={() => setExpanded((previous) => !previous)}
            aria-expanded={expanded}
          >
            {expanded ? EXPLAINABILITY_HIDE_ALL : EXPLAINABILITY_SHOW_ALL}
          </button>

          <AnimatePresence>
            {expanded && (
              <motion.div
                initial={reducedMotion ? false : { opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={reducedMotion ? undefined : { opacity: 0, height: 0 }}
                className="mt-4 space-y-2 max-h-56 overflow-y-auto pr-1"
              >
                {waterfall.map((item, index) => {
                  const isPositive = item.contribution >= 0;
                  return (
                    <div
                      key={`${item.feature}-${index}`}
                      className="text-sm text-slate-700 flex justify-between gap-4 py-1 border-b border-slate-200 last:border-0"
                    >
                      <span>
                        {getFriendlyFeatureLabel(
                          item.feature,
                          featureConfig?.features?.[item.feature]?.label
                        )}
                      </span>
                      <span
                        className={isPositive ? "text-delta-up" : "text-delta-down"}
                        aria-label={
                          isPositive ? ARIA_CONTRIBUTION_CLEARER : ARIA_CONTRIBUTION_MURKIER
                        }
                      >
                        {formatSignedMeters(item.contribution)}
                      </span>
                    </div>
                  );
                })}
              </motion.div>
            )}
          </AnimatePresence>
        </>
      ) : (
        <p className="mt-4 text-base text-lake-amber">
          {EXPLAINABILITY_MISSING}
        </p>
      )}
    </div>
  );
}

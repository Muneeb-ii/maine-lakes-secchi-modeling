import { motion } from "framer-motion";
import { useReducedMotion } from "../../lib/useReducedMotion";

const sectionMotion = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0 },
};

function MotionSection({ id, children, reducedMotion, className = "" }) {
  const motionProps = reducedMotion
    ? {}
    : {
        initial: "hidden",
        animate: "visible",
        variants: sectionMotion,
        transition: { duration: 0.35, ease: [0.22, 1, 0.36, 1] },
      };

  return (
    <motion.section id={id} className={`scroll-mt-8 ${className}`} {...motionProps}>
      {children}
    </motion.section>
  );
}

export function AppShell({
  header,
  lakeSection,
  parametersSection,
  resultsSection,
  driversSection,
}) {
  const reducedMotion = useReducedMotion();

  return (
    <div className="dashboard-bg min-h-screen text-slate-100">
      <div className="max-w-[1600px] mx-auto p-6 lg:p-8 space-y-6">
        {header}

        <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
          <MotionSection
            id="lake"
            reducedMotion={reducedMotion}
            className="order-1 xl:order-2 xl:col-span-4 xl:col-start-9"
          >
            {lakeSection}
          </MotionSection>

          <MotionSection
            id="parameters"
            reducedMotion={reducedMotion}
            className="order-2 xl:order-3 xl:col-span-4 xl:col-start-9"
          >
            {parametersSection}
          </MotionSection>

          <MotionSection
            id="results"
            reducedMotion={reducedMotion}
            className="order-3 xl:order-1 xl:col-span-8 xl:col-start-1 xl:row-start-1 xl:row-span-3 space-y-6 min-w-0"
          >
            {resultsSection}
          </MotionSection>

          <MotionSection
            id="drivers"
            reducedMotion={reducedMotion}
            className="order-4 xl:order-4 xl:col-span-4 xl:col-start-9"
          >
            {driversSection}
          </MotionSection>
        </div>
      </div>
    </div>
  );
}

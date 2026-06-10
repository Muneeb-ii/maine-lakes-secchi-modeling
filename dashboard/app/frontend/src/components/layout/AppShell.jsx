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
  predictionSection,
  scenarioSection,
  trajectorySection,
  resultsSection,
  driversSection,
  footer,
}) {
  const reducedMotion = useReducedMotion();

  return (
    <div className="dashboard-bg flex min-h-screen flex-col text-slate-900">
      <main className="flex-1">
        <div className="mx-auto w-full max-w-[1600px] space-y-4 p-3 sm:p-4 lg:space-y-6 lg:p-8">
          {header}

          <div className="grid grid-cols-1 gap-4 lg:gap-6 xl:grid-cols-12 xl:items-start">
            <MotionSection
              id="prediction"
              reducedMotion={reducedMotion}
              className="order-1 xl:col-span-8 min-w-0"
            >
              {predictionSection || resultsSection}
            </MotionSection>

            <MotionSection
              id="lake"
              reducedMotion={reducedMotion}
              className="order-2 xl:col-span-4"
            >
              {lakeSection}
            </MotionSection>

            <MotionSection
              id="parameters"
              reducedMotion={reducedMotion}
              className="order-3 xl:col-span-12"
            >
              {parametersSection}
            </MotionSection>

            <MotionSection
              id="scenario"
              reducedMotion={reducedMotion}
              className="order-4 xl:col-span-7 min-w-0 xl:self-stretch"
            >
              {scenarioSection}
            </MotionSection>

            <MotionSection
              id="drivers"
              reducedMotion={reducedMotion}
              className="order-5 xl:col-span-5 xl:self-stretch"
            >
              {driversSection}
            </MotionSection>

            <MotionSection
              id="trajectory"
              reducedMotion={reducedMotion}
              className="order-6 xl:col-span-12 min-w-0"
            >
              {trajectorySection}
            </MotionSection>
          </div>
        </div>
      </main>
      {footer}
    </div>
  );
}

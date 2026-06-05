import { motion } from "framer-motion";
import {
  ArrowRight,
  BarChart3,
  FlaskConical,
  Layers,
  LineChart,
  Waves,
} from "lucide-react";
import { CLARITY_BANDS } from "../../lib/constants";
import {
  LANDING_CLARITY_TITLE,
  LANDING_DESTINATIONS,
  LANDING_EYEBROW,
  LANDING_HIGHLIGHTS,
  LANDING_HOW_IT_WORKS_TITLE,
  LANDING_INTRO,
  LANDING_TITLE,
  LANDING_WORKSPACES_INTRO,
  LANDING_WORKSPACES_TITLE,
  MODEL_FOOTNOTE,
  SECCHI_DIRECTION_NOTE,
} from "../../lib/copy";
import { PAGE_CONTAINER } from "../../lib/layoutClasses";
import { ROUTES } from "../../lib/routes";
import { useReducedMotion } from "../../lib/useReducedMotion";
import { AppFooter } from "./AppFooter";

const fadeUp = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0 },
};

const highlightIcons = [FlaskConical, LineChart, Layers];

const clarityTone = [
  "border-l-4 border-delta-down bg-orange-50/80",
  "border-l-4 border-lake-amber bg-amber-50/70",
  "border-l-4 border-delta-up bg-emerald-50/80",
];

const destinations = [
  {
    ...LANDING_DESTINATIONS.trends,
    path: ROUTES.trends,
    icon: BarChart3,
    accent: "border-lake-amber/40 bg-amber-50/80 text-lake-amber",
    featured: false,
  },
  {
    ...LANDING_DESTINATIONS.playground,
    path: ROUTES.playground,
    icon: FlaskConical,
    accent: "border-lake-accent/30 bg-blue-50/90 text-lake-accent",
    featured: true,
  },
];

function MotionBlock({ children, className = "", reducedMotion, delay = 0 }) {
  if (reducedMotion) {
    return <div className={className}>{children}</div>;
  }

  return (
    <motion.div
      className={className}
      initial="hidden"
      animate="visible"
      variants={fadeUp}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1], delay }}
    >
      {children}
    </motion.div>
  );
}

export function LandingPage() {
  const reducedMotion = useReducedMotion();

  return (
    <div className="dashboard-bg flex min-h-screen flex-col text-slate-900">
      <main className="flex-1">
        <div className={`${PAGE_CONTAINER} space-y-5 py-6 sm:py-8 lg:py-10`}>
          <MotionBlock reducedMotion={reducedMotion}>
            <div className="landing-hero-panel overflow-hidden">
              <div className="grid lg:grid-cols-12">
                <div className="space-y-4 border-b border-lake-border p-5 sm:p-6 lg:col-span-7 lg:border-b-0 lg:border-r">
                  <p className="inline-flex items-center gap-2 rounded-full border border-lake-accent/25 bg-white px-3 py-1.5 text-sm font-semibold uppercase tracking-wide text-lake-accent">
                    <Waves className="h-4 w-4" aria-hidden />
                    {LANDING_EYEBROW}
                  </p>
                  <h1 className="display-title text-3xl leading-tight sm:text-4xl lg:text-[2.5rem]">
                    {LANDING_TITLE}
                  </h1>
                  <p className="text-base leading-7 text-slate-700">{LANDING_INTRO}</p>
                  <div className="info-card !bg-slate-50/90">
                    <p className="info-label">{SECCHI_DIRECTION_NOTE}</p>
                    <p className="info-value !mt-1.5 font-normal text-slate-700">{MODEL_FOOTNOTE}</p>
                  </div>
                </div>

                <aside className="landing-inset space-y-3 p-5 sm:p-6 lg:col-span-5">
                  <h2 className="section-heading text-base">{LANDING_CLARITY_TITLE}</h2>
                  <ul className="space-y-2.5" aria-label="Secchi clarity bands">
                    {CLARITY_BANDS.map((band, index) => (
                      <li
                        key={band.label}
                        className={`rounded-lg border border-lake-border/80 px-3 py-2.5 ${clarityTone[index]}`}
                      >
                        <p className="text-sm font-semibold text-slate-900">{band.label}</p>
                        <p className="mt-0.5 text-sm leading-snug text-slate-600">
                          {band.description}
                        </p>
                      </li>
                    ))}
                  </ul>
                </aside>
              </div>
            </div>
          </MotionBlock>

          <MotionBlock reducedMotion={reducedMotion} delay={0.05}>
            <div className="grid gap-5 lg:grid-cols-12 lg:items-stretch">
              <section className="panel flex flex-col p-5 lg:col-span-4 lg:p-6">
                <h2 className="section-heading">{LANDING_HOW_IT_WORKS_TITLE}</h2>
                <ul className="mt-4 flex flex-1 flex-col gap-4">
                  {LANDING_HIGHLIGHTS.map((item, index) => {
                    const Icon = highlightIcons[index] ?? Layers;
                    return (
                      <li
                        key={item.title}
                        className="flex gap-3 border-b border-slate-200 pb-4 last:border-b-0 last:pb-0"
                      >
                        <span className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-lake-accent/10 text-lake-accent">
                          <Icon className="h-4 w-4" aria-hidden />
                        </span>
                        <div>
                          <h3 className="text-base font-semibold text-slate-950">{item.title}</h3>
                          <p className="mt-1 text-sm leading-6 text-slate-700">{item.body}</p>
                        </div>
                      </li>
                    );
                  })}
                </ul>
              </section>

              <section className="flex flex-col gap-4 lg:col-span-8">
                <div>
                  <h2 className="section-heading text-lg">{LANDING_WORKSPACES_TITLE}</h2>
                  <p className="mt-1.5 text-base leading-7 text-slate-700">
                    {LANDING_WORKSPACES_INTRO}
                  </p>
                </div>
                <div className="grid flex-1 gap-4 sm:grid-cols-2">
                  {destinations.map((item) => {
                    const Icon = item.icon;
                    return (
                      <a
                        key={item.path}
                        href={item.path}
                        className={`group panel flex flex-col p-5 text-left transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-lake-accent ${
                          item.featured
                            ? "shadow-[0_18px_40px_rgba(0,90,181,0.12)] ring-2 ring-lake-accent/15 hover:-translate-y-0.5 hover:border-lake-accent"
                            : "hover:-translate-y-0.5 hover:border-slate-400 hover:shadow-panel"
                        }`}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <span
                            className={`inline-flex h-10 w-10 items-center justify-center rounded-lg border ${item.accent}`}
                          >
                            <Icon className="h-4 w-4" aria-hidden />
                          </span>
                          <span className="rounded-full border border-lake-border bg-slate-50 px-2.5 py-1 text-sm font-semibold uppercase tracking-wide text-slate-600">
                            {item.status}
                          </span>
                        </div>
                        <span className="mt-4 text-xl font-semibold text-slate-950">
                          {item.title}
                        </span>
                        <span className="mt-2 flex-1 text-base leading-7 text-slate-700">
                          {item.description}
                        </span>
                        <span className="mt-4 inline-flex items-center gap-2 text-base font-semibold text-lake-accent">
                          {item.cta}
                          <ArrowRight
                            className="h-4 w-4 transition group-hover:translate-x-1"
                            aria-hidden
                          />
                        </span>
                      </a>
                    );
                  })}
                </div>
              </section>
            </div>
          </MotionBlock>
        </div>
      </main>
      <AppFooter />
    </div>
  );
}

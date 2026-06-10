import { motion } from "framer-motion";
import {
  ArrowRight,
  BarChart3,
  FlaskConical,
  Layers,
  LineChart,
} from "lucide-react";
import {
  LANDING_DESTINATIONS,
  LANDING_HEADER_HOOK_LINES,
  LANDING_HEADER_STATS,
  LANDING_HIGHLIGHTS,
  LANDING_HOW_IT_WORKS_TITLE,
  LANDING_TITLE,
  LANDING_WORKSPACES_TITLE,
} from "../../lib/copy";
import { PAGE_CONTAINER } from "../../lib/layoutClasses";
import { ROUTES } from "../../lib/routes";
import { useReducedMotion } from "../../lib/useReducedMotion";
import { DashboardLogo } from "../brand/DashboardLogo";
import { AppFooter } from "./AppFooter";
import { ClarityScaleBar } from "./ClarityScaleBar";

const fadeUp = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0 },
};

const highlightIcons = [FlaskConical, LineChart, Layers];

const destinations = [
  {
    ...LANDING_DESTINATIONS.trends,
    path: ROUTES.trends,
    icon: BarChart3,
    accent: "border-lake-amber/40 bg-amber-50/80 text-lake-amber",
    statusBadgeClass: "status-badge-soon",
    featured: false,
  },
  {
    ...LANDING_DESTINATIONS.playground,
    path: ROUTES.playground,
    icon: FlaskConical,
    accent: "border-lake-accent/30 bg-blue-50/90 text-lake-accent",
    statusBadgeClass: "status-badge-ready",
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
        <div className={`${PAGE_CONTAINER} space-y-4 py-4 sm:py-6 lg:py-8`}>
          <MotionBlock reducedMotion={reducedMotion}>
            <header className="landing-hero-panel hero-column-wash overflow-hidden p-4 sm:p-5 lg:p-6">
              <div className="grid gap-5 max-md:grid-cols-1 md:grid-cols-[minmax(0,1fr)_auto] md:items-center md:gap-6 lg:gap-8">
                <div className="flex min-w-0 flex-col items-center gap-4 max-md:text-center md:flex-row md:items-center md:gap-5 md:text-left">
                  <DashboardLogo className="h-14 w-14 shrink-0 md:h-16 md:w-16" />
                  <div className="min-w-0 flex-1">
                    <h1 className="display-title text-2xl leading-tight sm:text-3xl lg:text-4xl">
                      {LANDING_TITLE}
                    </h1>
                    <p className="body-copy mt-2 leading-snug">
                      {LANDING_HEADER_HOOK_LINES[0]}
                      <br />
                      {LANDING_HEADER_HOOK_LINES[1]}
                    </p>
                  </div>
                </div>

                <dl className="grid min-w-0 grid-cols-3 gap-2 sm:gap-3 max-md:w-full md:min-w-[18rem] md:max-w-md md:shrink-0 lg:min-w-[20rem] lg:max-w-lg lg:gap-4">
                  {LANDING_HEADER_STATS.map((stat) => (
                    <div key={stat.label} className="landing-stat-card info-card-accent">
                      <dt className="info-label">{stat.label}</dt>
                      <dd className="info-value mt-0.5 tabular-nums">{stat.value}</dd>
                    </div>
                  ))}
                </dl>
              </div>

              <ClarityScaleBar className="mt-5 border-t border-lake-border/70 pt-4 sm:pt-5" />
            </header>
          </MotionBlock>

          <MotionBlock reducedMotion={reducedMotion} delay={0.05}>
            <div className="grid gap-4 lg:grid-cols-12 lg:items-stretch">
              <section className="panel panel-accent-left panel-accent-prediction flex flex-col p-4 sm:p-5 lg:col-span-4">
                <h2 className="section-heading">{LANDING_HOW_IT_WORKS_TITLE}</h2>
                <ul className="mt-3 flex flex-1 flex-col gap-3">
                  {LANDING_HIGHLIGHTS.map((item, index) => {
                    const Icon = highlightIcons[index] ?? Layers;
                    return (
                      <li
                        key={item.title}
                        className="flex gap-3 border-b border-slate-200 pb-3 last:border-b-0 last:pb-0"
                      >
                        <span className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-lake-accent/10 text-lake-accent">
                          <Icon className="h-4 w-4" aria-hidden />
                        </span>
                        <div>
                          <h3 className="section-subheading">{item.title}</h3>
                          <p className="body-copy mt-0.5">{item.body}</p>
                        </div>
                      </li>
                    );
                  })}
                </ul>
              </section>

              <section className="flex flex-col gap-3 lg:col-span-8">
                <h2 className="section-heading">{LANDING_WORKSPACES_TITLE}</h2>
                <div className="grid flex-1 gap-3 sm:grid-cols-2">
                  {destinations.map((item) => {
                    const Icon = item.icon;
                    return (
                      <a
                        key={item.path}
                        href={item.path}
                        className={`group panel flex flex-col p-4 sm:p-5 text-left transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-lake-accent ${
                          item.featured
                            ? "shadow-[0_18px_40px_rgba(0,90,181,0.12)] ring-2 ring-lake-accent/15 hover:-translate-y-0.5 hover:border-lake-accent"
                            : "hover:-translate-y-0.5 hover:border-slate-400 hover:shadow-panel"
                        }`}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <span
                            className={`inline-flex h-9 w-9 items-center justify-center rounded-lg border ${item.accent}`}
                          >
                            <Icon className="h-4 w-4" aria-hidden />
                          </span>
                          <span className={item.statusBadgeClass}>{item.status}</span>
                        </div>
                        <span className="section-subheading mt-3">{item.title}</span>
                        <span className="body-copy mt-1.5 flex-1">{item.description}</span>
                        <span className="mt-3 inline-flex items-center gap-2 text-lg font-semibold text-lake-accent">
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

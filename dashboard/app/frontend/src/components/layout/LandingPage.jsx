import { motion } from "framer-motion";
import { ArrowRight, BarChart3, FlaskConical, MapPin } from "lucide-react";
import {
  LANDING_FEATURED_LAKE,
  LANDING_HEADER_HOOK_LINES,
  LANDING_TITLE,
} from "../../lib/copy";
import { PAGE_CONTAINER } from "../../lib/layoutClasses";
import { ROUTES } from "../../lib/routes";
import { useReducedMotion } from "../../lib/useReducedMotion";
import { DashboardLogo } from "../brand/DashboardLogo";
import { AppFooter } from "./AppFooter";

const featuredLakeQuery = `lake=${LANDING_FEATURED_LAKE.id}`;
const trendsPath = `${ROUTES.trends}?${featuredLakeQuery}`;
const playgroundPath = `${ROUTES.playground}?${featuredLakeQuery}`;

const fadeUp = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0 },
};

function MotionBlock({ children, className = "", reducedMotion, delay = 0, style }) {
  if (reducedMotion) {
    return <div className={className} style={style}>{children}</div>;
  }

  return (
    <motion.div
      className={className}
      style={style}
      initial="hidden"
      animate="visible"
      variants={fadeUp}
      transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1], delay }}
    >
      {children}
    </motion.div>
  );
}

function SnapshotStep({
  accent,
  eyebrow,
  title,
  body,
  cta,
  href,
  icon: Icon,
  image,
  alt,
  preview,
  reducedMotion,
  delay,
}) {
  const workspaceTheme = accent === "trends"
    ? {
        "--workspace-accent": "var(--accent-amber)",
        "--workspace-soft": "#fffbeb",
        "--workspace-border": "rgba(230, 159, 0, 0.42)",
        "--workspace-glow": "0 0 0 1px rgba(230, 159, 0, 0.14), 0 18px 42px rgba(230, 159, 0, 0.16)",
        "--workspace-glow-hover": "0 0 0 2px rgba(230, 159, 0, 0.24), 0 20px 48px rgba(230, 159, 0, 0.23)",
        "--workspace-tag-bg": "var(--dashboard-accent)",
        "--workspace-tag-text": "#ffffff",
        "--workspace-tag-border": "var(--dashboard-accent)",
      }
    : {
        "--workspace-accent": "var(--accent)",
        "--workspace-soft": "var(--accent-soft)",
        "--workspace-border": "rgba(0, 90, 181, 0.34)",
        "--workspace-glow": "0 0 0 1px rgba(0, 90, 181, 0.13), 0 18px 42px rgba(0, 90, 181, 0.16)",
        "--workspace-glow-hover": "0 0 0 2px rgba(0, 90, 181, 0.22), 0 20px 48px rgba(0, 90, 181, 0.23)",
        "--workspace-tag-bg": "var(--dashboard-accent)",
        "--workspace-tag-text": "#ffffff",
        "--workspace-tag-border": "var(--dashboard-accent)",
      };

  return (
    <MotionBlock
      reducedMotion={reducedMotion}
      delay={delay}
      style={workspaceTheme}
      className={`landing-story-step landing-story-step-${accent} landing-workspace-card landing-workspace-card-${accent}`}
    >
      <a href={href} className="group block focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-lake-accent">
        <div className="landing-snapshot-frame">
          {preview ?? <img className="landing-snapshot-image" src={image} alt={alt} loading="lazy" />}
        </div>
        <div className="landing-story-step-copy">
          <div className="landing-story-step-heading">
            <span className="landing-story-step-icon" aria-hidden="true"><Icon className="h-4 w-4" /></span>
            <span className="landing-story-step-eyebrow">{eyebrow}</span>
          </div>
          <h3 className="landing-story-step-title">{title}</h3>
          <p className="landing-story-step-body">{body}</p>
          <span className={`landing-story-step-cta landing-story-step-cta-${accent}`}>
            <span>{cta}</span>
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" aria-hidden="true" />
          </span>
        </div>
      </a>
    </MotionBlock>
  );
}

export function LandingPage() {
  const reducedMotion = useReducedMotion();

  return (
    <div className="dashboard-bg flex min-h-screen flex-col text-slate-900">
      <main className="flex-1">
        <div className={`${PAGE_CONTAINER} space-y-4 py-4 sm:py-6 lg:py-8`}>
          <MotionBlock reducedMotion={reducedMotion}>
            <header className="landing-hero-panel landing-hero-shell overflow-hidden p-4 sm:p-6 lg:p-7">
              <div className="landing-hero-copy">
                <div className="flex items-start gap-4 sm:gap-5">
                  <DashboardLogo className="h-14 w-14 shrink-0 sm:h-16 sm:w-16" />
                  <div className="min-w-0">
                    <h1 className="display-title text-3xl leading-tight sm:text-4xl lg:text-5xl">{LANDING_TITLE}</h1>
                    <p className="body-copy mt-2 max-w-2xl leading-snug">
                      {LANDING_HEADER_HOOK_LINES[0]} {LANDING_HEADER_HOOK_LINES[1]}
                    </p>
                  </div>
                </div>
                <div className="landing-hero-actions mt-5 flex flex-wrap gap-2.5">
                  <a href={trendsPath} className="landing-hero-cta landing-hero-cta-trends">
                    See Wilson Lake’s record <ArrowRight className="h-4 w-4" aria-hidden="true" />
                  </a>
                  <a href={playgroundPath} className="landing-hero-cta landing-hero-cta-playground">
                    Try a what-if <ArrowRight className="h-4 w-4" aria-hidden="true" />
                  </a>
                </div>
              </div>

              <div className="landing-featured-lake" aria-label={`Featured example: ${LANDING_FEATURED_LAKE.name}`}>
                <div className="landing-featured-lake-mark" aria-hidden="true"><MapPin className="h-5 w-5" /></div>
                <div className="min-w-0">
                  <p className="landing-featured-lake-label">Featured example</p>
                  <p className="landing-featured-lake-name">{LANDING_FEATURED_LAKE.name}</p>
                  <p className="landing-featured-lake-meta">
                    {LANDING_FEATURED_LAKE.id} · {LANDING_FEATURED_LAKE.region} · {LANDING_FEATURED_LAKE.historyYears} monitored years
                  </p>
                </div>
                <div className="landing-featured-lake-wave" aria-hidden="true" />
              </div>
            </header>
          </MotionBlock>

          <MotionBlock reducedMotion={reducedMotion} delay={0.06}>
            <section className="landing-story-panel panel p-4 sm:p-6 lg:p-7" aria-labelledby="landing-story-title">
              <div className="landing-story-intro">
                <div className="min-w-0">
                  <p className="landing-story-kicker">One lake, two lenses</p>
                  <h2 id="landing-story-title" className="display-title mt-1 text-2xl leading-tight sm:text-3xl">
                    See the record. Then test a what-if.
                  </h2>
                  <p className="body-copy mt-2 max-w-3xl">
                    Follow {LANDING_FEATURED_LAKE.name} from its measured summer history into a scenario you can change yourself.
                  </p>
                </div>
                <div className="landing-story-context">
                  <span className="landing-story-context-icon" aria-hidden="true"><MapPin className="h-4 w-4" /></span>
                  <span>
                    <strong>{LANDING_FEATURED_LAKE.name}</strong>
                    <small>{LANDING_FEATURED_LAKE.latestYear} record · outlook available</small>
                  </span>
                </div>
              </div>

              <div className="landing-story-flow">
                <SnapshotStep
                  accent="trends"
                  eyebrow="Trends"
                  title="Read the record"
                  body={`See ${LANDING_FEATURED_LAKE.historyYears} monitored years at a glance, then place a baseline outlook beside the observed record.`}
                  cta="Open Wilson Lake trends"
                  href={trendsPath}
                  icon={BarChart3}
                  preview={(
                    <div className="landing-trends-preview" aria-label="Wilson Lake Trends workspace showing the observed record and baseline outlook">
                      <div className="landing-trends-preview-panel">
                        <span>Observed record</span>
                        <img src="/landing/wilson-trends-history-chart.png" alt="" loading="lazy" />
                      </div>
                      <div className="landing-trends-preview-panel">
                        <span>Baseline outlook</span>
                        <img src="/landing/wilson-trends-forecast-chart.png" alt="" loading="lazy" />
                      </div>
                    </div>
                  )}
                  reducedMotion={reducedMotion}
                  delay={0.12}
                />

                <div className="landing-story-connector" aria-hidden="true">
                  <ArrowRight className="h-5 w-5" />
                </div>

                <SnapshotStep
                  accent="playground"
                  eyebrow="Playground"
                  title="Try a what-if"
                  body="Start from the lake’s typical profile, adjust water conditions, and see how the predicted clarity responds."
                  cta="Try Wilson Lake in Playground"
                  href={playgroundPath}
                  icon={FlaskConical}
                  preview={(
                    <div className="landing-playground-preview" aria-label="Wilson Lake Playground showing predicted Secchi depth and scenario changes">
                      <div className="landing-playground-preview-panel">
                        <span>Predicted Secchi depth</span>
                        <img src="/landing/wilson-playground-prediction-strip.png" alt="" loading="lazy" />
                      </div>
                      <div className="landing-playground-preview-panel">
                        <span>Scenario history</span>
                        <img src="/landing/wilson-playground-changes-strip.png" alt="" loading="lazy" />
                      </div>
                    </div>
                  )}
                  reducedMotion={reducedMotion}
                  delay={0.2}
                />
              </div>

            </section>
          </MotionBlock>
        </div>
      </main>
      <AppFooter />
    </div>
  );
}

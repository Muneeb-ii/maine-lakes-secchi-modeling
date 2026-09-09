import { BarChart3, BookOpen, FlaskConical } from "lucide-react";
import { LANDING_DESTINATIONS, PLAYGROUND_TITLE } from "../../lib/copy";
import { MODELING_PAGE } from "../../lib/infoPagesCopy";
import { PAGE_CONTAINER } from "../../lib/layoutClasses";
import { ROUTES } from "../../lib/routes";
import { SECTION_ACCENTS } from "../../lib/theme";
import { SectionHeadingIcon } from "../ui/SectionHeadingIcon";
import { InfoPageNav } from "./InfoPageNav";
import { PageFrame } from "./PageFrame";

function ModelingSection({ accent, section }) {
  const isTrends = accent === "trends";
  const bulletClass = isTrends ? "text-lake-amber" : "text-lake-accent";
  const metricClass = isTrends ? "info-card-accent-trends" : "info-card-accent";
  const sectionSpacing = section.stats?.length ? "pb-8" : "";

  return (
    <section id={section.id} className={`scroll-mt-8 border-t border-lake-border pt-8 first:border-t-0 first:pt-0 ${sectionSpacing}`}>
      <h2 className="section-heading text-xl text-slate-950">
        <SectionHeadingIcon section={accent} icon={BookOpen} />
        {section.title}
      </h2>
      <div className="mt-4 space-y-4">
        {section.paragraphs?.map((paragraph) => (
          <p key={paragraph} className="text-base leading-7 text-slate-700">
            {paragraph}
          </p>
        ))}
      </div>

      {section.stats?.length > 0 && (
        <dl className="mt-5 grid gap-3 sm:grid-cols-3">
          {section.stats.map((stat) => (
            <div key={stat.label} className={metricClass}>
              <dt className="info-label">{stat.label}</dt>
              <dd className="info-value tabular-nums">{stat.value}</dd>
            </div>
          ))}
        </dl>
      )}

      {section.featureGroups?.length > 0 && (
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          {section.featureGroups.map((group) => (
            <div key={group.name} className="info-card h-full">
              <h3 className="text-base font-semibold text-slate-950">{group.name}</h3>
              <p className="mt-1 text-base leading-7 text-slate-700">{group.description}</p>
              <ul className="mt-3 space-y-1.5 text-base leading-7 text-slate-700">
                {group.features.map((feature) => (
                  <li key={feature} className="flex gap-2">
                    <span className={bulletClass} aria-hidden>
                      •
                    </span>
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}

      {section.list?.length > 0 && (
        <ul className="mt-5 space-y-2 text-base leading-7 text-slate-700">
          {section.list.map((item) => (
            <li key={item} className="flex gap-3">
              <span
                className={`mt-2 h-1.5 w-1.5 shrink-0 rounded-full ${isTrends ? "bg-lake-amber" : "bg-lake-accent"}`}
                aria-hidden
              />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function ModelingWorkspacePanel({
  accent,
  children,
  id,
  icon,
  summary,
  title,
  washClassName,
  cta,
  ctaClassName,
  ctaHref,
  ctaIcon: CtaIcon,
}) {
  return (
    <div
      id={id}
      className={`panel mt-5 p-6 sm:p-8 ${SECTION_ACCENTS[accent].panelAccentClass} ${washClassName || ""}`}
    >
      <div className="border-b border-lake-border pb-8">
        <h2 className={`display-title modeling-workspace-title-${accent} flex flex-wrap items-center gap-3 text-2xl sm:text-3xl`}>
          <SectionHeadingIcon section={accent} icon={icon} />
          {title}
        </h2>
        <p className="mt-3 text-base leading-7 text-slate-700">{summary}</p>
      </div>
      {children}
      {cta && CtaIcon && (
        <div className="mt-8 border-t border-lake-border pt-6">
          <a href={ctaHref} className={`workspace-action-button w-fit ${ctaClassName || ""}`}>
            <CtaIcon className="h-4 w-4" aria-hidden />
            {cta}
          </a>
        </div>
      )}
    </div>
  );
}

export function ModelingProcessPage() {
  const { eyebrow, title, intro, playground, trends } = MODELING_PAGE;

  return (
    <PageFrame>
      <article className={`${PAGE_CONTAINER} py-6 sm:py-10 lg:py-12`}>
        <InfoPageNav eyebrow={eyebrow} />
        <header className="panel modeling-page-title-panel p-6 sm:p-8">
          <h1 className="display-title text-3xl sm:text-4xl">{title}</h1>
          <p className="mt-4 text-lg leading-8 text-slate-700">{intro}</p>
        </header>

        <ModelingWorkspacePanel
          accent="prediction"
          icon={FlaskConical}
          summary={playground.summary}
          title={PLAYGROUND_TITLE}
          washClassName="hero-wash-prediction"
          cta={LANDING_DESTINATIONS.playground.cta}
          ctaClassName="workspace-action-button-playground"
          ctaHref={ROUTES.playground}
          ctaIcon={FlaskConical}
        >
          {playground.sections.map((section) => (
            <ModelingSection key={section.id} accent="prediction" section={section} />
          ))}
        </ModelingWorkspacePanel>

        <ModelingWorkspacePanel
          accent="trends"
          id="trends-modeling"
          icon={BarChart3}
          summary={trends.summary}
          title={LANDING_DESTINATIONS.trends.title}
          washClassName="hero-wash-trends"
          cta={LANDING_DESTINATIONS.trends.cta}
          ctaClassName="workspace-action-button-trends"
          ctaHref={ROUTES.trends}
          ctaIcon={BarChart3}
        >
          {trends.sections.map((section) => (
            <ModelingSection key={section.id} accent="trends" section={section} />
          ))}
        </ModelingWorkspacePanel>
      </article>
    </PageFrame>
  );
}

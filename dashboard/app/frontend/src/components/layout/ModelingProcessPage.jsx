import { BarChart3, BookOpen, FlaskConical } from "lucide-react";
import { LANDING_DESTINATIONS, PLAYGROUND_TITLE } from "../../lib/copy";
import { MODELING_PAGE } from "../../lib/infoPagesCopy";
import { PAGE_CONTAINER } from "../../lib/layoutClasses";
import { ROUTES } from "../../lib/routes";
import { SECTION_ACCENTS } from "../../lib/theme";
import { SectionHeadingIcon } from "../ui/SectionHeadingIcon";
import { InfoPageNav } from "./InfoPageNav";
import { PageFrame } from "./PageFrame";
import { PageInProgressNotice } from "./PageInProgressNotice";

const TRENDS_PANEL_WASH =
  "linear-gradient(135deg, rgba(230, 159, 0, 0.08) 0%, #ffffff 55%)";

function ModelingSection({ section }) {
  return (
    <section id={section.id} className="scroll-mt-8 border-t border-lake-border pt-8 first:border-t-0 first:pt-0">
      <h2 className="section-heading text-xl text-slate-950">
        <SectionHeadingIcon section="drivers" icon={BookOpen} />
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
            <div key={stat.label} className="info-card-accent">
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
                    <span className="text-lake-accent" aria-hidden>
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
              <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-lake-accent" aria-hidden />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export function ModelingProcessPage() {
  const { eyebrow, title, intro, playground, trends } = MODELING_PAGE;

  return (
    <PageFrame>
      <article className={`${PAGE_CONTAINER} py-6 sm:py-10 lg:py-12`}>
        <InfoPageNav eyebrow={eyebrow} />
        <PageInProgressNotice />
        <header className={`panel p-6 sm:p-8 ${SECTION_ACCENTS.prediction.panelAccentClass} hero-wash-prediction`}>
          <h1 className="display-title text-3xl sm:text-4xl">{title}</h1>
          <p className="mt-4 text-lg leading-8 text-slate-700">{intro}</p>
        </header>

        <div className={`panel mt-5 p-6 sm:p-8 ${SECTION_ACCENTS.prediction.panelAccentClass}`}>
          <div className="border-b border-lake-border pb-8">
            <h2 className="display-title flex flex-wrap items-center gap-3 text-2xl sm:text-3xl">
              <SectionHeadingIcon section="prediction" icon={FlaskConical} />
              {PLAYGROUND_TITLE}
            </h2>
            <p className="mt-3 max-w-3xl text-base leading-7 text-slate-700">{playground.summary}</p>
          </div>
          {playground.sections.map((section) => (
            <ModelingSection key={section.id} section={section} />
          ))}
        </div>

        <div
          id="trends-modeling"
          className={`panel mt-5 p-6 sm:p-8 ${SECTION_ACCENTS.trends.panelAccentClass}`}
          style={{ backgroundImage: TRENDS_PANEL_WASH }}
        >
          <div className="flex flex-wrap items-start justify-between gap-3">
            <h2 className="display-title flex flex-wrap items-center gap-3 text-2xl sm:text-3xl">
              <SectionHeadingIcon section="trends" icon={BarChart3} />
              {LANDING_DESTINATIONS.trends.title}
            </h2>
            <span className="status-badge-soon">{LANDING_DESTINATIONS.trends.status}</span>
          </div>
          <p className="mt-3 text-base font-medium leading-7 text-slate-700">{trends.summary}</p>
          <div className="mt-4 space-y-4">
            {trends.paragraphs.map((paragraph) => (
              <p key={paragraph} className="max-w-3xl text-base leading-7 text-slate-700">
                {paragraph}
              </p>
            ))}
          </div>
          <a href={ROUTES.trends} className="action-button mt-6 inline-flex">
            <BarChart3 className="h-4 w-4" aria-hidden />
            {trends.workspaceCta}
          </a>
        </div>
      </article>
    </PageFrame>
  );
}

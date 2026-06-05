import { MODELING_PAGE } from "../../lib/infoPagesCopy";
import { PAGE_CONTAINER } from "../../lib/layoutClasses";
import { InfoPageNav } from "./InfoPageNav";
import { PageFrame } from "./PageFrame";

function ModelingSection({ section }) {
  return (
    <section id={section.id} className="scroll-mt-8 border-t border-lake-border pt-8 first:border-t-0 first:pt-0">
      <h2 className="section-heading text-xl text-slate-950">{section.title}</h2>
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
            <div key={stat.label} className="info-card">
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
              <p className="mt-1 text-sm leading-6 text-slate-600">{group.description}</p>
              <ul className="mt-3 space-y-1.5 text-sm leading-6 text-slate-700">
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
  const { eyebrow, title, intro, sections } = MODELING_PAGE;

  return (
    <PageFrame>
      <article className={`${PAGE_CONTAINER} py-6 sm:py-10 lg:py-12`}>
        <InfoPageNav />
        <header className="panel p-6 sm:p-8">
          <p className="text-sm font-semibold uppercase tracking-wide text-lake-accent">{eyebrow}</p>
          <h1 className="display-title mt-3 text-3xl sm:text-4xl">{title}</h1>
          <p className="mt-4 text-base leading-7 text-slate-700">{intro}</p>
        </header>

        <div className="panel mt-5 p-6 sm:p-8">
          {sections.map((section) => (
            <ModelingSection key={section.id} section={section} />
          ))}
        </div>
      </article>
    </PageFrame>
  );
}

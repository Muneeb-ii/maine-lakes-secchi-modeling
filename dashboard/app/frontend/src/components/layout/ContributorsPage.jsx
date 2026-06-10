import { Building2, ExternalLink, Users } from "lucide-react";
import { CONTRIBUTORS_PAGE } from "../../lib/infoPagesCopy";
import { PAGE_CONTAINER } from "../../lib/layoutClasses";
import { SECTION_ACCENTS } from "../../lib/theme";
import { SectionHeadingIcon } from "../ui/SectionHeadingIcon";
import { InfoPageNav } from "./InfoPageNav";
import { PageFrame } from "./PageFrame";

export function ContributorsPage() {
  const { eyebrow, title, intro, developers, partners } = CONTRIBUTORS_PAGE;

  return (
    <PageFrame>
      <section className={`${PAGE_CONTAINER} py-6 sm:py-10 lg:py-12`}>
        <InfoPageNav />
        <div className={`panel p-6 sm:p-8 ${SECTION_ACCENTS.prediction.panelAccentClass}`}>
          <p className="inline-flex items-center rounded-full border border-lake-accent/25 bg-lake-accentSoft px-3 py-1.5 text-sm font-semibold uppercase tracking-wide text-lake-accent">
            {eyebrow}
          </p>
          <h1 className="display-title mt-3 text-3xl sm:text-4xl">{title}</h1>
          <p className="mt-4 max-w-3xl text-lg leading-8 text-slate-700">{intro}</p>

          <div className="mt-8 grid gap-8 lg:grid-cols-2 lg:gap-10">
            <div>
              <h2 className="section-heading text-lg">
                <SectionHeadingIcon section="prediction" icon={Users} />
                {developers.title}
              </h2>
              <ul className="mt-3 space-y-1 text-base text-slate-900">
                {developers.names.map((name) => (
                  <li key={name}>{name}</li>
                ))}
              </ul>
              <p className="mt-2 text-base text-slate-700">{developers.affiliation}</p>
            </div>

            <div className="border-t border-lake-border pt-8 lg:border-l lg:border-t-0 lg:pl-10 lg:pt-0">
              <h2 className="section-heading text-lg">
                <SectionHeadingIcon section="lake" icon={Building2} />
                {partners.title}
              </h2>
              <ul className="mt-4 space-y-4">
                {partners.items.map((partner) => (
                  <li key={partner.name} className="info-card-accent">
                    <a
                      href={partner.href}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1.5 text-base font-semibold text-lake-accent hover:text-blue-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-lake-accent"
                    >
                      {partner.name}
                      <ExternalLink className="h-4 w-4" aria-hidden />
                    </a>
                    <p className="mt-1.5 text-base leading-7 text-slate-700">{partner.detail}</p>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>
    </PageFrame>
  );
}

import { Building2, ExternalLink, Users } from "lucide-react";
import { CONTRIBUTORS_PAGE } from "../../lib/infoPagesCopy";
import { PAGE_CONTAINER } from "../../lib/layoutClasses";
import { SECTION_ACCENTS } from "../../lib/theme";
import { SectionHeadingIcon } from "../ui/SectionHeadingIcon";
import { InfoPageNav } from "./InfoPageNav";
import { PageFrame } from "./PageFrame";
import { PageInProgressNotice } from "./PageInProgressNotice";

const CONTRIBUTOR_ACCENT_CLASSES = {
  lake: {
    section: "contributor-section-lake",
    card: "contributor-card-lake",
    role: "text-lake-sectionLake",
  },
  drivers: {
    section: "contributor-section-drivers",
    card: "contributor-card-drivers",
    role: "text-lake-sectionDrivers",
  },
};

export function ContributorsPage() {
  const { eyebrow, title, intro, developers, partners } = CONTRIBUTORS_PAGE;

  return (
    <PageFrame>
      <section className={`${PAGE_CONTAINER} py-6 sm:py-10 lg:py-12`}>
        <InfoPageNav eyebrow={eyebrow} />
        <PageInProgressNotice />
        <div className={`panel p-6 sm:p-8 ${SECTION_ACCENTS.prediction.panelAccentClass}`}>
          <h1 className="display-title text-3xl sm:text-4xl">{title}</h1>
          <p className="mt-4 text-lg leading-8 text-slate-700">{intro}</p>

          <div className="mt-8 space-y-8">
            <div>
              <h2 className="section-heading text-lg">
                <SectionHeadingIcon section="prediction" icon={Users} />
                {developers.title}
              </h2>
              <div className="mt-4 space-y-6">
                {developers.sections.map((section) => (
                  <section
                    key={section.title}
                    className={`contributor-section ${
                      CONTRIBUTOR_ACCENT_CLASSES[section.accent]?.section || "contributor-section-lake"
                    }`}
                  >
                    <h3 className="contributor-section-title">{section.title}</h3>
                    <ul className="mt-3 grid gap-3 md:grid-cols-2">
                      {section.people.map((contributor) => (
                        <li
                          key={contributor.name}
                          className={`contributor-card ${
                            CONTRIBUTOR_ACCENT_CLASSES[section.accent]?.card || "contributor-card-lake"
                          }`}
                        >
                          <p className="text-base font-semibold text-slate-950">{contributor.name}</p>
                          <p
                            className={`mt-1 text-sm font-semibold uppercase tracking-wide ${
                              CONTRIBUTOR_ACCENT_CLASSES[section.accent]?.role || "text-lake-sectionLake"
                            }`}
                          >
                            {contributor.role}
                          </p>
                          <p className="mt-1.5 text-base leading-7 text-slate-700">{contributor.detail}</p>
                        </li>
                      ))}
                    </ul>
                  </section>
                ))}
              </div>
              <p className="mt-2 text-base text-slate-700">{developers.affiliation}</p>
            </div>

            <div className="border-t border-lake-border pt-8">
              <h2 className="section-heading text-lg">
                <SectionHeadingIcon section="lake" icon={Building2} />
                {partners.title}
              </h2>
              <ul className="mt-4 grid gap-4 md:grid-cols-3">
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

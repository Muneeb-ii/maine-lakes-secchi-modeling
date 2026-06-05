import colbyLogo from "../../assets/logos/colbyseal.png";
import lakesLogo from "../../assets/logos/7lakesalliance.png";
import usgsLogo from "../../assets/logos/usgs.png";
import { FOOTER_DEVELOPERS, FOOTER_PARTNERS_LABEL } from "../../lib/copy";

const partnerLogos = [
  { label: "Colby College", src: colbyLogo, href: "https://www.colby.edu/" },
  { label: "7 Lakes Alliance", src: lakesLogo, href: "https://7lakesalliance.org/" },
  { label: "Sponsored by USGS funding", src: usgsLogo, href: "https://www.usgs.gov/" },
];

export function AppFooter() {
  return (
    <footer className="border-t border-lake-border bg-white">
      <div className="mx-auto max-w-[1600px] px-6 py-8 lg:px-8">
        <div className="grid gap-7 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-center">
          <div className="max-w-3xl">
            <p className="text-sm font-semibold uppercase tracking-wide text-lake-accent">
              {FOOTER_PARTNERS_LABEL}
            </p>
            <p className="mt-2 text-base leading-7 text-slate-700">{FOOTER_DEVELOPERS}</p>
          </div>
          <div
            className="grid grid-cols-1 gap-3 sm:grid-cols-3 lg:min-w-[520px]"
            aria-label="Project partners"
          >
            {partnerLogos.map((logo) => (
              <a
                key={logo.label}
                href={logo.href}
                target="_blank"
                rel="noreferrer"
                className="group flex h-16 items-center justify-center rounded-lg border border-lake-border bg-slate-50 px-4 transition hover:-translate-y-0.5 hover:border-lake-accent hover:bg-white hover:shadow-panel focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-lake-accent"
                aria-label={`Visit ${logo.label} website`}
              >
                <img
                  src={logo.src}
                  alt={logo.label}
                  className="max-h-11 max-w-[155px] object-contain transition group-hover:scale-[1.02]"
                  loading="lazy"
                  decoding="async"
                />
              </a>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
}

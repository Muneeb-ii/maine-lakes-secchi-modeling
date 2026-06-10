import colbyLogo from "../../assets/logos/colbyseal.png";
import lakesLogo from "../../assets/logos/7lakesalliance.png";
import usgsLogo from "../../assets/logos/usgs.png";
import { FOOTER_LINKS } from "../../lib/infoPagesCopy";
import { ROUTES, navigateTo } from "../../lib/routes";

const partnerLogos = [
  { label: "Colby College", src: colbyLogo, href: "https://www.colby.edu/" },
  { label: "7 Lakes Alliance", src: lakesLogo, href: "https://7lakesalliance.org/" },
  { label: "Sponsored by USGS funding", src: usgsLogo, href: "https://www.usgs.gov/" },
];

const footerLinks = [
  { label: FOOTER_LINKS.contributors, path: ROUTES.contributors },
  { label: FOOTER_LINKS.modeling, path: ROUTES.modeling },
];

function FooterNavLink({ path, children }) {
  return (
    <a
      href={path}
      onClick={(event) => {
        event.preventDefault();
        navigateTo(path);
      }}
      className="text-base font-semibold text-lake-accent transition hover:text-blue-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-lake-accent"
    >
      {children}
    </a>
  );
}

export function AppFooter() {
  return (
    <footer className="footer-accent-divider bg-white">
      <div className="mx-auto max-w-[1600px] px-4 py-6 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div
            className="grid grid-cols-1 gap-3 sm:grid-cols-3 sm:gap-4 lg:min-w-[520px]"
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

          <nav
            aria-label="Footer"
            className="flex flex-wrap items-center justify-center gap-4 sm:gap-6 lg:justify-end"
          >
            {footerLinks.map((link) => (
              <FooterNavLink key={link.path} path={link.path}>
                {link.label}
              </FooterNavLink>
            ))}
          </nav>
        </div>
      </div>
    </footer>
  );
}

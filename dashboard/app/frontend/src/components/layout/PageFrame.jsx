import { AppFooter } from "./AppFooter";

export function PageFrame({ children, footerAddon = null }) {
  return (
    <div className="dashboard-bg flex min-h-screen flex-col text-slate-900">
    <main className="flex-1">{children}</main>
      {footerAddon}
      <AppFooter />
    </div>
  );
}

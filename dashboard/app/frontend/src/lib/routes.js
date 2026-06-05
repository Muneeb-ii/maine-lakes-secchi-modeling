export const ROUTES = {
  landing: "/",
  playground: "/playground",
  trends: "/trends",
};

export function navigateTo(path) {
  window.history.pushState({}, "", path);
  window.dispatchEvent(new Event("popstate"));
}

export const ROUTES = {
  landing: "/",
  playground: "/playground",
  trends: "/trends",
  contributors: "/contributors",
  modeling: "/modeling-process",
};

export function navigateTo(path) {
  window.history.pushState({}, "", path);
  window.dispatchEvent(new Event("popstate"));
}

import { useEffect, useState } from "react";

export function navigate(path: string): void {
  if (location.pathname + location.search === path) return;
  history.pushState({}, "", path);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

export function usePath(): string {
  const [path, setPath] = useState(() => location.pathname);
  useEffect(() => {
    const on = () => setPath(location.pathname);
    window.addEventListener("popstate", on);
    return () => window.removeEventListener("popstate", on);
  }, []);
  return path;
}

export type Route =
  | { name: "login" }
  | { name: "home" }
  | { name: "lesson"; id: string }
  | { name: "summary"; id: string }
  | { name: "notfound" };

export function matchRoute(path: string): Route {
  if (path === "/" || path === "") return { name: "home" };
  if (path === "/login") return { name: "login" };
  const lesson = path.match(/^\/lesson\/([0-9a-f-]{36})$/);
  if (lesson) return { name: "lesson", id: lesson[1] };
  const summary = path.match(/^\/summary\/([0-9a-f-]{36})$/);
  if (summary) return { name: "summary", id: summary[1] };
  return { name: "notfound" };
}

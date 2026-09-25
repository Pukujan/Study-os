import { useEffect, useState } from "react";
import { api, ApiError, type Me } from "./api";
import { matchRoute, navigate, usePath } from "./router";
import { tracker } from "./tracker";
import Login from "./pages/Login";
import HomeLanes from "./pages/HomeLanes";
import Lesson from "./pages/Lesson";
import Summary from "./pages/Summary";
import TryPage from "./pages/Try";
import Player from "./pages/Player";
import AdminFeedback from "./pages/AdminFeedback";

export default function App() {
  const path = usePath();
  const route = matchRoute(path);
  const [me, setMe] = useState<Me | null>(null);
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    api
      .me()
      .then(setMe)
      .catch((e) => {
        if (!(e instanceof ApiError && e.status === 401)) console.error(e);
      })
      .finally(() => setChecked(true));
  }, []);

  useEffect(() => {
    tracker.pageView(path.replace(/[0-9a-f-]{36}/g, "id"));
  }, [path]);

  useEffect(() => {
    if (checked && !me) {
      const publicRoute = route.name === "home" || route.name === "try";
      if (!publicRoute && route.name !== "login") navigate("/login");
    }
  }, [checked, me, route.name]);

  if (!checked) return <main className="shell"><p className="muted">Loading…</p></main>;

  const logout = async () => {
    await api.logout().catch(() => undefined);
    setMe(null);
    navigate("/login");
  };

  const isGuest = !!me && (me.role === "guest" || me.handle.startsWith("guest-"));

  return (
    <div className="app">
      <header className="top">
        <a href="/" onClick={(e) => { e.preventDefault(); navigate("/"); }} className="brand" data-track="nav.home">Study OS</a>
        {me ? (
          <span className="who">
            {isGuest ? (
              <button className="link" onClick={() => navigate("/")} data-track="nav.claim">Save progress</button>
            ) : (
              <>
                {me.display_name || me.handle}
                <button className="link" onClick={logout} data-track="nav.logout">Sign out</button>
              </>
            )}
          </span>
        ) : (
          <span className="who">
            <button className="link" onClick={() => navigate("/login")} data-track="nav.signin">Sign in</button>
          </span>
        )}
      </header>
      <main className="shell">
        {route.name === "login" && <Login onSignedIn={(m) => { setMe(m); navigate("/"); }} />}
        {me && route.name === "home" && <HomeLanes me={me} />}
        {me && route.name === "try" && <TryPage onSignedIn={(m) => { setMe(m); navigate("/"); }} />}
        {!me && (route.name === "home" || route.name === "try") && <TryPage onSignedIn={(m) => { setMe(m); navigate("/"); }} />}
        {me && route.name === "play" && <Player sessionId={route.id} />}
        {me && route.name === "admin_feedback" && <AdminFeedback me={me} />}
        {me && route.name === "lesson" && <Lesson sessionId={route.id} />}
        {me && route.name === "summary" && <Summary sessionId={route.id} />}
        {route.name === "notfound" && <p>Page not found. <a href="/">Go home</a></p>}
      </main>
    </div>
  );
}

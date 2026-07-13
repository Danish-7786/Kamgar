import { NavLink, Outlet } from "react-router-dom";

// Shell shared by every page: top nav + routed content area.
export function AppLayout() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <h1 className="app-title">KaamGar</h1>
        <nav className="app-nav">
          <NavLink to="/jobs">Jobs</NavLink>
          <NavLink to="/scraper">Scraper</NavLink>
        </nav>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}

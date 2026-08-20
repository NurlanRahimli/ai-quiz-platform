import { useState } from "react";
import { Outlet } from "react-router-dom";
import { Menu } from "lucide-react";

import Sidebar from "./Sidebar";

import "../../styles/components/layout/AppLayout.css";

export default function AppLayout() {
  const [isNavigationOpen, setIsNavigationOpen] = useState(false);

  return (
    <div className="app-layout">
      <Sidebar
        isOpen={isNavigationOpen}
        onClose={() => setIsNavigationOpen(false)}
      />

      <div
        className={`app-layout__overlay ${
          isNavigationOpen ? "app-layout__overlay--visible" : ""
        }`}
        onClick={() => setIsNavigationOpen(false)}
        aria-hidden="true"
      />

      <header className="app-layout__mobile-header">
        <div className="app-layout__mobile-brand">
          <div className="app-layout__mobile-logo" aria-hidden="true">
            Q
          </div>

          <span>QuizApp</span>
        </div>

        <button
          type="button"
          className="app-layout__menu-button"
          onClick={() => setIsNavigationOpen(true)}
          aria-label="Open navigation"
          aria-expanded={isNavigationOpen}
        >
          <Menu size={22} strokeWidth={2} aria-hidden="true" />
        </button>
      </header>

      <main className="app-layout__main">
        <div className="app-layout__content">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
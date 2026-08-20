import { useState } from "react";
import { Menu, X } from "lucide-react";
import Sidebar from "./Sidebar";
import "../../styles/components/layout/AppShell.css";

type AppShellProps = {
  children: React.ReactNode;
};

export default function AppShell({ children }: AppShellProps) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  return (
    <div className="app-shell">
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
      />

      {isSidebarOpen && (
        <button
          type="button"
          className="app-shell__backdrop"
          aria-label="Close navigation"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      <div className="app-shell__workspace">
        <header className="app-shell__mobile-header">
          <div className="app-shell__mobile-brand">
            <div
              className="app-shell__mobile-logo"
              aria-hidden="true"
            >
              Q
            </div>

            <span>QuizApp</span>
          </div>

          <button
            type="button"
            className="app-shell__menu-button"
            aria-label={
              isSidebarOpen ? "Close navigation" : "Open navigation"
            }
            aria-expanded={isSidebarOpen}
            onClick={() =>
              setIsSidebarOpen((current) => !current)
            }
          >
            {isSidebarOpen ? (
              <X size={22} strokeWidth={2} />
            ) : (
              <Menu size={22} strokeWidth={2} />
            )}
          </button>
        </header>

        <main className="app-shell__content">
          {children}
        </main>
      </div>
    </div>
  );
}
import {
  LayoutDashboard,
  LogOut,
  Plus,
  Compass,
  History,
  ScrollText,
} from "lucide-react";
import { NavLink, useNavigate } from "react-router-dom";

import { useAuth } from "../../auth/useAuth";

import ThemeToggle from "../ui/ThemeToggle";

import "../../styles/components/layout/Sidebar.css";

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function Sidebar({
  isOpen,
  onClose,
}: SidebarProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    onClose();
    logout();
    navigate("/login", { replace: true });
  };

  const initial =
    user?.display_name?.trim().charAt(0).toUpperCase() || "U";

  return (
    <aside
      className={`app-sidebar ${isOpen ? "app-sidebar--open" : ""
        }`}
    >
      <div className="app-sidebar__brand">
        <div className="app-sidebar__logo" aria-hidden="true">
          Q
        </div>

        <span className="app-sidebar__brand-name">QuizApp</span>
      </div>

      <nav className="app-sidebar__navigation">
        <div className="app-sidebar__section">
          <span className="app-sidebar__section-label">Main</span>

          <NavLink
            to="/dashboard"
            onClick={onClose}
            className={({ isActive }) =>
              `app-sidebar__link ${isActive ? "app-sidebar__link--active" : ""
              }`
            }
          >
            <LayoutDashboard
              className="app-sidebar__link-icon"
              size={19}
              strokeWidth={1.9}
              aria-hidden="true"
            />
            Dashboard
          </NavLink>

          <NavLink
            to="/discover"
            onClick={onClose}
            className={({ isActive }) =>
              `app-sidebar__link ${isActive ? "app-sidebar__link--active" : ""
              }`
            }
          >
            <Compass
              className="app-sidebar__link-icon"
              size={19}
              strokeWidth={1.9}
              aria-hidden="true"
            />
            Discover Quizzes
          </NavLink>

          <NavLink
            to="/attempts"
            onClick={onClose}
            className={({ isActive }) =>
              `app-sidebar__link ${isActive ? "app-sidebar__link--active" : ""
              }`
            }
          >
            <History
              className="app-sidebar__link-icon"
              size={19}
              strokeWidth={1.9}
              aria-hidden="true"
            />
            My Attempts
          </NavLink>

          <NavLink
            to="/quizzes/new"
            onClick={onClose}
            className={({ isActive }) =>
              `app-sidebar__link ${isActive ? "app-sidebar__link--active" : ""
              }`
            }
          >
            <Plus
              className="app-sidebar__link-icon"
              size={19}
              strokeWidth={2}
              aria-hidden="true"
            />
            Create Quiz
          </NavLink>
          <NavLink
            to="/audit-log"
            onClick={onClose}
            className={({ isActive }) =>
              `app-sidebar__link ${isActive ? "app-sidebar__link--active" : ""
              }`
            }
          >
            <ScrollText
              className="app-sidebar__link-icon"
              size={19}
              strokeWidth={1.9}
              aria-hidden="true"
            />
            Audit Log
          </NavLink>
        </div>
      </nav>

      <div className="app-sidebar__footer">
        <div className="app-sidebar__theme">
          <ThemeToggle />
        </div>
        <button
          type="button"
          className="app-sidebar__user"
          onClick={() => {
            navigate("/profile")
            onClose()
          }}
          aria-label="Open profile"
        >
          <div className="app-sidebar__avatar" aria-hidden="true">
            {initial}
          </div>

          <div className="app-sidebar__user-info">
            <span className="app-sidebar__user-name">
              {user?.display_name ?? "User"}
            </span>

            <span className="app-sidebar__user-email">
              {user?.email}
            </span>
          </div>
        </button>

        <button
          type="button"
          className="app-sidebar__logout"
          onClick={handleLogout}
        >
          <LogOut size={18} strokeWidth={1.9} aria-hidden="true" />
          Logout
        </button>
      </div>
    </aside>
  );
}
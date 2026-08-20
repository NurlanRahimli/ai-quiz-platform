import { Monitor, Moon, Sun } from "lucide-react";

import {
  type ThemePreference,
} from "../../theme/theme-context";
import { useTheme } from "../../theme/useTheme";

import "../../styles/components/ui/ThemeToggle.css";

const options: {
  value: ThemePreference;
  label: string;
  icon: typeof Sun;
}[] = [
  {
    value: "light",
    label: "Light",
    icon: Sun,
  },
  {
    value: "dark",
    label: "Dark",
    icon: Moon,
  },
  {
    value: "system",
    label: "System",
    icon: Monitor,
  },
];

export default function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  return (
    <div
      className="theme-toggle"
      role="group"
      aria-label="Color theme"
    >
      {options.map((option) => {
        const Icon = option.icon;
        const isActive = theme === option.value;

        return (
          <button
            key={option.value}
            type="button"
            className={`theme-toggle__option ${
              isActive ? "theme-toggle__option--active" : ""
            }`}
            onClick={() => setTheme(option.value)}
            aria-pressed={isActive}
            title={option.label}
          >
            <Icon
              size={16}
              strokeWidth={1.9}
              aria-hidden="true"
            />

            <span>{option.label}</span>
          </button>
        );
      })}
    </div>
  );
}
import React from "react";
import { Moon, Sun } from "lucide-react";

export type AppTheme = "dark" | "light";

interface ThemeToggleProps {
  theme: AppTheme;
  onToggle: () => void;
}

export const ThemeToggle: React.FC<ThemeToggleProps> = ({ theme, onToggle }) => {
  const nextTheme = theme === "dark" ? "light" : "dark";
  const Icon = theme === "dark" ? Sun : Moon;

  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={onToggle}
      aria-label={`Switch to ${nextTheme} mode`}
      title={`Switch to ${nextTheme} mode`}
      aria-pressed={theme === "light"}
    >
      <Icon size={16} aria-hidden="true" />
      <span>{nextTheme === "light" ? "Light mode" : "Dark mode"}</span>
    </button>
  );
};

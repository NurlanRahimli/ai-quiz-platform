import {
  Atom,
  BookOpen,
  Brain,
  BriefcaseBusiness,
  Calculator,
  Code2,
  Cpu,
  FileQuestion,
  FlaskConical,
  Globe2,
  Languages,
  Landmark,
  Lightbulb,
  Map,
  Microscope,
  Percent,
  Puzzle,
  ScrollText,
  Sigma,
  Terminal,
  type LucideIcon,
} from "lucide-react";

const QUIZ_ICONS: Record<string, LucideIcon> = {
  "file-question": FileQuestion,
  "code-2": Code2,
  terminal: Terminal,
  cpu: Cpu,
  calculator: Calculator,
  sigma: Sigma,
  percent: Percent,
  atom: Atom,
  "flask-conical": FlaskConical,
  microscope: Microscope,
  landmark: Landmark,
  "scroll-text": ScrollText,
  "globe-2": Globe2,
  map: Map,
  languages: Languages,
  "book-open": BookOpen,
  "briefcase-business": BriefcaseBusiness,
  brain: Brain,
  puzzle: Puzzle,
  lightbulb: Lightbulb,
};

type QuizIconProps = {
  name?: string | null;
  size?: number;
  strokeWidth?: number;
  className?: string;
};

export default function QuizIcon({
  name,
  size = 22,
  strokeWidth = 2,
  className,
}: QuizIconProps) {
  const Icon = (name && QUIZ_ICONS[name]) || FileQuestion;

  return (
    <Icon
      size={size}
      strokeWidth={strokeWidth}
      className={className}
      aria-hidden="true"
    />
  );
}

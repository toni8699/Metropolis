import BodyCard from "@/shared/components/BodyCard";

const MAX_WIDTH = {
  "3xl": "max-w-3xl",
  "6xl": "max-w-6xl",
  "7xl": "max-w-7xl",
  full: "max-w-full",
};

export default function PageShell({
  children,
  maxWidth = "full",
  card = false,
  className = "",
}) {
  const widthClass = MAX_WIDTH[maxWidth] || MAX_WIDTH.full;
  const shellClass = `mx-auto w-full ${widthClass} ${className}`.trim();

  if (card) {
    return <BodyCard className={shellClass}>{children}</BodyCard>;
  }

  return <div className={shellClass}>{children}</div>;
}

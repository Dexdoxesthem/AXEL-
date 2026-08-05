interface RibbonCardProps {
  title: React.ReactNode;
  tint?: "olive" | "sage" | "salmon" | "peach" | "lime" | "sky" | "steel" | "periwinkle";
  children: React.ReactNode;
  className?: string;
}

export default function RibbonCard({
  title,
  tint = "sage",
  children,
  className = "",
}: RibbonCardProps) {
  return (
    <section className={`ribbon ${className}`}>
      <header className="ribbon__title">
        <span>{title}</span>
      </header>
      <div className={`ribbon__body ribbon__body--${tint}`}>{children}</div>
    </section>
  );
}

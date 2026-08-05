interface EyebrowProps {
  children: React.ReactNode;
  tint?: "olive" | "sage" | "salmon" | "peach" | "lime" | "sky" | "steel" | "periwinkle";
  small?: boolean;
}

export default function Eyebrow({ children, tint = "olive", small }: EyebrowProps) {
  return (
    <h2 className={`eyebrow eyebrow--${tint}${small ? " eyebrow--sm" : ""}`}>
      {children}
    </h2>
  );
}

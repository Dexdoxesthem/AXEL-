interface NewBurstProps {
  label?: string;
  className?: string;
}

export default function NewBurst({ label = "NEW!", className = "" }: NewBurstProps) {
  return <span className={`sticker sticker--new ${className}`}>{label}</span>;
}

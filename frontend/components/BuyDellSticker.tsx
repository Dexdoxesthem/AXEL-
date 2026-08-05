interface BuyDellStickerProps {
  href: string;
  label: string;
  sub?: string;
}

export default function BuyDellSticker({ href, label, sub }: BuyDellStickerProps) {
  return (
    <a className="sticker sticker--buy" href={href} style={{ position: "static" }}>
      {label}
    </a>
  );
}

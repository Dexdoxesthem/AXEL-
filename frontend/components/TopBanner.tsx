import BuyDellSticker from "./BuyDellSticker";

interface TopBannerProps {
  sub?: string;
  action?: { href: string; label: string };
  phone?: string;
}

export default function TopBanner({
  sub = "NAAC COLLEGE — SEMESTER ANALYTICS SYSTEM",
  action,
  phone = "1-800-1996-AXEL",
}: TopBannerProps) {
  return (
    <div className="top-banner">
      <div>
        <p className="banner-title">AXEL. Student Performance. Online.</p>
        <p className="banner-sub">{sub}</p>
      </div>
      <div className="banner-right">
        {action && (
          <BuyDellSticker href={action.href} label={action.label} />
        )}
        <span className="phone-callout">{phone}</span>
      </div>
    </div>
  );
}

interface CertSealProps {
  className?: string;
}

export default function CertSeal({ className = "" }: CertSealProps) {
  return (
    <div className={`cert-seal ${className}`}>
      <span className="seal-ax">AXEL</span>
      <span>1996</span>
      <span>SEAL</span>
    </div>
  );
}

interface PageFrameProps {
  children: React.ReactNode;
}

export default function PageFrame({ children }: PageFrameProps) {
  return <div className="page-frame">{children}</div>;
}

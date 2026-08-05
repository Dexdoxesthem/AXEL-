import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AXEL — Student Performance System",
  description:
    "NAAC student performance dashboard: GPA analytics, at-risk detection, study groups and recommendations.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

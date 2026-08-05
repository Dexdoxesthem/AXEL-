import PageFrame from "@/components/PageFrame";
import TopBanner from "@/components/TopBanner";
import CertSeal from "@/components/CertSeal";
import RibbonCard from "@/components/RibbonCard";
import LoginForm from "@/components/LoginForm";

export default function LoginPage() {
  return (
    <PageFrame>
      <TopBanner sub="RESTRICTED ACCESS — AUTHORIZED USERS ONLY" />
      <div className="page-body">
        <div className="auth-card" style={{ position: "relative" }}>
          <CertSeal className="seal--corner" />
          <RibbonCard title="System Login" tint="sky">
            <div style={{ marginBottom: 14 }}>
              <p style={{ margin: 0 }}>
                This is the AXEL Student Performance System. Enter the system
                password to view the class dashboard, analytics and reports.
              </p>
              <p className="muted" style={{ margin: "8px 0 0" }}>
                Default: <code>axel123</code> (overridable via the{" "}
                <code>AXEL_PASSWORD</code> environment variable).
              </p>
            </div>
            <LoginForm />
          </RibbonCard>
        </div>
      </div>
    </PageFrame>
  );
}

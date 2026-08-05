import PageFrame from "@/components/PageFrame";
import TopBanner from "@/components/TopBanner";
import Eyebrow from "@/components/Eyebrow";
import RibbonCard from "@/components/RibbonCard";
import FooterBand from "@/components/FooterBand";
import {
  GpaHistogram,
  AttendanceHistogram,
  SubjectAverages,
  RiskDonut,
} from "@/components/AnalyticsCharts";
import { readData } from "@/lib/data";

export default function AnalyticsPage() {
  const data = readData();
  const slim = data.students.map((s) => ({
    gpa: s.gpa,
    attendance: s.attendance,
  }));
  const subjects = data.subject_difficulty.map((s) => ({
    subject: s.subject,
    mean: s.mean,
    std: s.std,
  }));
  const m = data.metrics;

  return (
    <PageFrame>
      <TopBanner
        sub={`COHORT ANALYTICS — ${m.students} STUDENTS · CLUSTERS K=${m.cluster_k}`}
        action={{ href: "/", label: "BUY a STUDENT" }}
      />

      <div className="page-body">
        <p>
          <a href="/">&larr; Back to home</a> · <a href="/compare">Compare</a>
        </p>

        <Eyebrow tint="olive" small>
          Headline numbers
        </Eyebrow>
        <div className="cols--3">
          <RibbonCard title="Students" tint="steel">
            <div style={{ textAlign: "center", padding: "6px 0" }}>
              <div style={{ fontFamily: "var(--font-display)", fontWeight: 900, fontSize: 34 }}>
                {m.students}
              </div>
            </div>
          </RibbonCard>
          <RibbonCard title="At risk" tint="salmon">
            <div style={{ textAlign: "center", padding: "6px 0" }}>
              <div style={{ fontFamily: "var(--font-display)", fontWeight: 900, fontSize: 34 }}>
                {m.at_risk_count}
              </div>
              <div className="caps muted" style={{ marginTop: 4 }}>
                {Math.round((m.at_risk_count / m.students) * 100)}% of class
              </div>
            </div>
          </RibbonCard>
          <RibbonCard title="Risk model accuracy" tint="sky">
            <div style={{ textAlign: "center", padding: "6px 0" }}>
              <div style={{ fontFamily: "var(--font-display)", fontWeight: 900, fontSize: 34 }}>
                {m.risk_accuracy ?? "—"}
              </div>
              <div className="caps muted" style={{ marginTop: 4 }}>
                &plusmn;{m.risk_accuracy_std ?? "—"}
              </div>
            </div>
          </RibbonCard>
        </div>

        <Eyebrow tint="sky" small>
          Risk split
        </Eyebrow>
        <RibbonCard title="At-risk vs on track" tint="steel">
          <RiskDonut atRisk={m.at_risk_count} onTrack={m.on_track_count} />
        </RibbonCard>

        <div className="cols">
          <div>
            <Eyebrow tint="salmon" small>
              GPA distribution
            </Eyebrow>
            <RibbonCard title="Overall GPA, 0.5-point bins" tint="sage">
              <GpaHistogram students={slim} />
            </RibbonCard>
          </div>
          <div>
            <Eyebrow tint="lime" small>
              Attendance distribution
            </Eyebrow>
            <RibbonCard title="Attendance, 10-point bins" tint="steel">
              <AttendanceHistogram students={slim} />
            </RibbonCard>
          </div>
        </div>

        <Eyebrow tint="olive" small>
          Subject difficulty
        </Eyebrow>
        <RibbonCard title="Class mean +- std by subject" tint="periwinkle">
          <SubjectAverages subjects={subjects} />
        </RibbonCard>
      </div>

      <FooterBand />
    </PageFrame>
  );
}

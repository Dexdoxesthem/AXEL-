import PageFrame from "@/components/PageFrame";
import TopBanner from "@/components/TopBanner";
import Eyebrow from "@/components/Eyebrow";
import FooterBand from "@/components/FooterBand";
import ComparePanel, { type ComparableStudent } from "@/components/ComparePanel";
import { readData } from "@/lib/data";

export default function ComparePage() {
  const data = readData();
  const students: ComparableStudent[] = data.students.map((s) => ({
    id: s.id,
    name: s.name,
    gpa_sem1: s.gpa_sem1,
    gpa_sem2: s.gpa_sem2,
    predicted_gpa: s.predicted_gpa,
    gpa: s.gpa,
    at_risk: s.at_risk,
  }));

  return (
    <PageFrame>
      <TopBanner
        sub="COMPARE STUDENTS SIDE BY SIDE"
        action={{ href: "/analytics", label: "BUY a CHART" }}
      />

      <div className="page-body">
        <p>
          <a href="/">&larr; Back to home</a> · <a href="/analytics">Analytics</a>
        </p>

        <Eyebrow tint="olive" small>
          Compare students
        </Eyebrow>
        <ComparePanel students={students} />
      </div>

      <FooterBand />
    </PageFrame>
  );
}

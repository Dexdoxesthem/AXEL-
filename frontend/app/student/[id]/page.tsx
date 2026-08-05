import { notFound } from "next/navigation";
import PageFrame from "@/components/PageFrame";
import TopBanner from "@/components/TopBanner";
import Eyebrow from "@/components/Eyebrow";
import RibbonCard from "@/components/RibbonCard";
import NewBurst from "@/components/NewBurst";
import FooterBand from "@/components/FooterBand";
import GpaTrendChart from "@/components/GpaTrendChart";
import { readData, findStudent } from "@/lib/data";

interface Props {
  params: { id: string };
}

export function generateStaticParams() {
  const data = readData();
  return data.students.map((s) => ({ id: String(s.id) }));
}

export default function StudentPage({ params }: Props) {
  const data = readData();
  const student = findStudent(data, Number(params.id));

  if (!student) notFound();

  const gpaPct = Math.round((student.gpa / 10) * 100);
  const delta = student.gpa_delta;

  return (
    <PageFrame>
      <TopBanner
        sub={`STUDENT ${student.id} — ${student.name.toUpperCase()} · GROUP ${student.group}`}
        action={{ href: `/student/${student.id}/report`, label: "BUY a REPORT" }}
      />

      <div className="page-body">
        <p>
          <a href="/">&larr; Back to home</a> ·{" "}
          <a href="/analytics">Analytics</a> ·{" "}
          <a href="/compare">Compare</a>
        </p>

        <div style={{ position: "relative", marginTop: 4 }}>
          {student.improving && (
            <NewBurst label="IMPROVING!" className="atrisk-burst" />
          )}
          <Eyebrow tint="salmon">
            Student {student.id} — {student.name}
          </Eyebrow>
        </div>

        <div className="cols--3">
          <RibbonCard title="Overall GPA" tint="steel">
            <div style={{ textAlign: "center", padding: "6px 0" }}>
              <div
                style={{
                  fontFamily: "var(--font-display)",
                  fontWeight: 900,
                  fontSize: 42,
                  lineHeight: 1,
                }}
              >
                {student.gpa.toFixed(2)}
              </div>
              <div className="caps muted" style={{ marginTop: 6 }}>
                / 10 · {gpaPct}% of scale
              </div>
            </div>
          </RibbonCard>

          <RibbonCard title="Attendance" tint="sage">
            <div style={{ textAlign: "center", padding: "6px 0" }}>
              <div
                style={{
                  fontFamily: "var(--font-display)",
                  fontWeight: 900,
                  fontSize: 42,
                  lineHeight: 1,
                }}
              >
                {student.attendance.toFixed(1)}%
              </div>
              <div className="caps muted" style={{ marginTop: 6 }}>
                {student.attendance_delta > 0 ? "+" : ""}
                {student.attendance_delta.toFixed(1)} pts vs sem 1
              </div>
            </div>
          </RibbonCard>

          <RibbonCard title="Predicted next GPA" tint="periwinkle">
            <div style={{ textAlign: "center", padding: "6px 0" }}>
              <div
                style={{
                  fontFamily: "var(--font-display)",
                  fontWeight: 900,
                  fontSize: 42,
                  lineHeight: 1,
                  color: "var(--primary)",
                }}
              >
                {student.predicted_gpa.toFixed(2)}
              </div>
              <div className="caps muted" style={{ marginTop: 6 }}>
                model: {data.metrics.best_model}
              </div>
            </div>
          </RibbonCard>
        </div>

        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", margin: "2px 0 14px" }}>
          {student.at_risk ? (
            <span className="sticker sticker--atrisk" style={{ position: "static" }}>
              At risk
            </span>
          ) : (
            <span className="sticker sticker--ontrack" style={{ position: "static" }}>
              On track
            </span>
          )}
          <span className="chip chip--sky">Study group {student.group}</span>
          <span className="chip chip--yellow">
            Trend {delta > 0 ? "+" : ""}
            {delta.toFixed(2)}
          </span>
        </div>

        <Eyebrow tint="olive" small>
          GPA trend
        </Eyebrow>
        <RibbonCard title="Semester-by-semester GPA" tint="sky">
          <GpaTrendChart
            sem1={student.gpa_sem1}
            sem2={student.gpa_sem2}
            predicted={student.predicted_gpa}
          />
        </RibbonCard>

        <div className="cols">
          <RibbonCard title="Recommended books" tint="lime">
            <ol style={{ margin: 0, paddingLeft: 20 }}>
              {student.recommended_books.map((b) => (
                <li key={b}>{b}</li>
              ))}
            </ol>
          </RibbonCard>

          <RibbonCard title="Weakest subjects" tint="steel">
            {student.weakest_subjects.length ? (
              <ol style={{ margin: 0, paddingLeft: 20 }}>
                {student.weakest_subjects.map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ol>
            ) : (
              <p style={{ margin: 0 }}>No weak subjects detected.</p>
            )}
          </RibbonCard>

          <RibbonCard title="Professor recommendations" tint="peach">
            {student.professors.length ? (
              <ul style={{ margin: 0, paddingLeft: 18 }}>
                {student.professors.map((p) => (
                  <li key={p}>{p}</li>
                ))}
              </ul>
            ) : (
              <p style={{ margin: 0 }}>No professor referrals needed.</p>
            )}
          </RibbonCard>

          <RibbonCard title="Study group" tint="periwinkle">
            {student.study_group.length ? (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Student</th>
                    <th>GPA</th>
                  </tr>
                </thead>
                <tbody>
                  {student.study_group.map((member) => (
                    <tr key={member.id}>
                      <td>{member.id}</td>
                      <td>
                        <a href={`/student/${member.id}`}>{member.name}</a>
                      </td>
                      <td>{member.gpa.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p style={{ margin: 0 }}>No group members found.</p>
            )}
          </RibbonCard>
        </div>

        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 4 }}>
          <a
            className="btn btn--primary"
            href={`/api/export?student=${student.id}`}
          >
            Download CSV record
          </a>
          <a className="btn btn--secondary" href="/compare">
            Compare with classmates
          </a>
        </div>
      </div>

      <FooterBand />
    </PageFrame>
  );
}

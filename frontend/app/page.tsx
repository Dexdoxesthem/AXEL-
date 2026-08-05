import PageFrame from "@/components/PageFrame";
import TopBanner from "@/components/TopBanner";
import Eyebrow from "@/components/Eyebrow";
import RibbonCard from "@/components/RibbonCard";
import CertSeal from "@/components/CertSeal";
import NewBurst from "@/components/NewBurst";
import FooterBand from "@/components/FooterBand";
import StudentLookup, { type LookupStudent } from "@/components/StudentLookup";
import { readData, atRiskSorted, topPerformers } from "@/lib/data";

export default function HomePage() {
  const data = readData();
  const lookup: LookupStudent[] = data.students.map((s) => ({
    id: s.id,
    name: s.name,
    gpa: s.gpa,
    at_risk: s.at_risk,
  }));
  const risk = atRiskSorted(data, 8);
  const top = topPerformers(data, 8);
  const m = data.metrics;

  return (
    <PageFrame>
      <TopBanner
        action={{ href: "/compare", label: "BUY a COMPARISON" }}
        sub={`${m.students} STUDENTS · GPA MODEL ${String(m.best_model).toUpperCase()} · RISK ACC ${m.risk_accuracy ?? "—"}`}
      />

      <div className="page-body">
        <div className="cols--rail">
          {/* ---------------- left rail ---------------- */}
          <div style={{ position: "relative" }}>
            <CertSeal className="seal--corner" />
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <a className="icon-link" href="/">
                <span className="icon-box">H</span> Home
              </a>
              <a className="icon-link" href="/analytics">
                <span className="icon-box icon-box--peach">A</span> Analytics
              </a>
              <a className="icon-link" href="/compare">
                <span className="icon-box icon-box--lime">C</span> Compare
              </a>
              <a className="icon-link" href="#at-risk">
                <span className="icon-box icon-box--sky">!</span> At-risk
              </a>
            </div>

            <div className="cta-red" style={{ marginTop: 14 }}>
              <h3>At AXEL.com, we help you find the right student. Fast.</h3>
              <p style={{ margin: "0 0 10px" }}>
                One search finds GPA, attendance, predicted performance, study
                group, recommended books and professors.
              </p>
              <a className="btn btn--secondary" href="/analytics">
                Explore analytics
              </a>
            </div>

            <RibbonCard title="Class pulse" tint="lime" className="bevel">
              <ul style={{ margin: 0, paddingLeft: 18 }}>
                <li>
                  <strong>{m.at_risk_count}</strong> students at risk
                  ({Math.round((m.at_risk_count / m.students) * 100)}%)
                </li>
                <li>
                  <strong>{m.on_track_count}</strong> students on track
                </li>
                <li>
                  Prediction model: <strong>{m.best_model}</strong> (R&sup2;{" "}
                  {m.gpa_r2 ?? "—"})
                </li>
                <li>
                  Risk classifier accuracy:{" "}
                  <strong>{m.risk_accuracy ?? "—"}</strong>
                </li>
              </ul>
            </RibbonCard>
          </div>

          {/* ---------------- main column ---------------- */}
          <div>
            <Eyebrow tint="olive">Student lookup</Eyebrow>
            <RibbonCard title="Find a system — er, student" tint="sky">
              <StudentLookup students={lookup} />
            </RibbonCard>

            <div id="at-risk" style={{ position: "relative", marginTop: 4 }}>
              <NewBurst label="NEW! at-risk list" className="atrisk-burst" />
              <Eyebrow tint="salmon" small>
                At-risk students
              </Eyebrow>
              <RibbonCard title="Lowest GPA, most in need" tint="sage">
                <ul style={{ margin: 0, padding: 0, listStyle: "none" }}>
                  {risk.map((s, i) => (
                    <li
                      key={s.id}
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        gap: 8,
                        padding: "5px 0",
                        borderBottom: i < risk.length - 1 ? "1px dashed var(--ink)" : "none",
                      }}
                    >
                      <a href={`/student/${s.id}`}>
                        <strong>{s.name}</strong>{" "}
                        <span className="muted">ID {s.id}</span>
                      </a>
                      <span>
                        <span className="chip chip--red">GPA {s.gpa.toFixed(2)}</span>{" "}
                        <span className="chip chip--sky">att {s.attendance.toFixed(0)}%</span>
                      </span>
                    </li>
                  ))}
                </ul>
              </RibbonCard>
            </div>

            <Eyebrow tint="periwinkle" small>
              Top performers
            </Eyebrow>
            <RibbonCard title="Honor roll — 10.0 GPA scale" tint="sky">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Student</th>
                    <th>GPA</th>
                    <th>Attendance</th>
                    <th>Trend</th>
                  </tr>
                </thead>
                <tbody>
                  {top.map((s, i) => (
                    <tr key={s.id}>
                      <td>{i + 1}</td>
                      <td>
                        <a href={`/student/${s.id}`}>
                          {s.name}
                        </a>{" "}
                        <span className="muted">ID {s.id}</span>
                      </td>
                      <td>{s.gpa.toFixed(2)}</td>
                      <td>{s.attendance.toFixed(1)}%</td>
                      <td>
                        {s.gpa_delta > 0 ? (
                          <span className="chip chip--lime">
                            +{s.gpa_delta.toFixed(2)}
                          </span>
                        ) : (
                          <span className="chip chip--yellow">
                            {s.gpa_delta.toFixed(2)}
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </RibbonCard>
          </div>
        </div>
      </div>

      <FooterBand />
    </PageFrame>
  );
}

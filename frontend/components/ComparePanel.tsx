"use client";

import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import RibbonCard from "@/components/RibbonCard";

export interface ComparableStudent {
  id: number;
  name: string;
  gpa_sem1: number;
  gpa_sem2: number;
  predicted_gpa: number;
  gpa: number;
  at_risk: boolean;
}

interface ComparePanelProps {
  students: ComparableStudent[];
}

const tooltipStyle = {
  borderRadius: 0,
  border: "1px solid #000",
  fontFamily: "Times New Roman, serif",
  fontSize: 13,
};

export default function ComparePanel({ students }: ComparePanelProps) {
  const [selected, setSelected] = useState<number[]>([
    students[0]?.id,
    students[1]?.id,
  ].filter((v): v is number => v != null));

  const chosen = useMemo(
    () => students.filter((s) => selected.includes(s.id)),
    [students, selected]
  );

  const chartData = chosen.map((s) => ({
    name: `${s.name} (${s.id})`,
    "Sem 1": s.gpa_sem1,
    "Sem 2": s.gpa_sem2,
    "Predicted": s.predicted_gpa,
  }));

  function toggle(id: number) {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  }

  return (
    <div>
      <RibbonCard title="Choose students to compare" tint="sage">
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
            gap: 6,
            maxHeight: 260,
            overflowY: "auto",
          }}
        >
          {students.map((s) => (
            <label
              key={s.id}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                border: "1px solid var(--ink)",
                background: selected.includes(s.id) ? "var(--tint-lime)" : "#fff",
                padding: "5px 7px",
                cursor: "pointer",
                fontSize: 13,
              }}
            >
              <input
                type="checkbox"
                checked={selected.includes(s.id)}
                onChange={() => toggle(s.id)}
              />
              <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {s.name} <span className="muted">({s.id})</span>
              </span>
            </label>
          ))}
        </div>
      </RibbonCard>

      {chosen.length > 0 && (
        <>
          <RibbonCard title="Side-by-side GPA comparison" tint="sky">
            <div className="chart-frame bevel" style={{ height: 320 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 12, right: 16, left: -18, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="2 2" stroke="#000" />
                  <XAxis
                    dataKey="name"
                    stroke="#000"
                    tickLine={false}
                    interval={0}
                    angle={-20}
                    textAnchor="end"
                    height={80}
                    tick={{ fontSize: 11 }}
                  />
                  <YAxis domain={[0, 10]} stroke="#000" tickLine={false} />
                  <Tooltip cursor={{ fill: "rgba(0,0,0,0.06)" }} contentStyle={tooltipStyle} />
                  <Legend />
                  <Bar dataKey="Sem 1" fill="#9ab6c8" />
                  <Bar dataKey="Sem 2" fill="#8c9ae0" />
                  <Bar dataKey="Predicted" fill="#e91d2a" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </RibbonCard>

          <RibbonCard title="Comparison table" tint="periwinkle">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Student</th>
                  <th>GPA sem 1</th>
                  <th>GPA sem 2</th>
                  <th>Overall</th>
                  <th>Predicted</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {chosen.map((s) => (
                  <tr key={s.id}>
                    <td>
                      <a href={`/student/${s.id}`}>{s.name}</a>{" "}
                      <span className="muted">({s.id})</span>
                    </td>
                    <td>{s.gpa_sem1.toFixed(2)}</td>
                    <td>{s.gpa_sem2.toFixed(2)}</td>
                    <td>
                      <strong>{s.gpa.toFixed(2)}</strong>
                    </td>
                    <td>{s.predicted_gpa.toFixed(2)}</td>
                    <td>
                      {s.at_risk ? (
                        <span className="chip chip--red">At risk</span>
                      ) : (
                        <span className="chip chip--lime">On track</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </RibbonCard>
        </>
      )}
    </div>
  );
}

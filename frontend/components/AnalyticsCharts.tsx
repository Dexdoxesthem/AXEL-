"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  ErrorBar,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const TINTS = [
  "#9ab6c8",
  "#b3bd95",
  "#d77a7a",
  "#e6915d",
  "#c0d4a7",
  "#a5b8c0",
  "#8c9ae0",
  "#8e8a25",
];

function bins(values: number[], min: number, max: number, step: number) {
  const out: { label: string; count: number }[] = [];
  for (let lo = min; lo < max; lo += step) {
    const hi = lo + step;
    out.push({
      label: step >= 1 ? String(lo) : lo.toFixed(1),
      count: values.filter((v) => v >= lo && v < hi).length,
    });
  }
  return out;
}

const tooltipStyle = {
  borderRadius: 0,
  border: "1px solid #000",
  fontFamily: "Times New Roman, serif",
  fontSize: 13,
};

interface SlimStudent {
  gpa: number;
  attendance: number;
}

export function GpaHistogram({ students }: { students: SlimStudent[] }) {
  const data = bins(students.map((s) => s.gpa), 0, 10, 0.5);
  return (
    <div className="chart-frame bevel" style={{ height: 260 }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 12, left: -18, bottom: 0 }}>
          <CartesianGrid strokeDasharray="2 2" stroke="#000" />
          <XAxis dataKey="label" stroke="#000" tickLine={false} interval={1} />
          <YAxis stroke="#000" tickLine={false} />
          <Tooltip cursor={{ fill: "rgba(0,0,0,0.06)" }} contentStyle={tooltipStyle} />
          <Bar dataKey="count" name="Students">
            {data.map((_, i) => (
              <Cell key={i} fill={TINTS[i % TINTS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function AttendanceHistogram({ students }: { students: SlimStudent[] }) {
  const data = bins(students.map((s) => s.attendance), 0, 100, 10);
  return (
    <div className="chart-frame bevel" style={{ height: 260 }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 12, left: -18, bottom: 0 }}>
          <CartesianGrid strokeDasharray="2 2" stroke="#000" />
          <XAxis dataKey="label" stroke="#000" tickLine={false} />
          <YAxis stroke="#000" tickLine={false} />
          <Tooltip cursor={{ fill: "rgba(0,0,0,0.06)" }} contentStyle={tooltipStyle} />
          <Bar dataKey="count" name="Students">
            {data.map((_, i) => (
              <Cell key={i} fill={TINTS[(i + 2) % TINTS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export interface SubjectRow {
  subject: string;
  mean: number;
  std: number;
}

export function SubjectAverages({ subjects }: { subjects: SubjectRow[] }) {
  const data = subjects.map((s) => ({
    subject: s.subject,
    mean: s.mean,
    error: s.std,
  }));
  return (
    <div className="chart-frame bevel" style={{ height: 320 }}>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data} margin={{ top: 12, right: 16, left: -18, bottom: 8 }}>
          <CartesianGrid strokeDasharray="2 2" stroke="#000" />
          <XAxis
            dataKey="subject"
            stroke="#000"
            tickLine={false}
            interval={0}
            angle={-30}
            textAnchor="end"
            height={80}
            tick={{ fontSize: 11 }}
          />
          <YAxis domain={[0, 10]} stroke="#000" tickLine={false} />
          <Tooltip cursor={{ fill: "rgba(0,0,0,0.06)" }} contentStyle={tooltipStyle} />
          <Bar dataKey="mean" name="Class mean" fill="#8c9ae0" />
          <ErrorBar dataKey="error" direction="y" width={4} stroke="#000" />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

export function RiskDonut({
  atRisk,
  onTrack,
}: {
  atRisk: number;
  onTrack: number;
}) {
  const data = [
    { name: "At risk", value: atRisk },
    { name: "On track", value: onTrack },
  ];
  return (
    <div className="chart-frame bevel" style={{ height: 240 }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            innerRadius={55}
            outerRadius={85}
            paddingAngle={2}
          >
            <Cell fill="#e91d2a" />
            <Cell fill="#b3bd95" />
          </Pie>
          <Tooltip contentStyle={tooltipStyle} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

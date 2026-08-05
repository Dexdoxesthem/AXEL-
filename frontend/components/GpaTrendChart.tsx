"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface GpaTrendChartProps {
  sem1: number;
  sem2: number;
  predicted: number;
}

export default function GpaTrendChart({ sem1, sem2, predicted }: GpaTrendChartProps) {
  const data = [
    { label: "Sem 1", value: sem1 },
    { label: "Sem 2", value: sem2 },
    { label: "Predicted", value: predicted },
  ];

  return (
    <div className="chart-frame bevel" style={{ height: 220 }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 12, left: -18, bottom: 0 }}>
          <CartesianGrid strokeDasharray="2 2" stroke="#000" />
          <XAxis dataKey="label" stroke="#000" tickLine={false} />
          <YAxis domain={[0, 10]} stroke="#000" tickLine={false} />
          <Tooltip
            cursor={{ fill: "rgba(0,0,0,0.06)" }}
            contentStyle={{
              borderRadius: 0,
              border: "1px solid #000",
              fontFamily: "Times New Roman, serif",
            }}
          />
          <Bar dataKey="value" name="GPA">
            {data.map((d, i) => (
              <Cell key={i} fill={i === 2 ? "var(--primary)" : "var(--tint-sky)"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

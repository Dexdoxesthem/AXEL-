"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";

export interface LookupStudent {
  id: number;
  name: string;
  gpa: number;
  at_risk: boolean;
}

interface StudentLookupProps {
  students: LookupStudent[];
}

export default function StudentLookup({ students }: StudentLookupProps) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<number | null>(null);

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return [];
    return students
      .filter(
        (s) =>
          s.name.toLowerCase().includes(q) || String(s.id).includes(q)
      )
      .slice(0, 10);
  }, [query, students]);

  function go() {
    const target =
      selected ??
      (results.length === 1 ? results[0].id : results[0]?.id);
    if (target != null) router.push(`/student/${target}`);
  }

  return (
    <div>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <input
          className="text-input"
          style={{ flex: 1, minWidth: 220 }}
          placeholder="type a student name or ID (try: ram kumar)"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setSelected(null);
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              go();
            }
          }}
        />
        <button className="btn btn--primary" type="button" onClick={go}>
          View dashboard
        </button>
      </div>

      {results.length > 0 && (
        <ul
          style={{
            listStyle: "none",
            margin: "10px 0 0",
            padding: 0,
            border: "1px solid var(--ink)",
            background: "#fff",
          }}
        >
          {results.map((s) => (
            <li key={s.id} style={{ borderBottom: "1px solid var(--ink)" }}>
              <button
                type="button"
                onClick={() => {
                  setSelected(s.id);
                  router.push(`/student/${s.id}`);
                }}
                style={{
                  width: "100%",
                  textAlign: "left",
                  background: selected === s.id ? "var(--tint-lime)" : "transparent",
                  border: "none",
                  padding: "7px 10px",
                  fontFamily: "inherit",
                  fontSize: 14,
                  cursor: "pointer",
                  display: "flex",
                  justifyContent: "space-between",
                  gap: 8,
                }}
              >
                <span>
                  <strong>{s.name}</strong>
                  <span className="muted"> &mdash; ID {s.id}</span>
                </span>
                <span>
                  <span className="chip chip--sky">GPA {s.gpa.toFixed(2)}</span>{" "}
                  {s.at_risk && <span className="chip chip--red">RISK</span>}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}

      <p className="muted" style={{ margin: "10px 0 0" }}>
        {students.length.toLocaleString()} students enrolled. Search or press{" "}
        <strong>Enter</strong> to open the top match.
      </p>
    </div>
  );
}

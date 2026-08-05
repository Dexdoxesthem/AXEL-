import { NextResponse } from "next/server";
import { readData } from "@/lib/data";

export async function GET(req: Request) {
  const url = new URL(req.url);
  const id = Number(url.searchParams.get("student"));

  const data = readData();
  const student = data.students.find((s) => s.id === id);

  if (!student) {
    return new NextResponse("Student not found", { status: 404 });
  }

  const rows = [
    ["student id", String(student.id)],
    ["student name", student.name],
    ["GPA sem 1", student.gpa_sem1.toFixed(2)],
    ["GPA sem 2", student.gpa_sem2.toFixed(2)],
    ["GPA overall", student.gpa.toFixed(2)],
    ["Predicted GPA", student.predicted_gpa.toFixed(2)],
    ["Attendance (%)", student.attendance.toFixed(1)],
    ["GPA delta", student.gpa_delta.toFixed(2)],
    ["Attendance delta", student.attendance_delta.toFixed(1)],
    ["Improving", student.improving ? "true" : "false"],
    ["At risk", student.at_risk ? "true" : "false"],
    ["Study group", String(student.group)],
    ["Recommended books", student.recommended_books.join("; ")],
    ["Professor recommendations", student.professors.join("; ")],
    ["Weakest subjects", student.weakest_subjects.join("; ")],
  ];

  const csv =
    rows.map((r) => `${r[0]},${`"${r[1]}"`}`).join("\r\n") + "\r\n";

  return new NextResponse(csv, {
    headers: {
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition": `attachment; filename="axel_student_${student.id}.csv"`,
    },
  });
}

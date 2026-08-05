import fs from "fs";
import path from "path";

export interface StudyGroupMember {
  id: number;
  name: string;
  gpa: number;
  attendance: number;
}

export interface Student {
  id: number;
  name: string;
  gpa_sem1: number;
  gpa_sem2: number;
  gpa: number;
  attendance: number;
  predicted_gpa: number;
  gpa_delta: number;
  attendance_delta: number;
  improving: boolean;
  at_risk: boolean;
  group: number;
  recommended_books: string[];
  professors: string[];
  weakest_subjects: string[];
  study_group: StudyGroupMember[];
}

export interface Metrics {
  students: number;
  cluster_k: number;
  prediction_features: string;
  best_model: string;
  gpa_r2: number | null;
  gpa_r2_std: number | null;
  gpa_mae: number | null;
  gpa_mae_std: number | null;
  risk_accuracy: number | null;
  risk_accuracy_std: number | null;
  at_risk_count: number;
  on_track_count: number;
}

export interface SubjectDifficulty {
  subject: string;
  semester: string;
  mean: number;
  std: number;
  min: number;
  max: number;
}

export interface EngineeredData {
  generated_by: string;
  metrics: Metrics;
  students: Student[];
  subject_difficulty: SubjectDifficulty[];
}

const DATA_PATH = path.join(process.cwd(), "data", "engineered.json");

export function readData(): EngineeredData {
  const raw = fs.readFileSync(DATA_PATH, "utf-8");
  return JSON.parse(raw) as EngineeredData;
}

export function findStudent(
  data: EngineeredData,
  id: number
): Student | undefined {
  return data.students.find((s) => s.id === id);
}

export function searchStudents(data: EngineeredData, query: string): Student[] {
  const q = query.trim().toLowerCase();
  if (!q) return [];
  return data.students
    .filter(
      (s) =>
        s.name.toLowerCase().includes(q) || String(s.id).includes(q)
    )
    .slice(0, 12);
}

export function atRiskSorted(data: EngineeredData, limit = 10): Student[] {
  return data.students
    .filter((s) => s.at_risk)
    .sort((a, b) => a.gpa - b.gpa)
    .slice(0, limit);
}

export function topPerformers(data: EngineeredData, limit = 10): Student[] {
  return data.students
    .sort((a, b) => b.gpa - a.gpa)
    .slice(0, limit);
}

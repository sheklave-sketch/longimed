const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

export interface Doctor {
  id: number;
  full_name: string;
  specialty: string;
  bio: string | null;
  is_available: boolean;
  rating_avg: number;
  rating_count: number;
  languages: string[];
  license_number?: string;
}

export interface Question {
  id: number;
  category: string;
  text: string;
  is_anonymous: boolean;
  status: string;
  answer_text: string | null;
  created_at: string;
  answered_at: string | null;
}

export interface PlatformStats {
  total_users: number;
  total_doctors: number;
  total_questions: number;
  total_sessions: number;
  pending_doctors: number;
  pending_questions: number;
}

export interface DoctorDashboardStats {
  total_sessions: number;
  active_sessions: number;
  pending_queue: number;
  rating_avg: number;
  rating_count: number;
  pending_earnings: number;
  paid_earnings: number;
}

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    cache: "no-store",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`);
  return res.json();
}

export async function fetchDoctors(): Promise<Doctor[]> {
  return apiFetch<Doctor[]>("/api/doctors");
}

export async function fetchDoctor(id: number): Promise<Doctor> {
  return apiFetch<Doctor>(`/api/doctors/${id}`);
}

export async function fetchQuestions(limit = 20, offset = 0): Promise<Question[]> {
  return apiFetch<Question[]>(`/api/questions?limit=${limit}&offset=${offset}`);
}

export async function fetchPlatformStats(): Promise<PlatformStats> {
  return apiFetch<PlatformStats>("/api/admin/stats");
}

export async function fetchDoctorDashboard(telegramId: number): Promise<DoctorDashboardStats> {
  return apiFetch<DoctorDashboardStats>(`/api/doctors/dashboard/${telegramId}`);
}

// Next.js rewrites proxy /api/* to VPS — no direct URL needed in browser
const API_BASE = "";

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

export interface QuestionDetail extends Question {
  follow_ups: Array<{
    id: number;
    text: string;
    is_anonymous: boolean;
    status: string;
    created_at: string;
  }>;
  answered_by_name: string | null;
}

export interface SessionItem {
  id: number;
  status: string;
  package: string;
  session_mode: string;
  issue_description: string;
  is_anonymous: boolean;
  doctor_name: string | null;
  patient_name: string | null;
  created_at: string;
  started_at: string | null;
  ended_at: string | null;
  rating: number | null;
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

async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
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

export async function fetchQuestionDetail(id: number): Promise<QuestionDetail> {
  return apiFetch<QuestionDetail>(`/api/questions/${id}`);
}

export async function fetchPlatformStats(): Promise<PlatformStats> {
  return apiFetch<PlatformStats>("/api/admin/stats");
}

export async function fetchDoctorDashboard(telegramId: number): Promise<DoctorDashboardStats> {
  return apiFetch<DoctorDashboardStats>(`/api/doctors/dashboard/${telegramId}`);
}

export async function submitQuestion(data: {
  telegram_id: number;
  category: string;
  text: string;
  is_anonymous: boolean;
}): Promise<Question> {
  return apiPost<Question>("/api/questions", data);
}

export async function submitFollowUp(
  questionId: number,
  data: { telegram_id: number; text: string; is_anonymous: boolean }
): Promise<{ id: number; text: string; status: string }> {
  return apiPost("/api/questions/" + questionId + "/follow-ups", data);
}

export async function bookSession(data: {
  telegram_id: number;
  package: string;
  specialty: string;
  doctor_id: number;
  issue_description: string;
  is_anonymous: boolean;
}): Promise<SessionItem> {
  return apiPost<SessionItem>("/api/sessions/book", data);
}

export async function fetchMySessions(telegramId: number): Promise<SessionItem[]> {
  return apiFetch<SessionItem[]>(`/api/sessions/my/${telegramId}`);
}

export async function searchQuestions(q: string): Promise<Question[]> {
  return apiFetch<Question[]>(`/api/search/questions?q=${encodeURIComponent(q)}`);
}

export async function searchDoctors(q: string): Promise<Doctor[]> {
  return apiFetch<Doctor[]>(`/api/search/doctors?q=${encodeURIComponent(q)}`);
}

export async function registerDoctor(data: {
  telegram_id: number;
  full_name: string;
  license_number: string;
  specialty: string;
  languages: string[];
  bio: string;
}): Promise<{ message: string }> {
  return apiPost("/api/doctors/register", data);
}

export async function adminRegisterDoctor(data: {
  admin_telegram_id: number;
  full_name: string;
  license_number: string;
  specialty: string;
  languages: string[];
  bio: string;
  doctor_telegram_id?: number;
  phone?: string;
  sex?: string;
  sub_specialization?: string;
}): Promise<{ id: number; status: string; is_verified: boolean }> {
  return apiPost("/api/admin/doctors/register", data);
}

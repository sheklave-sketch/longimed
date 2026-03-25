"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import StatCard from "@/components/StatCard";
import { initTelegram, getTelegramUser } from "@/lib/telegram";
import { adminRegisterDoctor } from "@/lib/api";

// Uses Next.js rewrites (next.config.js) to proxy /api/* to VPS
const API_BASE = "";
// Admin tokens — Dr. Tsegab and Moshe can access via ?token=<TOKEN>
const ADMIN_TOKENS: Record<string, number> = {
  "longimed-admin-tsegab-2026": 348870668,
  "longimed-admin-moshe-2026": 297659579,
};

const SPECIALTIES = [
  { value: "general", label: "General / GP", icon: "🩺" },
  { value: "internal_medicine", label: "Internal Medicine", icon: "💊" },
  { value: "pediatrics", label: "Pediatrics", icon: "👶" },
  { value: "obgyn", label: "OB/GYN", icon: "🤰" },
  { value: "surgery", label: "Surgery", icon: "🔪" },
  { value: "orthopedics", label: "Orthopedics", icon: "🦴" },
  { value: "dermatology", label: "Dermatology", icon: "🧴" },
  { value: "mental_health", label: "Mental Health", icon: "🧠" },
  { value: "cardiology", label: "Cardiology", icon: "❤️" },
  { value: "neurology", label: "Neurology", icon: "🧬" },
  { value: "ent", label: "ENT", icon: "👂" },
  { value: "ophthalmology", label: "Ophthalmology", icon: "👁️" },
  { value: "other", label: "Other", icon: "➕" },
];

interface AdminData {
  stats: { total_users: number; total_doctors: number; total_questions: number; total_sessions: number; pending_doctors: number; pending_questions: number };
  pending_doctors: Array<{ id: number; full_name: string; specialty: string; license_number: string; applied_at: string }>;
  recent_payments: Array<{ id: number; amount_etb: number; status: string; created_at: string; user_telegram_id: number }>;
}

export default function AdminPanel() {
  const [data, setData] = useState<AdminData | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [adminTgId, setAdminTgId] = useState(0);

  // Add doctor form state
  const [docName, setDocName] = useState("");
  const [docLicense, setDocLicense] = useState("");
  const [docSpecialty, setDocSpecialty] = useState("");
  const [docLangs, setDocLangs] = useState<string[]>(["en"]);
  const [docBio, setDocBio] = useState("");
  const [docTgId, setDocTgId] = useState("");
  const [docPhone, setDocPhone] = useState("");
  const [docSex, setDocSex] = useState("");
  const [docSubSpec, setDocSubSpec] = useState("");
  const [docPhoto, setDocPhoto] = useState<File | null>(null);
  const [docPhotoPreview, setDocPhotoPreview] = useState("");
  const [docLicenseFile, setDocLicenseFile] = useState<File | null>(null);
  const [docLicenseFileName, setDocLicenseFileName] = useState("");
  const [addLoading, setAddLoading] = useState(false);
  const [addSuccess, setAddSuccess] = useState(false);
  const [signupLink, setSignupLink] = useState("");
  const [addError, setAddError] = useState("");

  useEffect(() => {
    initTelegram();

    // Try: 1) Telegram user, 2) URL token, 3) URL admin_id param
    let tgId = getTelegramUser()?.id || 0;

    if (!tgId && typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const token = params.get("token");
      const adminId = params.get("admin_id");
      if (token && ADMIN_TOKENS[token]) {
        tgId = ADMIN_TOKENS[token];
      } else if (adminId && !isNaN(Number(adminId))) {
        tgId = Number(adminId);
      }
    }

    setAdminTgId(tgId);
    if (!tgId) { setLoading(false); return; }

    fetch(`${API_BASE}/api/admin/dashboard/${tgId}`)
      .then((r) => { if (!r.ok) throw new Error(); return r.json(); })
      .then(setData).catch(() => setData(null)).finally(() => setLoading(false));
  }, []);

  const handleAction = async (id: number, action: "approve" | "reject") => {
    setActionLoading(id);
    try {
      const res = await fetch(`${API_BASE}/api/admin/doctors/${id}/${action}`, { method: "POST" });
      if (res.ok) setData((p) => p ? {
        ...p, pending_doctors: p.pending_doctors.filter((d) => d.id !== id),
        stats: { ...p.stats, pending_doctors: p.stats.pending_doctors - 1, total_doctors: action === "approve" ? p.stats.total_doctors + 1 : p.stats.total_doctors },
      } : null);
    } catch {} finally { setActionLoading(null); }
  };

  const uploadFile = async (file: File): Promise<string> => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch("/api/upload", { method: "POST", body: formData });
    if (!res.ok) throw new Error("Upload failed");
    const data = await res.json();
    return data.url;
  };

  const handlePhotoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setDocPhoto(file);
      setDocPhotoPreview(URL.createObjectURL(file));
    }
  };

  const handleLicenseChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setDocLicenseFile(file);
      setDocLicenseFileName(file.name);
    }
  };

  const handleAddDoctor = async () => {
    if (!docName.trim() || !docLicense.trim() || !docSpecialty) {
      setAddError("Name, license number, and specialty are required.");
      return;
    }
    setAddLoading(true);
    setAddError("");
    try {
      // Upload files first if provided
      let profilePhotoUrl: string | undefined;
      let licenseDocUrl: string | undefined;

      if (docPhoto) {
        profilePhotoUrl = await uploadFile(docPhoto);
      }
      if (docLicenseFile) {
        licenseDocUrl = await uploadFile(docLicenseFile);
      }

      const result = await adminRegisterDoctor({
        admin_telegram_id: adminTgId,
        full_name: docName.trim(),
        license_number: docLicense.trim(),
        specialty: docSpecialty,
        languages: docLangs,
        bio: docBio.trim(),
        doctor_telegram_id: docTgId ? parseInt(docTgId) : undefined,
        phone: docPhone || undefined,
        sex: docSex || undefined,
        sub_specialization: docSubSpec.trim() || undefined,
        profile_photo_url: profilePhotoUrl,
        license_document_url: licenseDocUrl,
      });
      setAddSuccess(true);
      if (result.signup_link) {
        setSignupLink(result.signup_link);
      }
      // Update stats
      if (data) {
        setData({ ...data, stats: { ...data.stats, total_doctors: data.stats.total_doctors + 1 } });
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to register doctor";
      setAddError(msg.includes("409") ? "License or Telegram ID already registered." : msg);
    } finally {
      setAddLoading(false);
    }
  };

  const toggleLang = (lang: string) => {
    setDocLangs((prev) => prev.includes(lang) ? prev.filter((l) => l !== lang) : [...prev, lang]);
  };

  if (loading) return (
    <div className="pt-6 space-y-3">
      {[1, 2, 3, 4].map((i) => <div key={i} className="card p-4 h-20"><div className="skeleton h-full rounded-lg" /></div>)}
    </div>
  );

  if (!data) {
    return (
      <div className="pt-10 px-6 text-center">
        <h2 className="font-display font-bold text-[20px] text-ink-rich mb-2">Admin Panel</h2>
        <p className="text-ink-secondary text-[14px] mb-4">
          {adminTgId ? `Could not load dashboard for TG ID ${adminTgId}. The API may be unreachable.` : "No admin credentials detected. Open from Telegram or use a token link."}
        </p>
        <p className="text-ink-muted text-[12px] mb-4">API: {API_BASE || "(not set)"}</p>
        <a href="/" className="text-brand-teal font-semibold text-[14px]">← Back to Home</a>
      </div>
    );
  }

  const { stats, pending_doctors, recent_payments } = data;

  return (
    <div className="pt-5 pb-8">
      {/* Header */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mb-5">
        <p className="text-[12px] font-semibold text-ink-muted uppercase tracking-[0.1em] mb-1">Admin</p>
        <h1 className="font-display font-bold text-[24px] text-ink-rich tracking-tight">Platform Overview</h1>
      </motion.div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3 mb-5">
        <StatCard label="Users" value={stats.total_users} icon="👥" accent="teal" index={0} />
        <StatCard label="Doctors" value={stats.total_doctors} icon="👨‍⚕️" accent="blue" index={1} />
        <StatCard label="Questions" value={stats.total_questions} icon="❓" accent="gold" index={2} />
        <StatCard label="Sessions" value={stats.total_sessions} icon="🩺" accent="rose" index={3} />
      </div>

      {/* Pending alert */}
      {(stats.pending_doctors > 0 || stats.pending_questions > 0) && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
          className="card p-4 mb-5 border-l-[3px] border-l-brand-gold"
        >
          <p className="font-display font-semibold text-ink-rich text-[13px] mb-1.5">Action Required</p>
          <div className="space-y-1">
            {stats.pending_doctors > 0 && (
              <p className="text-[12px] text-ink-body"><span className="font-bold text-brand-gold">{stats.pending_doctors}</span> doctor application{stats.pending_doctors > 1 ? "s" : ""} pending</p>
            )}
            {stats.pending_questions > 0 && (
              <p className="text-[12px] text-ink-body"><span className="font-bold text-brand-gold">{stats.pending_questions}</span> question{stats.pending_questions > 1 ? "s" : ""} awaiting review</p>
            )}
          </div>
        </motion.div>
      )}

      {/* Add Doctor Button */}
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.22 }} className="mb-5">
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="w-full py-3 rounded-2xl bg-brand-teal text-white font-display font-bold text-[14px] hover:bg-brand-teal-deep transition-colors shadow-glow"
        >
          {showAddForm ? "✕ Close Form" : "➕ Register New Doctor"}
        </button>
      </motion.div>

      {/* Add Doctor Form */}
      {showAddForm && (
        <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} className="mb-6">
          <div className="card p-5 space-y-4">
            <h2 className="font-display font-semibold text-ink-rich text-[15px]">Register Doctor (Auto-Verified)</h2>

            {addSuccess ? (
              <div className="py-4 text-center">
                <div className="text-3xl mb-2">✅</div>
                <p className="font-display font-semibold text-ink-rich text-[14px] mb-3">Doctor registered successfully!</p>

                {signupLink ? (
                  <div className="text-left bg-surface-muted rounded-xl p-4 mb-3">
                    <p className="text-[11px] font-semibold text-ink-muted uppercase tracking-[0.08em] mb-2">Send this link to the doctor</p>
                    <p className="text-[12px] text-ink-secondary mb-2">They tap it to connect their Telegram account:</p>
                    <div className="bg-surface-white rounded-lg p-3 border border-surface-border mb-3">
                      <p className="text-[12px] font-mono text-brand-teal break-all select-all">{signupLink}</p>
                    </div>
                    <button
                      onClick={() => { navigator.clipboard.writeText(signupLink); }}
                      className="w-full py-2.5 rounded-xl bg-brand-teal text-white text-[12px] font-bold hover:bg-brand-teal-deep transition-colors"
                    >📋 Copy Link</button>
                  </div>
                ) : (
                  <p className="text-[12px] text-ink-muted">Doctor already linked to Telegram — no signup link needed.</p>
                )}

                <button onClick={() => { setShowAddForm(false); setAddSuccess(false); setSignupLink(""); setDocName(""); setDocLicense(""); setDocSpecialty(""); setDocLangs(["en"]); setDocBio(""); setDocTgId(""); setDocPhone(""); setDocSex(""); setDocSubSpec(""); setDocPhoto(null); setDocPhotoPreview(""); setDocLicenseFile(null); setDocLicenseFileName(""); }}
                  className="mt-2 text-[13px] text-brand-teal font-semibold"
                >Register Another Doctor</button>
              </div>
            ) : (
              <>
                <div>
                  <label className="text-[11px] font-semibold text-ink-muted uppercase tracking-[0.08em] mb-1.5 block">Full Name *</label>
                  <input type="text" value={docName} onChange={(e) => setDocName(e.target.value)} placeholder="Dr. Full Name"
                    className="w-full bg-surface-white border border-surface-border rounded-xl px-3.5 py-2.5 text-[13px] text-ink-rich placeholder:text-ink-faint focus:outline-none focus:border-brand-teal transition-all" />
                </div>

                <div>
                  <label className="text-[11px] font-semibold text-ink-muted uppercase tracking-[0.08em] mb-1.5 block">License Number *</label>
                  <input type="text" value={docLicense} onChange={(e) => setDocLicense(e.target.value)} placeholder="FMHACA-12345"
                    className="w-full bg-surface-white border border-surface-border rounded-xl px-3.5 py-2.5 text-[13px] text-ink-rich placeholder:text-ink-faint focus:outline-none focus:border-brand-teal transition-all" />
                </div>

                <div>
                  <label className="text-[11px] font-semibold text-ink-muted uppercase tracking-[0.08em] mb-1.5 block">Specialty *</label>
                  <div className="grid grid-cols-2 gap-1.5">
                    {SPECIALTIES.map((spec) => (
                      <button key={spec.value} onClick={() => setDocSpecialty(spec.value)}
                        className={`py-2 px-3 rounded-xl text-[12px] font-semibold text-left transition-all ${
                          docSpecialty === spec.value ? "bg-brand-teal text-white" : "bg-surface-muted text-ink-body hover:bg-surface-border"
                        }`}
                      >{spec.icon} {spec.label}</button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="text-[11px] font-semibold text-ink-muted uppercase tracking-[0.08em] mb-1.5 block">Languages</label>
                  <div className="flex gap-2">
                    {[{ v: "en", l: "English" }, { v: "am", l: "Amharic" }].map(({ v, l }) => (
                      <button key={v} onClick={() => toggleLang(v)}
                        className={`flex-1 py-2 rounded-xl text-[12px] font-semibold transition-all ${
                          docLangs.includes(v) ? "bg-brand-teal text-white" : "bg-surface-muted text-ink-body"
                        }`}
                      >{l}</button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="text-[11px] font-semibold text-ink-muted uppercase tracking-[0.08em] mb-1.5 block">Sex</label>
                  <div className="flex gap-2">
                    {[{ v: "male", l: "👨 Male" }, { v: "female", l: "👩 Female" }].map(({ v, l }) => (
                      <button key={v} onClick={() => setDocSex(v)}
                        className={`flex-1 py-2 rounded-xl text-[12px] font-semibold transition-all ${
                          docSex === v ? "bg-brand-teal text-white" : "bg-surface-muted text-ink-body"
                        }`}
                      >{l}</button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="text-[11px] font-semibold text-ink-muted uppercase tracking-[0.08em] mb-1.5 block">Sub-Specialization</label>
                  <input type="text" value={docSubSpec} onChange={(e) => setDocSubSpec(e.target.value)} placeholder="e.g., Pediatric Cardiology, Trauma Surgery"
                    className="w-full bg-surface-white border border-surface-border rounded-xl px-3.5 py-2.5 text-[13px] text-ink-rich placeholder:text-ink-faint focus:outline-none focus:border-brand-teal transition-all" />
                </div>

                <div>
                  <label className="text-[11px] font-semibold text-ink-muted uppercase tracking-[0.08em] mb-1.5 block">Bio / Description</label>
                  <textarea value={docBio} onChange={(e) => setDocBio(e.target.value)} placeholder="Brief bio..." rows={2}
                    className="w-full bg-surface-white border border-surface-border rounded-xl px-3.5 py-2.5 text-[13px] text-ink-rich placeholder:text-ink-faint focus:outline-none focus:border-brand-teal transition-all resize-none" />
                </div>

                {/* Photo Upload */}
                <div>
                  <label className="text-[11px] font-semibold text-ink-muted uppercase tracking-[0.08em] mb-1.5 block">Profile Photo</label>
                  <div className="flex items-center gap-3">
                    {docPhotoPreview ? (
                      <img src={docPhotoPreview} alt="Preview" className="w-16 h-16 rounded-xl object-cover border border-surface-border" />
                    ) : (
                      <div className="w-16 h-16 rounded-xl bg-surface-muted flex items-center justify-center text-[24px]">📷</div>
                    )}
                    <label className="flex-1 py-2.5 rounded-xl bg-surface-muted text-ink-body text-[12px] font-semibold text-center cursor-pointer hover:bg-surface-border transition-all">
                      {docPhoto ? "Change Photo" : "Upload Photo"}
                      <input type="file" accept="image/*" onChange={handlePhotoChange} className="hidden" />
                    </label>
                  </div>
                </div>

                {/* License Upload */}
                <div>
                  <label className="text-[11px] font-semibold text-ink-muted uppercase tracking-[0.08em] mb-1.5 block">License Document</label>
                  <label className="flex items-center gap-3 py-3 px-4 rounded-xl bg-surface-muted cursor-pointer hover:bg-surface-border transition-all">
                    <span className="text-[18px]">📄</span>
                    <span className="text-[12px] font-semibold text-ink-body flex-1">
                      {docLicenseFileName || "Upload license (photo or PDF)"}
                    </span>
                    <input type="file" accept="image/*,.pdf" onChange={handleLicenseChange} className="hidden" />
                  </label>
                </div>

                <div className="pt-2 border-t border-surface-border">
                  <p className="text-[11px] font-semibold text-ink-muted uppercase tracking-[0.08em] mb-2">Optional — Telegram & Phone</p>
                  <div className="space-y-3">
                    <div>
                      <label className="text-[11px] text-ink-secondary mb-1 block">Doctor&apos;s Telegram ID</label>
                      <input type="text" value={docTgId} onChange={(e) => setDocTgId(e.target.value)} placeholder="e.g., 348870668"
                        className="w-full bg-surface-white border border-surface-border rounded-xl px-3.5 py-2.5 text-[13px] text-ink-rich placeholder:text-ink-faint focus:outline-none focus:border-brand-teal transition-all" />
                      <p className="text-[10px] text-ink-muted mt-1">If provided, the doctor will be notified on Telegram</p>
                    </div>
                    <div>
                      <label className="text-[11px] text-ink-secondary mb-1 block">Phone Number</label>
                      <input type="text" value={docPhone} onChange={(e) => setDocPhone(e.target.value)} placeholder="+251..."
                        className="w-full bg-surface-white border border-surface-border rounded-xl px-3.5 py-2.5 text-[13px] text-ink-rich placeholder:text-ink-faint focus:outline-none focus:border-brand-teal transition-all" />
                    </div>
                  </div>
                </div>

                {addError && (
                  <p className="text-[12px] text-red-500 font-semibold">{addError}</p>
                )}

                <button onClick={handleAddDoctor} disabled={addLoading || !docName.trim() || !docLicense.trim() || !docSpecialty}
                  className="w-full py-3 rounded-xl bg-brand-teal text-white font-display font-bold text-[14px] hover:bg-brand-teal-deep transition-colors disabled:opacity-50"
                >{addLoading ? "Registering..." : "Register & Verify Doctor"}</button>
              </>
            )}
          </div>
        </motion.div>
      )}

      {/* Doctor applications */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }} className="mb-6">
        <h2 className="font-display font-semibold text-ink-rich text-[14px] mb-3">Doctor Applications</h2>
        {pending_doctors.length > 0 ? (
          <div className="space-y-3">
            {pending_doctors.map((doc) => (
              <div key={doc.id} className="card p-4">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-gradient-teal-soft flex items-center justify-center font-display font-bold text-brand-teal-deep text-[14px]">
                      {doc.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2)}
                    </div>
                    <div>
                      <p className="font-display font-semibold text-ink-rich text-[14px]">Dr. {doc.full_name}</p>
                      <p className="text-[11px] text-ink-secondary">{doc.specialty.replace("_", " ")} · <span className="font-mono">{doc.license_number}</span></p>
                    </div>
                  </div>
                  <span className="text-[10px] text-ink-muted bg-surface-muted px-2 py-0.5 rounded-md">{doc.applied_at ? new Date(doc.applied_at).toLocaleDateString() : "—"}</span>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => handleAction(doc.id, "approve")} disabled={actionLoading === doc.id}
                    className="flex-1 py-2.5 rounded-xl bg-brand-teal text-white text-[12px] font-bold hover:bg-brand-teal-deep transition-colors disabled:opacity-50 shadow-glow-sm"
                  >Approve</button>
                  <button onClick={() => handleAction(doc.id, "reject")} disabled={actionLoading === doc.id}
                    className="flex-1 py-2.5 rounded-xl bg-surface-muted text-ink-secondary text-[12px] font-bold hover:bg-red-50 hover:text-red-600 transition-colors disabled:opacity-50"
                  >Reject</button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="card p-8 text-center"><p className="text-ink-muted text-[13px]">No pending applications</p></div>
        )}
      </motion.div>

      {/* Payments */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
        <h2 className="font-display font-semibold text-ink-rich text-[14px] mb-3">Recent Payments</h2>
        {recent_payments.length > 0 ? (
          <div className="space-y-2">
            {recent_payments.map((p) => {
              const sc: Record<string, string> = { completed: "bg-emerald-50 text-emerald-700 border-emerald-200", pending: "bg-amber-50 text-amber-700 border-amber-200", failed: "bg-red-50 text-red-500 border-red-200" };
              return (
                <div key={p.id} className="card p-3.5 flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-surface-muted flex items-center justify-center text-[14px]">💰</div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[13px] font-semibold text-ink-rich">{p.amount_etb?.toLocaleString() || "—"} ETB</p>
                    <p className="text-[11px] text-ink-muted">{new Date(p.created_at).toLocaleDateString()}</p>
                  </div>
                  <span className={`shrink-0 px-2 py-[3px] rounded-lg border text-[10px] font-semibold ${sc[p.status] || sc.pending}`}>{p.status}</span>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="card p-8 text-center"><p className="text-ink-muted text-[13px]">No payments yet</p></div>
        )}
      </motion.div>
    </div>
  );
}

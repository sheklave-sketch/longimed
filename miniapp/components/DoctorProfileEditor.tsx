"use client";

import { useState, useEffect } from "react";

const SPECIALTIES = [
  "general", "family_medicine", "internal_medicine", "pediatrics",
  "obgyn", "surgery", "orthopedics", "dermatology", "mental_health",
  "cardiology", "neurology", "ent", "ophthalmology", "other",
];

const LANGS = ["en", "am", "or", "ti"];

export interface DoctorProfile {
  id: number;
  full_name: string;
  bio: string;
  specialty: string;
  specialties: string[];
  languages: string[];
  sex: string | null;
  sub_specialization: string;
  profile_photo_url: string | null;
}

interface Props {
  initial: DoctorProfile;
  endpoint: string;
  /** Extra body fields merged into the PATCH (e.g. admin_telegram_id). */
  extraBody?: Record<string, unknown>;
  /** Allow editing fields normally restricted to admins. */
  adminMode?: boolean;
  onSaved?: (updated: DoctorProfile) => void;
}

export default function DoctorProfileEditor({ initial, endpoint, extraBody, adminMode, onSaved }: Props) {
  const [fullName, setFullName] = useState(initial.full_name);
  const [bio, setBio] = useState(initial.bio);
  const [specialty, setSpecialty] = useState(initial.specialty);
  const [specialties, setSpecialties] = useState<string[]>(initial.specialties.length ? initial.specialties : [initial.specialty]);
  const [languages, setLanguages] = useState<string[]>(initial.languages.length ? initial.languages : ["en"]);
  const [sex, setSex] = useState(initial.sex || "");
  const [subSpec, setSubSpec] = useState(initial.sub_specialization);
  const [photoUrl, setPhotoUrl] = useState(initial.profile_photo_url || "");
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<{ kind: "ok" | "err"; text: string } | null>(null);

  useEffect(() => {
    setFullName(initial.full_name);
    setBio(initial.bio);
    setSpecialty(initial.specialty);
    setSpecialties(initial.specialties.length ? initial.specialties : [initial.specialty]);
    setLanguages(initial.languages.length ? initial.languages : ["en"]);
    setSex(initial.sex || "");
    setSubSpec(initial.sub_specialization);
    setPhotoUrl(initial.profile_photo_url || "");
  }, [initial]);

  const toggleArrayValue = (current: string[], setter: (next: string[]) => void, value: string) => {
    setter(current.includes(value) ? current.filter((v) => v !== value) : [...current, value]);
  };

  const onPhotoChange = async (file: File) => {
    setUploading(true);
    setMsg(null);
    try {
      const form = new FormData();
      form.append("file", file);
      const r = await fetch("/api/upload", { method: "POST", body: form });
      if (!r.ok) throw new Error("Upload failed");
      const data = await r.json();
      setPhotoUrl(data.url);
    } catch (e) {
      setMsg({ kind: "err", text: e instanceof Error ? e.message : "Upload failed" });
    } finally {
      setUploading(false);
    }
  };

  const save = async () => {
    setSaving(true);
    setMsg(null);
    try {
      const body: Record<string, unknown> = {
        ...(extraBody || {}),
        bio,
        sub_specialization: subSpec,
        profile_photo_url: photoUrl,
        specialty,
        specialties,
        languages,
        sex: sex || null,
      };
      if (adminMode) {
        body.full_name = fullName;
      }
      const r = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!r.ok) {
        const txt = await r.text();
        throw new Error(txt || `HTTP ${r.status}`);
      }
      setMsg({ kind: "ok", text: "Profile saved." });
      onSaved?.({
        ...initial,
        full_name: fullName,
        bio,
        specialty,
        specialties,
        languages,
        sex: sex || null,
        sub_specialization: subSpec,
        profile_photo_url: photoUrl || null,
      });
    } catch (e) {
      setMsg({ kind: "err", text: e instanceof Error ? e.message : "Save failed" });
    } finally {
      setSaving(false);
    }
  };

  const initials = (fullName || "?").split(/\s+/).map((n) => n[0]).join("").slice(0, 2).toUpperCase();

  return (
    <div className="space-y-5">
      {/* Photo */}
      <div className="flex items-center gap-4">
        {photoUrl ? (
          <img src={photoUrl} alt={fullName} className="w-16 h-16 rounded-2xl object-cover border border-surface-border" />
        ) : (
          <div className="w-16 h-16 rounded-2xl bg-brand-teal-light flex items-center justify-center font-display font-bold text-brand-teal-deep text-[18px] border border-surface-border">
            {initials}
          </div>
        )}
        <div className="flex-1 min-w-0">
          <label className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-muted text-ink-rich text-[12px] font-semibold cursor-pointer hover:bg-surface-border transition-colors">
            <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" /></svg>
            {photoUrl ? "Replace photo" : "Upload photo"}
            <input
              type="file"
              accept="image/*"
              className="hidden"
              disabled={uploading}
              onChange={(e) => { const f = e.target.files?.[0]; if (f) onPhotoChange(f); }}
            />
          </label>
          {uploading && <span className="text-[11px] text-ink-muted ml-2">Uploading…</span>}
        </div>
      </div>

      {/* Full name (admin only) */}
      {adminMode && (
        <div>
          <label className="block text-[11px] font-semibold text-ink-muted uppercase tracking-wider mb-1.5">Full name</label>
          <input
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            className="w-full px-3.5 py-2.5 rounded-xl bg-surface-white border border-surface-border text-[14px] text-ink-rich focus-ring"
          />
        </div>
      )}

      {/* Bio */}
      <div>
        <label className="block text-[11px] font-semibold text-ink-muted uppercase tracking-wider mb-1.5">Bio</label>
        <textarea
          value={bio}
          onChange={(e) => setBio(e.target.value)}
          rows={4}
          maxLength={500}
          placeholder="A few sentences patients will see — your experience, focus areas, languages they can consult in."
          className="w-full px-3.5 py-2.5 rounded-xl bg-surface-white border border-surface-border text-[14px] text-ink-rich resize-none focus-ring"
        />
        <p className="text-[10px] text-ink-muted mt-1 text-right">{bio.length}/500</p>
      </div>

      {/* Sub-specialization */}
      <div>
        <label className="block text-[11px] font-semibold text-ink-muted uppercase tracking-wider mb-1.5">Sub-specialty (optional)</label>
        <input
          type="text"
          value={subSpec}
          onChange={(e) => setSubSpec(e.target.value)}
          placeholder="e.g. Pediatric cardiology"
          className="w-full px-3.5 py-2.5 rounded-xl bg-surface-white border border-surface-border text-[14px] text-ink-rich focus-ring"
        />
      </div>

      {/* Specialty */}
      <div>
        <label className="block text-[11px] font-semibold text-ink-muted uppercase tracking-wider mb-1.5">Primary specialty</label>
        <select
          value={specialty}
          onChange={(e) => {
            const v = e.target.value;
            setSpecialty(v);
            if (!specialties.includes(v)) setSpecialties([v, ...specialties]);
          }}
          className="w-full px-3.5 py-2.5 rounded-xl bg-surface-white border border-surface-border text-[14px] text-ink-rich focus-ring"
        >
          {SPECIALTIES.map((s) => (
            <option key={s} value={s}>{s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}</option>
          ))}
        </select>
      </div>

      {/* Additional specialties */}
      <div>
        <label className="block text-[11px] font-semibold text-ink-muted uppercase tracking-wider mb-1.5">Also practices</label>
        <div className="flex flex-wrap gap-1.5">
          {SPECIALTIES.map((s) => {
            const active = specialties.includes(s);
            return (
              <button
                key={s}
                type="button"
                onClick={() => toggleArrayValue(specialties, setSpecialties, s)}
                className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold border transition-colors ${
                  active
                    ? "bg-brand-teal text-white border-brand-teal"
                    : "bg-surface-white text-ink-secondary border-surface-border hover:border-brand-teal/40"
                }`}
              >
                {s.replace(/_/g, " ")}
              </button>
            );
          })}
        </div>
      </div>

      {/* Languages */}
      <div>
        <label className="block text-[11px] font-semibold text-ink-muted uppercase tracking-wider mb-1.5">Languages</label>
        <div className="flex flex-wrap gap-1.5">
          {LANGS.map((lang) => {
            const labels: Record<string, string> = { en: "English", am: "Amharic", or: "Oromifa", ti: "Tigrinya" };
            const active = languages.includes(lang);
            return (
              <button
                key={lang}
                type="button"
                onClick={() => toggleArrayValue(languages, setLanguages, lang)}
                className={`px-3 py-1.5 rounded-lg text-[12px] font-semibold border transition-colors ${
                  active
                    ? "bg-brand-blue text-white border-brand-blue"
                    : "bg-surface-white text-ink-secondary border-surface-border hover:border-brand-blue/40"
                }`}
              >
                {labels[lang]}
              </button>
            );
          })}
        </div>
      </div>

      {/* Sex */}
      <div>
        <label className="block text-[11px] font-semibold text-ink-muted uppercase tracking-wider mb-1.5">Sex</label>
        <div className="flex gap-2">
          {[
            { v: "", l: "Prefer not to say" },
            { v: "male", l: "Male" },
            { v: "female", l: "Female" },
          ].map((opt) => (
            <button
              key={opt.v}
              type="button"
              onClick={() => setSex(opt.v)}
              className={`px-3 py-1.5 rounded-lg text-[12px] font-semibold border transition-colors ${
                sex === opt.v
                  ? "bg-ink-rich text-white border-ink-rich"
                  : "bg-surface-white text-ink-secondary border-surface-border hover:border-ink-rich/30"
              }`}
            >
              {opt.l}
            </button>
          ))}
        </div>
      </div>

      {/* Save */}
      <div className="flex items-center gap-3 pt-2">
        <button
          type="button"
          onClick={save}
          disabled={saving || uploading}
          className="px-5 py-2.5 rounded-xl bg-brand-teal text-white font-display font-bold text-[13px] shadow-glow-sm active:scale-[0.97] transition-transform disabled:opacity-60"
        >
          {saving ? "Saving…" : "Save profile"}
        </button>
        {msg && (
          <span className={`text-[12px] font-medium ${msg.kind === "ok" ? "text-emerald-600" : "text-rose-600"}`}>
            {msg.text}
          </span>
        )}
      </div>
    </div>
  );
}

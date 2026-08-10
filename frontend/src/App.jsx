import { useState, useEffect } from "react";
import "./App.css";

const API_BASE = "http://127.0.0.1:8000";

function App() {
  const [token, setToken] = useState(null);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [authStatus, setAuthStatus] = useState({ text: "", error: false });
  const [authBusy, setAuthBusy] = useState(false);

  const [jobDescription, setJobDescription] = useState("");
  const [genStatus, setGenStatus] = useState({ text: "", error: false });
  const [genBusy, setGenBusy] = useState(false);
  const [letters, setLetters] = useState([]);
  const [downloadingId, setDownloadingId] = useState(null);

  const [experiences, setExperiences] = useState([]);
  const [expTitle, setExpTitle] = useState("");
  const [expDescription, setExpDescription] = useState("");
  const [expSkills, setExpSkills] = useState("");
  const [expBusy, setExpBusy] = useState(false);
  const [deletingExpId, setDeletingExpId] = useState(null);

  async function register(e) {
    e.preventDefault();
    setAuthBusy(true);
    try {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      setAuthStatus(
        res.ok
          ? { text: "Registered — now log in.", error: false }
          : { text: "Registration failed — that username may be taken.", error: true }
      );
    } finally {
      setAuthBusy(false);
    }
  }

  async function login(e) {
    e.preventDefault();
    setAuthBusy(true);
    try {
      const form = new URLSearchParams();
      form.append("username", username);
      form.append("password", password);

      const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: form,
      });

      if (!res.ok) {
        setAuthStatus({ text: "Login failed — check your username and password.", error: true });
        return;
      }

      const data = await res.json();
      setAuthStatus({ text: "", error: false });
      setPassword("");
      setToken(data.access_token);
    } finally {
      setAuthBusy(false);
    }
  }

  function logout() {
    setToken(null);
    setUsername("");
    setPassword("");
    setLetters([]);
    setExperiences([]);
    setJobDescription("");
    setGenStatus({ text: "", error: false });
  }

  async function generate(e) {
    e.preventDefault();
    setGenBusy(true);
    setGenStatus({ text: "Generating…", error: false });
    try {
      const res = await fetch(`${API_BASE}/api/cover-letters`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ job_description: jobDescription }),
      });

      if (res.ok) {
        setJobDescription("");
        setGenStatus({ text: "Cover letter generated.", error: false });
        loadHistory();
      } else {
        const detail = await res.json().catch(() => null);
        setGenStatus({
          text: detail?.detail || "Failed to generate cover letter.",
          error: true,
        });
      }
    } finally {
      setGenBusy(false);
    }
  }

  async function downloadPdf(letterId) {
    setDownloadingId(letterId);
    try {
      const res = await fetch(`${API_BASE}/api/cover-letters/${letterId}/pdf`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        alert("Failed to download PDF");
        return;
      }

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);

      const link = document.createElement("a");
      link.href = url;
      link.download = `cover_letter_${letterId}.pdf`;
      link.click();

      window.URL.revokeObjectURL(url);
    } finally {
      setDownloadingId(null);
    }
  }

  async function loadHistory() {
    const res = await fetch(`${API_BASE}/api/cover-letters`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) setLetters(await res.json());
  }

  async function loadExperiences() {
    const res = await fetch(`${API_BASE}/api/profile/experiences`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) setExperiences(await res.json());
  }

  async function addExperience(e) {
    e.preventDefault();
    setExpBusy(true);
    try {
      const res = await fetch(`${API_BASE}/api/profile/experiences`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          title: expTitle,
          description: expDescription,
          skills: expSkills || null,
        }),
      });

      if (res.ok) {
        setExpTitle("");
        setExpDescription("");
        setExpSkills("");
        loadExperiences();
      }
    } finally {
      setExpBusy(false);
    }
  }

  async function deleteExperience(id) {
    setDeletingExpId(id);
    try {
      await fetch(`${API_BASE}/api/profile/experiences/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      loadExperiences();
    } finally {
      setDeletingExpId(null);
    }
  }

  // Whenever we get a token (just logged in), load history + experiences
  useEffect(() => {
    if (token) {
      loadHistory();
      loadExperiences();
    }
  }, [token]);

  if (!token) {
    return (
      <div className="page page-center">
        <form className="auth-card" onSubmit={login}>
          <div className="brand">
            <span className="brand-mark">✉</span>
            <h1 className="brand-title">Cover Letter Generator</h1>
          </div>
          <p className="brand-sub">Sign in to generate and manage your cover letters.</p>

          <div className="field">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              name="username"
              autoComplete="username"
              placeholder="jane.doe"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          <div className="field">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <div className="auth-actions">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={register}
              disabled={authBusy}
            >
              Register
            </button>
            <button type="submit" className="btn btn-primary" disabled={authBusy}>
              {authBusy && <span className="spinner" />} Login
            </button>
          </div>

          {authStatus.text && (
            <p className={`status-msg ${authStatus.error ? "status-error" : "status-info"}`}>
              {authStatus.text}
            </p>
          )}
        </form>
      </div>
    );
  }

  return (
    <div className="page">
      <header className="app-header">
        <div className="brand brand-compact">
          <span className="brand-mark">✉</span>
          <h2 className="brand-title">Cover Letter Generator</h2>
        </div>
        <button className="btn btn-ghost btn-small" onClick={logout}>
          Log out ({username})
        </button>
      </header>

      <div className="app-grid">
        <div className="stack">
          <section className="card">
            <div className="card-header-row">
              <h2>My Experience</h2>
            </div>
            <p className="card-hint">
              Add roles, projects, or skills — the generator uses these as your
              background instead of a static resume file.
            </p>

            <form onSubmit={addExperience}>
              <div className="field">
                <label htmlFor="exp-title">Title</label>
                <input
                  id="exp-title"
                  placeholder="e.g. Backend Developer, Acme Inc."
                  value={expTitle}
                  onChange={(e) => setExpTitle(e.target.value)}
                  required
                />
              </div>
              <div className="field">
                <label htmlFor="exp-description">Description</label>
                <textarea
                  id="exp-description"
                  rows={3}
                  placeholder="What did you do / build / own?"
                  value={expDescription}
                  onChange={(e) => setExpDescription(e.target.value)}
                  required
                />
              </div>
              <div className="field">
                <label htmlFor="exp-skills">Skills (optional)</label>
                <input
                  id="exp-skills"
                  placeholder="Python, FastAPI, SQL"
                  value={expSkills}
                  onChange={(e) => setExpSkills(e.target.value)}
                />
              </div>
              <div className="card-actions">
                <button type="submit" className="btn btn-primary" disabled={expBusy}>
                  {expBusy && <span className="spinner" />} Add Experience
                </button>
              </div>
            </form>

            {experiences.length === 0 ? (
              <p className="empty-state mt-lg">
                No experience entries yet — add one above.
              </p>
            ) : (
              <div className="letter-list mt-lg">
                {experiences.map((exp) => (
                  <div className="letter-card" key={exp.id}>
                    <div className="letter-info">
                      <span className="letter-title">{exp.title}</span>
                      <span className="letter-company">{exp.description}</span>
                      {exp.skills && <span className="letter-date">Skills: {exp.skills}</span>}
                    </div>
                    <button
                      className="btn btn-ghost btn-small"
                      onClick={() => deleteExperience(exp.id)}
                      disabled={deletingExpId === exp.id}
                    >
                      {deletingExpId === exp.id ? <span className="spinner" /> : "Delete"}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </section>

          <section className="card">
            <div className="card-header-row">
              <h2>New Cover Letter</h2>
            </div>
            <p className="card-hint">Paste a job description and generate a tailored letter.</p>

            <form onSubmit={generate}>
              <div className="field">
                <label htmlFor="job-description">Job description</label>
                <textarea
                  id="job-description"
                  rows={8}
                  placeholder="Paste the job posting here..."
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  required
                />
              </div>
              <div className="card-actions">
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={genBusy || experiences.length === 0}
                >
                  {genBusy && <span className="spinner" />} Generate
                </button>
                {experiences.length === 0 && (
                  <span className="status-msg inline status-info">
                    Add at least one experience entry first.
                  </span>
                )}
              </div>
              {genStatus.text && (
                <p className={`status-msg ${genStatus.error ? "status-error" : "status-info"}`}>
                  {genStatus.text}
                </p>
              )}
            </form>
          </section>
        </div>

        <section className="card">
          <div className="card-header-row">
            <h2>History</h2>
          </div>
          <p className="card-hint">Your previously generated cover letters.</p>

          {letters.length === 0 ? (
            <p className="empty-state">No cover letters yet.</p>
          ) : (
            <div className="letter-list">
              {letters.map((letter) => (
                <div className="letter-card" key={letter.id}>
                  <div className="letter-info">
                    <span className="letter-title">{letter.job_title}</span>
                    <span className="letter-company">{letter.company_name}</span>
                    <span className="letter-date">
                      {new Date(letter.created_at).toLocaleString()}
                    </span>
                  </div>
                  <button
                    className="btn btn-secondary btn-small"
                    onClick={() => downloadPdf(letter.id)}
                    disabled={downloadingId === letter.id}
                  >
                    {downloadingId === letter.id ? <span className="spinner" /> : "Download PDF"}
                  </button>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

export default App;

import { useState, useEffect } from "react";
import "./App.css";

const API_BASE = "http://127.0.0.1:8000";

function App() {
  const [token, setToken] = useState(null);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [authStatus, setAuthStatus] = useState("");

  const [jobDescription, setJobDescription] = useState("");
  const [genStatus, setGenStatus] = useState("");
  const [letters, setLetters] = useState([]);

  async function register() {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    setAuthStatus(res.ok ? "Registered — now log in." : "Registration failed.");
  }

  async function login() {
    const form = new URLSearchParams();
    form.append("username", username);
    form.append("password", password);

    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form,
    });

    if (!res.ok) {
      setAuthStatus("Login failed.");
      return;
    }

    const data = await res.json();
    setToken(data.access_token);
  }

  async function generate() {
    setGenStatus("Generating...");
    const res = await fetch(`${API_BASE}/api/cover-letters`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ job_description: jobDescription }),
    });

    setGenStatus(res.ok ? "Done!" : "Failed to generate.");
    if (res.ok) {
      setJobDescription("");
      loadHistory();
    }
  }

  async function downloadPdf(letterId) {
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
  }

  async function loadHistory() {
    const res = await fetch(`${API_BASE}/api/cover-letters`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) setLetters(await res.json());
  }

  // Whenever we get a token (just logged in), load the history
  useEffect(() => {
    if (token) loadHistory();
  }, [token]);

  if (!token) {
    return (
      <div className="container">
        <h2>Cover Letter Generator</h2>
        <h3>Login</h3>
        <input
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <button onClick={register}>Register</button>
        <button onClick={login}>Login</button>
        <p>{authStatus}</p>
      </div>
    );
  }

  return (
    <div className="container">
      <h2>Cover Letter Generator</h2>

      <h3>New Cover Letter</h3>
      <textarea
        rows={8}
        placeholder="Paste job description..."
        value={jobDescription}
        onChange={(e) => setJobDescription(e.target.value)}
      />
      <button onClick={generate}>Generate</button>
      <p>{genStatus}</p>

      <h3>History</h3>
      {letters.map((letter) => (
        <div className="letter-card" key={letter.id}>
          <strong>{letter.job_title}</strong> — {letter.company_name}
          <br />
          <small>{new Date(letter.created_at).toLocaleString()}</small>
          <br />
          <button onClick={() => downloadPdf(letter.id)}>
            Download PDF
          </button>
        </div>
      ))}
    </div>
  );
}

export default App;
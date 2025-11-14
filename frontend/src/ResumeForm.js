import React, { useState, useEffect } from "react";
import axios from "axios";

const API_BASE = "http://93.127.129.105:8000";

const ResumeForm = ({ authKey }) => {
  const [resumes, setResumes] = useState([]);
  const [form, setForm] = useState({
    name: "",
    role_name: "",
    email: "",
    phone: "",
    address: "",
    linkedin: "",
    profile_summary: "",
    skills: "",
  });
  const [education, setEducation] = useState([]);
  const [experience, setExperience] = useState([]);
  const [selectedName, setSelectedName] = useState(null);

  // Fetch list of resumes
  useEffect(() => {
    loadResumes();
  }, []);

  const loadResumes = async () => {
    try {
      const res = await axios.get(`${API_BASE}/resume/`);
      setResumes(res.data.resumes || []);
    } catch {
      console.error("Error fetching resumes list");
    }
  };

  useEffect(() => {
    if (!authKey) return;

    const timer = setTimeout(loadResumes, 500);
    return () => clearTimeout(timer);
  }, [authKey]);

  const loadResume = async (name) => {
    try {
      const res = await axios.get(`${API_BASE}/resume/${name}`);
      const data = res.data;
      setForm({
        name: data.name,
        role_name: data.role_name,
        email: data.email,
        phone: data.phone,
        address: data.address,
        linkedin: data.linkedin,
        profile_summary: data.profile_summary,
        skills: data.skills,
      });
      setEducation(data.education || []);
      setExperience(data.experience || []);
      setSelectedName(name);
    } catch {
      alert("Error loading resume");
    }
  };

  const handleNew = () => {
    setForm({
      name: "",
      role_name: "",
      email: "",
      phone: "",
      address: "",
      linkedin: "",
      profile_summary: "",
      skills: "",
    });
    setEducation([{ degree: "", category: "", from_year: "", to_year: "", location: "", university: "" }]);
    setExperience([{ role: "", company: "", from_date: "", to_date: "", location: "", responsibilities: "" }]);
    setSelectedName(null);
  };

  // Editor updates
  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });
  const handleEduChange = (i, e) => {
    const newEdu = [...education];
    newEdu[i][e.target.name] = e.target.value;
    setEducation(newEdu);
  };
  const handleExpChange = (i, e) => {
    const newExp = [...experience];
    newExp[i][e.target.name] = e.target.value;
    setExperience(newExp);
  };

  const addEdu = () => setEducation([...education, { degree: "", category: "", from_year: "", to_year: "", location: "", university: "" }]);
  const addExp = () => setExperience([...experience, { role: "", company: "", from_date: "", to_date: "", location: "", responsibilities: "" }]);

  const deleteEdu = (i) => setEducation(education.filter((_, idx) => idx !== i));
  const deleteExp = (i) => setExperience(experience.filter((_, idx) => idx !== i));

  const handleSave = async () => {
    try {
      const payload = { ...form, education, experience };
      const res = await axios.post(`${API_BASE}/resume`, payload);
      alert("Saved successfully!");
      loadResumes();
      setSelectedName(form.name);
    } catch {
      alert("Error saving resume");
    }
  };

  return (
    <div style={{ display: "flex", height: "100vh", fontFamily: "sans-serif" }}>
      {/* Left column — Resume list */}
      <div style={{ width: "220px", background: "#f0f2f5", padding: "10px", borderRight: "1px solid #ccc" }}>
        <h3 style={{ margin: "10px 0" }}>Resumes</h3>
        <button
          onClick={handleNew}
          style={{
            width: "100%",
            background: "#007bff",
            color: "#fff",
            padding: "6px",
            border: "none",
            borderRadius: "4px",
            marginBottom: "10px",
            cursor: "pointer",
          }}
        >
          ➕ New Resume
        </button>
        <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
          {resumes.map((name, idx) => (
            <li key={idx}>
              <button
                onClick={() => loadResume(name)}
                style={{
                  width: "100%",
                  textAlign: "left",
                  padding: "6px",
                  border: "none",
                  borderRadius: "4px",
                  marginBottom: "4px",
                  background: name === selectedName ? "#007bff" : "#fff",
                  color: name === selectedName ? "#fff" : "#333",
                  cursor: "pointer",
                }}
              >
                {name}
              </button>
            </li>
          ))}
        </ul>
      </div>

      {/* Middle column — Editor form */}
      <div style={{ flex: 1, padding: "20px", overflowY: "auto" }}>
        <h2>Resume Editor</h2>
        {["name", "role_name", "email", "phone", "address", "linkedin"].map((f) => (
          <div key={f} style={{ marginBottom: "8px" }}>
            <label style={{ fontWeight: "bold" }}>{f.replace("_", " ").toUpperCase()}</label>
            <input
              type="text"
              name={f}
              value={form[f]}
              onChange={handleChange}
              style={{ width: "100%", padding: "6px" }}
            />
          </div>
        ))}

        <h4>Profile Summary</h4>
        <textarea
          name="profile_summary"
          value={form.profile_summary}
          onChange={handleChange}
          rows={5}
          style={{ width: "100%", padding: "6px" }}
        />

        <h4>Education</h4>
        {education.map((edu, i) => (
          <div key={i} style={{ border: "1px solid #ccc", padding: "10px", borderRadius: "6px", marginBottom: "10px" }}>
            <button
              type="button"
              onClick={() => deleteEdu(i)}
              style={{ float: "right", background: "#dc3545", color: "#fff", border: "none", padding: "2px 8px", borderRadius: "4px" }}
            >
              🗑
            </button>
            {["degree", "category", "from_year", "to_year", "location", "university"].map((f) => (
              <div key={f} style={{ marginBottom: "4px" }}>
                <label style={{ fontWeight: "bold" }}>{f.replace("_", " ").toUpperCase()}</label>
                <input
                  type="text"
                  name={f}
                  value={edu[f]}
                  onChange={(e) => handleEduChange(i, e)}
                  style={{ width: "100%", padding: "5px" }}
                />
              </div>
            ))}
          </div>
        ))}
        <button onClick={addEdu}>➕ Add Education</button>

        <h4>Experience</h4>
        {experience.map((exp, i) => (
          <div key={i} style={{ border: "1px solid #ccc", padding: "10px", borderRadius: "6px", marginBottom: "10px" }}>
            <button
              type="button"
              onClick={() => deleteExp(i)}
              style={{ float: "right", background: "#dc3545", color: "#fff", border: "none", padding: "2px 8px", borderRadius: "4px" }}
            >
              🗑
            </button>
            {["role", "company", "from_date", "to_date", "location"].map((f) => (
              <div key={f} style={{ marginBottom: "4px" }}>
                <label style={{ fontWeight: "bold" }}>{f.replace("_", " ").toUpperCase()}</label>
                <input
                  type="text"
                  name={f}
                  value={exp[f]}
                  onChange={(e) => handleExpChange(i, e)}
                  style={{ width: "100%", padding: "5px" }}
                />
              </div>
            ))}
            <label style={{ fontWeight: "bold" }}>Responsibilities</label>
            <textarea
              name="responsibilities"
              value={exp.responsibilities}
              onChange={(e) => handleExpChange(i, e)}
              rows={3}
              style={{ width: "100%", padding: "5px" }}
            />
          </div>
        ))}
        <button onClick={addExp}>➕ Add Experience</button>

        <h4>Skills</h4>
        <textarea
          name="skills"
          value={form.skills}
          onChange={handleChange}
          rows={4}
          style={{ width: "100%", padding: "6px" }}
        />

        <button
          onClick={handleSave}
          style={{
            marginTop: "15px",
            background: "#007bff",
            color: "#fff",
            padding: "8px 16px",
            border: "none",
            borderRadius: "6px",
            cursor: "pointer",
          }}
        >
          💾 Save Resume
        </button>
      </div>

      {/* Right column — Live preview */}
      <div style={{ width: "400px", background: "#fafafa", padding: "20px", borderLeft: "1px solid #ccc", overflowY: "auto" }}>
        <h2 style={{ marginBottom: "0" }}>{form.name || "Your Name"}</h2>
        <button
            onClick={async () => {
                try {
                const payload = { ...form, education, experience };
                const res = await axios.post(`${API_BASE}/resume/pdf`, payload, {
                    responseType: "blob",
                });
                const blob = new Blob([res.data], { type: "application/pdf" });
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement("a");
                link.href = url;
                link.download = `${form.name || "resume"}.pdf`;
                link.click();
                window.URL.revokeObjectURL(url);
                } catch (err) {
                alert("Error downloading PDF");
                }
            }}
            style={{
                background: "#28a745",
                color: "white",
                border: "none",
                padding: "6px 12px",
                borderRadius: "6px",
                cursor: "pointer",
            }}
            >
            ⬇️ Download PDF
            </button>
        <p style={{ fontStyle: "italic", color: "#666" }}>{form.role_name}</p>
        <p>{form.email} | {form.phone}</p>
        <p>{form.address}</p>
        <hr />
        <h3>Profile</h3>
        <p>{form.profile_summary}</p>
        <h3>Education</h3>
        {education.map((edu, i) => (
          <div key={i} style={{ marginBottom: "8px" }}>
            <strong>{edu.degree}</strong> — {edu.university} ({edu.from_year}–{edu.to_year})
            <br />
            <span>{edu.location}</span>
          </div>
        ))}
        <h3>Experience</h3>
        {experience.map((exp, i) => (
          <div key={i} style={{ marginBottom: "8px" }}>
            <strong>{exp.role}</strong> — {exp.company} ({exp.from_date}–{exp.to_date})
            <br />
            <span>{exp.location}</span>
            <ul>
              {exp.responsibilities
                ?.split("\n")
                .filter(Boolean)
                .map((r, idx) => (
                  <li key={idx}>{r.replace(/^•\s*/, "")}</li>
                ))}
            </ul>
          </div>
        ))}
        <h3>Skills</h3>
        <pre style={{ whiteSpace: "pre-wrap", fontFamily: "inherit" }}>{form.skills}</pre>
      </div>
    </div>
  );
};

export default ResumeForm;

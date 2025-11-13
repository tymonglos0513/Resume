import React, { useState } from "react";
import axios from "axios";

function MainPage({ authKey }) {
  const API_BASE = "http://93.127.142.20:8000";

  const [jobText, setJobText] = useState("");
  const [selectedResumeName, setSelectedResumeName] = useState("");
  const [resumeList, setResumeList] = useState([]);
  const [status, setStatus] = useState("");
  const [elapsed, setElapsed] = useState(0);
  const [downloading, setDownloading] = useState(false);
  const [companyName, setCompanyName] = useState("");
  const [roleName, setRoleName] = useState("");
  const [jobLink, setJobLink] = useState("");

  // load resume names on mount
  React.useEffect(() => {
    axios
      .get(`${API_BASE}/resume/`)
      .then((res) => setResumeList(res.data.resumes || []))
      .catch(() => setResumeList([]));
  }, []);

  React.useEffect(() => {
    if (!authKey) {
      setResumeList([]);
      setStatus("No auth key provided");
      return;
    }

    const fetchResumes = async () => {
      try {
        const res = await axios.get(`${API_BASE}/resume/`);
        setResumeList(res.data.resumes || []);
        setStatus("");
      } catch (err) {
        console.error(err);
        setStatus("❌ Failed to fetch resumes — check your key");
      }
    };

    // Optional debounce: wait 500ms after typing stops
    const timer = setTimeout(fetchResumes, 500);
    return () => clearTimeout(timer);
  }, [authKey]); // 👈 refetch whenever authKey changes

  const handleDownloadCustomizedResume = async () => {
    if (!selectedResumeName || !jobText.trim()) {
      alert("Please select a resume and enter a job description.");
      return;
    }

    setDownloading(true);
    setStatus("Generating customized resume...");
    setElapsed(0);

    const timer = setInterval(() => setElapsed((prev) => prev + 1), 1000);

    try {
      // Step 1 — get base resume
      const baseRes = await axios.get(`${API_BASE}/resume/${selectedResumeName}`);

      // Step 2 — customize it via AI
      const payload = { resume: baseRes.data, job_description: jobText };
      const customized = await axios.post(`${API_BASE}/resume/customize`, payload);
      const customizedResume = customized.data;

      if (customizedResume.error) throw new Error("Customization failed");

      setCompanyName(customizedResume["apply_company"])
      setRoleName(customizedResume["role_name"])

      try {
        await axios.post("http://93.127.142.20:8001/api/applications", {
          profile_name: selectedResumeName,
          company_name: customizedResume["apply_company"],
          job_link: jobLink,
          role_name: customizedResume["role_name"],
          resume: customizedResume, // full customized resume object
        });
        setStatus("✅ Resume successfully sent to external system!");
      } catch (err) {
        console.error("❌ Failed to send resume:", err);
        setStatus("⚠️ Customized resume generated but not sent to external system.");
      }

      // Step 3 — generate PDF
      setStatus("Generating PDF file...");
      const pdfRes = await axios.post(`${API_BASE}/resume/pdf`, customizedResume, {
        responseType: "blob",
      });

      // Step 4 — trigger download
      const blob = new Blob([pdfRes.data], { type: "application/pdf" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${customizedResume.name || "resume"}.pdf`;
      link.click();
      window.URL.revokeObjectURL(url);

      setStatus("✅ Download complete!");

      // ✅ Step 4 — Generate Cover Letter
      setStatus("Generating Cover Letter...");
      const coverRes = await axios.post(`${API_BASE}/resume/coverletter`, {
        resume: customizedResume,
        job_description: jobText,
      });

      const coverLetterText = coverRes.data.cover_letter;
      if (!coverLetterText) throw new Error("Cover letter generation failed");

      // Step 5 — Generate PDF for Cover Letter
      setStatus("Generating Cover Letter PDF...");
      const coverPdfRes = await axios.post(
        `${API_BASE}/resume/pdf`,
        {
          ...customizedResume,
          profile_summary: coverLetterText, // reuse the summary field for rendering
          name: customizedResume.name || selectedResumeName,
          role_name: "Cover Letter", // Label header
          experience: [],
          skills: "",
          education: [],
        },
        { responseType: "blob" }
      );

      const coverBlob = new Blob([coverPdfRes.data], { type: "application/pdf" });
      const coverUrl = window.URL.createObjectURL(coverBlob);
      const coverLink = document.createElement("a");
      coverLink.href = coverUrl;
      coverLink.download = `${customizedResume.name || "resume"}_cover_letter.pdf`;
      coverLink.click();
      window.URL.revokeObjectURL(coverUrl);

      setStatus("✅ Resume and Cover Letter Generated!");
    } catch (err) {
      console.error(err);
      setStatus("❌ Error generating customized resume.");
    } finally {
      clearInterval(timer);
      setDownloading(false);
    }
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        fontFamily: "sans-serif",
        backgroundColor: "#f7f9fc",
      }}
    >
      {/* Header */}
      <header
        style={{
          padding: "20px",
          borderBottom: "1px solid #ccc",
          background: "#fff",
          textAlign: "center",
        }}
      >
        <h2 style={{ margin: 0 }}>Resume Customizer</h2>
      </header>

      {/* Main content */}
      <main style={{ flex: 1, padding: "40px", maxWidth: "800px", margin: "0 auto" }}>
        <label style={{ fontWeight: "bold" }}>Select Resume</label>
        <select
          value={selectedResumeName}
          onChange={(e) => setSelectedResumeName(e.target.value)}
          style={{
            width: "100%",
            marginBottom: "15px",
            padding: "8px",
            border: "1px solid #ccc",
            borderRadius: "4px",
          }}
        >
          <option value="">-- Choose Resume --</option>
          {resumeList.map((name, i) => (
            <option key={i} value={name}>
              {name}
            </option>
          ))}
        </select>

        <textarea
          value={jobText}
          onChange={(e) => setJobText(e.target.value)}
          placeholder="First line should be Job Title, and job description following"
          rows={14}
          style={{
            width: "100%",
            borderRadius: "6px",
            border: "1px solid #ccc",
            padding: "10px",
            resize: "vertical",
            marginBottom: "20px",
            fontFamily: "monospace",
          }}
        />

        <div style={{ marginTop: "10px" }}>
          <label style={{ fontWeight: "bold" }}>Job Link</label>
          <input
            type="text"
            value={jobLink}
            onChange={(e) => setJobLink(e.target.value)}
            placeholder="Paste the job URL"
            style={{
              width: "100%",
              marginBottom: "10px",
              padding: "8px",
              borderRadius: "4px",
              border: "1px solid #ccc",
            }}
          />
        </div>

        <button
          onClick={handleDownloadCustomizedResume}
          disabled={downloading}
          style={{
            background: downloading ? "#6c757d" : "#28a745",
            color: "white",
            padding: "10px 20px",
            border: "none",
            borderRadius: "6px",
            cursor: downloading ? "not-allowed" : "pointer",
            fontSize: "16px",
          }}
        >
          {downloading ? "⏳ Generating Resume and Cover letter ..." : "⬇️ Download Customized Resume and Cover letter"}
        </button>
        <div style={{ marginTop: "30px" }}>
          <label style={{ fontWeight: "bold" }}>Company Name</label>
          <input
            type="text"
            value={companyName}
            placeholder="e.g. Chainlink Labs"
            readOnly
            style={{
              width: "100%",
              marginBottom: "10px",
              padding: "8px",
              borderRadius: "4px",
              border: "1px solid #ccc",
              cursor: "not-allowed",
            }}
          />

          <label style={{ fontWeight: "bold" }}>Role Name</label>
          <input
            type="text"
            value={roleName}
            placeholder="e.g. Senior Backend Engineer"
            readOnly
            style={{
              width: "100%",
              marginBottom: "10px",
              padding: "8px",
              borderRadius: "4px",
              border: "1px solid #ccc",
              cursor: "not-allowed",
            }}
          />
        </div>
      </main>

      {/* Footer status bar */}
      {status && (
        <footer
          style={{
            position: "fixed",
            bottom: 0,
            left: 0,
            width: "100%",
            backgroundColor: "#f8f9fa",
            borderTop: "1px solid #ddd",
            padding: "8px 20px",
            textAlign: "center",
            fontFamily: "sans-serif",
            fontSize: "14px",
            color: downloading
              ? "#333"
              : status.startsWith("✅")
              ? "green"
              : "red",
          }}
        >
          {status}
          {downloading && (
            <span style={{ marginLeft: "6px" }}>({elapsed}s elapsed)</span>
          )}
        </footer>
      )}
    </div>
  );
}

export default MainPage;

import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Cell } from "recharts";

function CountPage({ authKey }) {
  const API_BASE = "http://93.127.142.20:8000";

  const [date, setDate] = useState(() => new Date().toISOString().split("T")[0]);
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [logContent, setLogContent] = useState("");
  const [loadingLog, setLoadingLog] = useState(false);
  const logRef = useRef(null);

  const fetchCounts = async (selectedDate) => {
    try {
      setLoading(true);
      setError("");
      const res = await axios.get(`${API_BASE}/resume/counts/${selectedDate}`);
      if (res.data.error) {
        setError(res.data.error);
        setData([]);
        return;
      }
      const countsObj = res.data.counts || {};
      const formattedData = Object.entries(countsObj).map(([name, count]) => ({
        name,
        count,
      }));
      setData(formattedData);
    } catch (err) {
      console.error(err);
      setError("Failed to fetch data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCounts(date);
  }, []);

  useEffect(() => {
    if (!authKey) return;

    const timer = setTimeout(() => fetchCounts(date), 500);
    return () => clearTimeout(timer);
  }, [authKey]);

  useEffect(() => {
    if (!authKey) return;

    const fetchLogs = async () => {
      setLoadingLog(true);
      try {
        const res = await axios.get(`${API_BASE}/logs/startup`);
        setLogContent(res.data);
      } catch (err) {
        console.error("Error fetching logs:", err);
        setLogContent("❌ Failed to load logs.");
      } finally {
        setLoadingLog(false);
      }
    };

    fetchLogs(); // initial fetch
  }, [authKey]);

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [logContent]);

  return (
    <div
      style={{
        fontFamily: "sans-serif",
        backgroundColor: "#f7f9fc",
        height: "100vh",
        padding: "30px",
      }}
    >
      <h2 style={{ textAlign: "center", marginBottom: "20px" }}>📊 Resume Customization Stats</h2>

      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          marginBottom: "20px",
          gap: "10px",
        }}
      >
        <label style={{ fontWeight: "bold" }}>Select Date:</label>
        <input
          type="date"
          value={date}
          onChange={(e) => {
            setDate(e.target.value);
            fetchCounts(e.target.value);
          }}
          style={{
            padding: "6px 10px",
            borderRadius: "4px",
            border: "1px solid #ccc",
          }}
        />
      </div>

      {loading && <p style={{ textAlign: "center" }}>Loading data...</p>}
      {error && <p style={{ textAlign: "center", color: "red" }}>{error}</p>}

      {!loading && !error && data.length > 0 && (
        <ResponsiveContainer width="100%" height={400}>
          <BarChart
            data={data}
            margin={{ top: 10, right: 30, left: 0, bottom: 20 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" angle={0} textAnchor="end" height={70} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="count" barSize={40}>
              {data.map((entry, index) => {
                const colors = [
                  "#007bff", "#28a745", "#ffc107", "#dc3545", "#6610f2",
                  "#17a2b8", "#6f42c1", "#fd7e14", "#20c997", "#e83e8c",
                  "#198754", "#0dcaf0", "#ff6f61", "#7952b3", "#fdc500"
                ];
                const color = colors[index % colors.length];
                return <Cell key={`cell-${index}`} fill={color} />;
              })}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}

      {!loading && !error && data.length === 0 && (
        <p style={{ textAlign: "center", color: "#555" }}>No data found for this date.</p>
      )}

      <div style={{ marginTop: "40px" }}>
        <h3>Backend Logs</h3>
        <textarea
          ref={logRef}
          readOnly
          value={loadingLog ? "Loading logs..." : logContent}
          rows={30}
          style={{
            width: "100%",
            fontFamily: "monospace",
            backgroundColor: "#111",
            color: "#0f0",
            padding: "10px",
            borderRadius: "6px",
            border: "1px solid #444",
            resize: "vertical",
          }}
        />
      </div>
    </div>
  );
}

export default CountPage;

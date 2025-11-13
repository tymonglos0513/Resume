import React, { useState, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Header from "./Header";
import MainPage from "./MainPage";
import ResumeForm from "./ResumeForm";
import CountPage from "./CountPage";
import axios from "axios";

function App() {
  const [authKey, setAuthKey] = useState(() => localStorage.getItem("authKey") || "");

  useEffect(() => {
    if (authKey) {
      localStorage.setItem("authKey", authKey);
    } else {
      localStorage.removeItem("authKey");
    }
  }, [authKey]);

  // ✅ Update Axios header dynamically on key change
  useEffect(() => {
    axios.interceptors.request.handlers = []; // remove old interceptors
    axios.interceptors.request.use((config) => {
      if (authKey) config.headers["X-Auth-Key"] = authKey;
      return config;
    });
  }, [authKey]);

  return (
    <Router>
      <Header authKey={authKey} setAuthKey={setAuthKey} />
      <div style={{ marginTop: "20px" }}>
        <Routes>
          <Route path="/" element={<MainPage authKey={authKey} />} />
          <Route path="/resume" element={<ResumeForm authKey={authKey} />} />
          <Route path="/counts" element={<CountPage authKey={authKey} />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;

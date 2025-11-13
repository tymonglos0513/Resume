import React from "react";
import { Link, useLocation } from "react-router-dom";

const Header = ({ authKey, setAuthKey }) => {
  const location = useLocation();

  const navStyle = {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    backgroundColor: "#007bff",
    color: "#fff",
    padding: "10px 30px",
    fontFamily: "sans-serif",
  };

  const linkStyle = (path) => ({
    color: "#fff",
    textDecoration: "none",
    fontWeight: location.pathname === path ? "bold" : "normal",
    borderBottom: location.pathname === path ? "2px solid #fff" : "none",
    paddingBottom: "2px",
    transition: "border-bottom 0.2s",
  });

  return (
    <header style={navStyle}>
      <h2 style={{ margin: 0 }}>AI Tools Portal</h2>
      <input
        type="password"
        value={authKey}
        onChange={(e) => setAuthKey(e.target.value)}
        placeholder="Enter Access Key"
        style={{
          padding: "6px 10px",
          borderRadius: "4px",
          border: "1px solid #ccc",
          outline: "none",
          width: "200px",
        }}
      />
      <nav style={{ display: "flex", gap: "20px" }}>
        <Link to="/" style={linkStyle("/")}>
          🏠 Main Page
        </Link>
        <Link to="/resume" style={linkStyle("/resume")}>
          📄 Resume Page
        </Link>
      </nav>
    </header>
  );
};

export default Header;

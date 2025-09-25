import React, { useState, useEffect } from "react";
import axios from "axios";

function App() {
  const [file, setFile] = useState(null);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [user, setUser] = useState(null);

  // ✅ Check if user is logged in when app loads
  useEffect(() => {
    axios
      .get("http://127.0.0.1:8000/me", { withCredentials: true })
      .then((res) => {
        if (res.data.user) {
          setUser(res.data.user);
        }
      })
      .catch(() => console.log("Not logged in"));
      const params = new URLSearchParams(window.location.search);
  const email = params.get("email");
  const id = params.get("id");
  const name = params.get("name"); // 👈 get name

  if (email && id) {
    setUser({ id, email, name }); // 👈 store name too
    window.history.replaceState({}, document.title, "/");
  }
  }, []);

  // 🔹 Google Sign-In
  const handleGoogleLogin = () => {
    window.location.href = "http://127.0.0.1:8000/login"; // Backend handles redirect
  };

  // 🔹 Upload PDF to backend
  const uploadPDF = async () => {
    if (!file) {
      alert("Please select a PDF first!");
      return;
    }
    try {
      const formData = new FormData();
      formData.append("file", file);

      await axios.post("http://127.0.0.1:8000/upload_pdf", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        withCredentials: true,
      });

      alert("✅ PDF uploaded and processed!");
    } catch (err) {
      console.error("Error uploading PDF:", err);
      alert("❌ Upload failed!");
    }
  };

  // 🔹 Ask a question to backend
  const askQuestion = async () => {
    if (!question.trim()) return;

    setMessages((prev) => [...prev, { role: "user", text: question }]);

    try {
      const res = await axios.post(
        "http://127.0.0.1:8000/ask",
        { question },
        {
          headers: { "Content-Type": "application/json" },
          withCredentials: true,
        }
      );

      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          text: res.data.answer,
          refs: res.data.sources,
        },
      ]);

      setQuestion("");
    } catch (err) {
      console.error("Error asking question:", err);
      alert("❌ Failed to get answer!");
    }
  };

  return (
      <div
    style={{
      maxWidth: 600,
      margin: "auto",
      padding: 20,
      background: "linear-gradient(135deg, #f9f9f9, #e6f0ff)", // 🔹 Background color
      minHeight: "100vh",
      borderRadius: "10px",
    }}
  >
      <h2>NEURORAG</h2>

      {/* 🔹 Auth Section */}
      {!user ? (
        <button
          onClick={handleGoogleLogin}
          style={{
            marginBottom: 20,
            padding: "10px 20px",
            background: "#4285F4",
            color: "white",
            border: "none",
            borderRadius: "5px",
            cursor: "pointer",
          }}
        >
          Sign in with Google
        </button>
      ) : (
        <div style={{ marginBottom: 20 }}>
          ✅ Logged in as <b>{user.name || user.email}</b>
        </div>
      )}

      {/* 🔹 PDF Upload */}
      <div style={{ marginBottom: 20 }}>
        <input
          type="file"
          accept="application/pdf"
          onChange={(e) => setFile(e.target.files[0])}
        />
        <button onClick={uploadPDF} style={{ marginLeft: 10 }}>
          Upload PDF
        </button>
      </div>

      {/* 🔹 Chat Messages */}
      <div style={{ marginTop: 20, borderTop: "1px solid #ccc", paddingTop: 10 }}>
        {messages.map((m, i) => (
          <div key={i} style={{ marginBottom: 15 }}>
            <b>{m.role === "user" ? "You" : "Bot"}:</b> {m.text}
            {m.refs && (
              <div style={{ fontSize: "0.8em", color: "gray", marginTop: 5 }}>
                <b>References:</b>
                <ul>
                  {m.refs.map((r, j) => (
                    <li key={j}>{r.slice(0, 100)}...</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* 🔹 Input Box */}
      <div style={{ marginTop: 20 }}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask something..."
          style={{ width: "80%", marginRight: 10 }}
        />
        <button onClick={askQuestion}>Ask</button>
      </div>
    </div>
  );
}

export default App;

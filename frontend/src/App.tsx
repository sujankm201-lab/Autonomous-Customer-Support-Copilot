import { useState } from "react";

function App() {
  const [token, setToken] = useState("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");

  const askQuestion = async () => {
    try {
      const response = await fetch("http://127.0.0.1:8000/rag/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          query: question,
        }),
      });

      const data = await response.json();

      console.log("Status:", response.status);
      console.log("Response:", data);

      if (response.ok) {
        setAnswer(data.answer);
      } else {
        setAnswer(JSON.stringify(data));
      }
    } catch (error) {
      console.error(error);
      setAnswer("Connection error");
    }
  };

  return (
    <div style={{ padding: "20px" }}>
      <h1>Autonomous Customer Support Copilot</h1>

      <input
        type="text"
        placeholder="Paste JWT Token"
        value={token}
        onChange={(e) => setToken(e.target.value)}
        style={{ width: "600px", marginBottom: "10px" }}
      />

      <br />

      <input
        type="text"
        placeholder="Ask your support question"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        style={{ width: "600px", marginBottom: "10px" }}
      />

      <br />

      <button onClick={askQuestion}>Ask</button>

      <h2>Answer:</h2>
      <p>{answer}</p>
    </div>
  );
}

export default App;
import { useState } from "react"
import { API_URL } from "../api"

function AskAI({ meetingId }) {
  const [question, setQuestion] = useState("")
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [expandedEvidence, setExpandedEvidence] = useState(null)

  const askQuestion = async () => {
    if (!question.trim() || loading) return

    const userQuestion = question.trim()
    setMessages((prev) => [...prev, { role: "user", content: userQuestion }])
    setQuestion("")
    setLoading(true)

    try {
      const response = await fetch(`${API_URL}/meetings/${meetingId}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: userQuestion, history: messages })
      })

      const data = await response.json()

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.answer, evidence: data.evidence }
      ])
    } catch (error) {
      console.error(error)
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Failed to get an answer." }
      ])
    }

    setLoading(false)
  }

  return (
    <div style={{ marginBottom: "32px" }}>
      <h2>Ask AI</h2>

      <div style={{ marginBottom: "16px" }}>
        {messages.map((message, index) => (
          <div key={index} style={{ padding: "10px", margin: "6px 0", borderRadius: "8px", background: message.role === "user" ? "#1e3a5f" : "#1a1a1a" }}>
            <strong>{message.role === "user" ? "You" : "AI"}</strong>
            <p style={{ margin: "4px 0" }}>{message.content}</p>

            {message.role === "assistant" && message.evidence?.length > 0 && (
              <div style={{ marginTop: "8px" }}>
                <small style={{ color: "#888" }}>Evidence:</small>
                {message.evidence.map((item, ei) => {
                  const isExpanded = expandedEvidence === `${index}-${ei}`
                  return (
                    <div key={ei}>
                      <button
                        onClick={() => setExpandedEvidence(isExpanded ? null : `${index}-${ei}`)}
                        style={{ background: "#333", border: "none", color: "#ccc", padding: "4px 8px", borderRadius: "4px", cursor: "pointer", margin: "2px" }}
                      >
                        {item.start} - {item.end}
                      </button>
                      {isExpanded && <p style={{ color: "#aaa", fontSize: "13px" }}>{item.text}</p>}
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        ))}

        {loading && <p style={{ color: "#888" }}>AI is thinking...</p>}
      </div>

      <div style={{ display: "flex", gap: "8px" }}>
        <input
          type="text"
          value={question}
          placeholder="Ask anything about this meeting..."
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") askQuestion() }}
          style={{ flex: 1, padding: "10px", borderRadius: "8px", border: "1px solid #333", background: "#222", color: "white" }}
        />
        <button
          onClick={askQuestion}
          disabled={loading || !question.trim()}
          style={{ padding: "10px 20px", borderRadius: "8px", border: "none", background: "#3b82f6", color: "white", cursor: "pointer" }}
        >
          {loading ? "..." : "Ask"}
        </button>
      </div>
    </div>
  )
}

export default AskAI
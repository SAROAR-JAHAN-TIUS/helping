import { useState } from "react"

function AskAI() {
  const [question, setQuestion] = useState("")
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
 const [expandedEvidence, setExpandedEvidence] = useState(null)

  const askQuestion = async () => {
    if (!question.trim() || loading) return

    const userQuestion = question.trim()

    setMessages(prev => [
      ...prev,
      {
        role: "user",
        content: userQuestion
      }
    ])

    setQuestion("")
    setLoading(true)

    try {
      const response = await fetch(
  "http://127.0.0.1:8000/meeting/ask",
  {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      question: userQuestion,
      history: messages
    })
  }
)
      const data = await response.json()

     setMessages(prev => [
  ...prev,
  {
    role: "assistant",
    content: data.answer,
    evidence: data.evidence
  }
])
    } catch (error) {
      console.error(error)

      setMessages(prev => [
        ...prev,
        {
          role: "assistant",
          content: "Failed to get an answer."
        }
      ])
    }

    setLoading(false)
  }

 return (
  <section>
    <h2>Ask AI</h2>

    <div>
      {messages.map((message, index) => (
        <div key={index}>
          <strong>
            {message.role === "user" ? "You" : "AI"}
          </strong>

          <p>{message.content}</p>

         {message.role === "assistant" &&
  message.evidence &&
  message.evidence.length > 0 && (
    <div>
      <strong>Evidence</strong>

      {message.evidence.map((item, evidenceIndex) => {
        const isExpanded =
          expandedEvidence === `${index}-${evidenceIndex}`

        return (
          <div key={evidenceIndex}>

            <button
              onClick={() => {
                const id = `${index}-${evidenceIndex}`

                setExpandedEvidence(
                  isExpanded ? null : id
                )

              }}
            >
              {item.start} - {item.end}
            </button>

            {isExpanded && (
              <p>
                {item.text}
              </p>
            )}

          </div>
        )
      })}
    </div>
  )}
        </div>
      ))}

      {loading && <p>AI is thinking...</p>}
    </div>

    <div>
      <input
        type="text"
        value={question}
        placeholder="Ask anything about this meeting..."
        onChange={e => setQuestion(e.target.value)}
        onKeyDown={e => {
          if (e.key === "Enter") {
            askQuestion()
          }
        }}
      />

      <button
        onClick={askQuestion}
        disabled={loading || !question.trim()}
      >
        {loading ? "Thinking..." : "Ask"}
      </button>
    </div>
  </section>
)
}

export default AskAI
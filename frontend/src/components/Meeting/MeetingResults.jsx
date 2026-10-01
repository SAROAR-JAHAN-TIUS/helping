import { useState, useEffect } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { API_URL } from "../../api"
import AskAI from "../AskAI"
import CalendarEvents from "../CalendarEvents"

function MeetingResults({ user }) {
  const { meetingId } = useParams()
  const navigate = useNavigate()

  const [status, setStatus] = useState("loading")
  const [analysis, setAnalysis] = useState(null)
  const [events, setEvents] = useState(null)
  const [hasReport, setHasReport] = useState(false)
  const [hasConversation, setHasConversation] = useState(false)
  const [meetingInfo, setMeetingInfo] = useState(null)

  useEffect(() => {
    checkResults()
    const interval = setInterval(checkResults, 3000)
    return () => clearInterval(interval)
  }, [meetingId])

  const checkResults = async () => {
    try {
      const response = await fetch(`${API_URL}/meetings/${meetingId}/results`)
      const data = await response.json()

      if (!data.success) return

      setStatus(data.status)

      if (data.analysis) setAnalysis(data.analysis)
      if (data.events) setEvents(data.events)
      setHasReport(data.has_report)
      setHasConversation(data.has_conversation_pdf)

      // Fetch meeting info
      const statusResponse = await fetch(`${API_URL}/meetings/${meetingId}/status`)
      const statusData = await statusResponse.json()
      if (statusData.success) setMeetingInfo(statusData.meeting)
    } catch (error) {
      console.error("Failed to fetch results:", error)
    }
  }

  if (status === "loading" || status === "ending" || status === "processing") {
    return (
      <div style={styles.page}>
        <div style={styles.center}>
          <h2>Processing Meeting...</h2>
          <p style={styles.muted}>Analyzing transcript, generating reports, extracting calendar events...</p>
          <div style={styles.spinner}></div>
          <p style={styles.muted}>This may take a minute.</p>
        </div>
      </div>
    )
  }

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <h1>Meeting Results</h1>
        <button onClick={() => navigate("/dashboard")} style={styles.backBtn}>
          ← Dashboard
        </button>
      </div>

      {meetingInfo && (
        <div style={styles.infoBar}>
          <span>{meetingInfo.title}</span>
          <span style={styles.muted}> · {meetingInfo.participants?.length || 0} participants</span>
        </div>
      )}

      {/* PDF Downloads */}
      <div style={styles.section}>
        <h2>Meeting Files</h2>
        <div style={styles.fileButtons}>
          {hasReport && (
            <button
              onClick={() => window.open(`${API_URL}/meetings/${meetingId}/report`, "_blank")}
              style={styles.fileBtn}
            >
              📄 Meeting Report PDF
            </button>
          )}
          {hasConversation && (
            <button
              onClick={() => window.open(`${API_URL}/meetings/${meetingId}/full-conversation`, "_blank")}
              style={styles.fileBtn}
            >
              📝 Full Conversation PDF
            </button>
          )}
          {!hasReport && !hasConversation && (
            <p style={styles.muted}>No files available yet.</p>
          )}
        </div>
      </div>

      {/* Analysis */}
      {analysis && (
        <div style={styles.section}>
          <h2>Meeting Summary</h2>
          <p>{analysis.summary}</p>

          {analysis.key_discussions?.length > 0 && (
            <>
              <h3>Key Discussions</h3>
              {analysis.key_discussions.map((item, i) => (
                <div key={i} style={styles.card}>
                  <h4>{item.topic}</h4>
                  <p>{item.discussion}</p>
                  <small style={styles.muted}>{item.timestamp}</small>
                </div>
              ))}
            </>
          )}

          {analysis.decisions?.length > 0 && (
            <>
              <h3>Decisions</h3>
              {analysis.decisions.map((item, i) => (
                <div key={i} style={styles.card}>
                  <p><strong>{item.decision}</strong></p>
                  <small style={styles.muted}>{item.speaker} · {item.timestamp}</small>
                </div>
              ))}
            </>
          )}

          {analysis.action_items?.length > 0 && (
            <>
              <h3>Action Items</h3>
              {analysis.action_items.map((item, i) => (
                <div key={i} style={styles.card}>
                  <p>{item.task}</p>
                  <small style={styles.muted}>
                    {item.assignee || "Unassigned"} · {item.timestamp}
                  </small>
                </div>
              ))}
            </>
          )}

          {analysis.important_points?.length > 0 && (
            <>
              <h3>Important Points</h3>
              {analysis.important_points.map((item, i) => (
                <div key={i} style={styles.card}>
                  <p>{item.point}</p>
                  <small style={styles.muted}>{item.timestamp}</small>
                </div>
              ))}
            </>
          )}
        </div>
      )}

      {/* Calendar Events */}
      <CalendarEvents meetingId={meetingId} />

      {/* AskAI */}
      <AskAI meetingId={meetingId} />
    </div>
  )
}

const styles = {
  page: { minHeight: "100vh", background: "#0a0a0a", color: "white", padding: "24px", maxWidth: "900px", margin: "0 auto" },
  center: { display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "60vh", textAlign: "center" },
  header: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" },
  backBtn: { padding: "8px 16px", borderRadius: "8px", border: "1px solid #333", background: "transparent", color: "#ccc", cursor: "pointer" },
  infoBar: { marginBottom: "24px", fontSize: "14px" },
  section: { marginBottom: "32px" },
  card: { background: "#1a1a1a", padding: "14px 18px", borderRadius: "10px", marginBottom: "10px", border: "1px solid #222" },
  fileButtons: { display: "flex", gap: "12px", flexWrap: "wrap" },
  fileBtn: { padding: "10px 20px", borderRadius: "8px", border: "none", background: "#2563eb", color: "white", cursor: "pointer", fontSize: "14px" },
  muted: { color: "#888" },
  spinner: { width: "40px", height: "40px", border: "4px solid #333", borderTop: "4px solid #3b82f6", borderRadius: "50%", animation: "spin 1s linear infinite", margin: "20px auto" }
}

export default MeetingResults

import { API_URL } from "../api"

function MeetingFiles({ meetingId }) {
  return (
    <div>
      <h2>Meeting Files</h2>
      <div style={{ display: "flex", gap: "12px" }}>
        <button
          onClick={() => window.open(`${API_URL}/meetings/${meetingId}/report`, "_blank")}
          style={{ padding: "10px 20px", borderRadius: "8px", border: "none", background: "#2563eb", color: "white", cursor: "pointer" }}
        >
          Meeting Report
        </button>
        <button
          onClick={() => window.open(`${API_URL}/meetings/${meetingId}/full-conversation`, "_blank")}
          style={{ padding: "10px 20px", borderRadius: "8px", border: "none", background: "#2563eb", color: "white", cursor: "pointer" }}
        >
          Full Conversation
        </button>
      </div>
    </div>
  )
}

export default MeetingFiles
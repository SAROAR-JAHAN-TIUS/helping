import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { API_URL } from "../../api"

function JoinMeeting() {
  const navigate = useNavigate()
  const [meetingId, setMeetingId] = useState("")
  const [loading, setLoading] = useState(false)

  const user = JSON.parse(localStorage.getItem("user"))

  const handleJoin = async () => {
    if (!meetingId.trim()) {
      alert("Enter meeting ID")
      return
    }

    if (!user?.google_id) {
      alert("Please sign in first")
      return
    }

    setLoading(true)

    try {
      const response = await fetch(
        `${API_URL}/meetings/${meetingId.trim()}/join?user_id=${encodeURIComponent(user.google_id)}`,
        { method: "POST" }
      )

      const data = await response.json()

      if (response.ok && data.success) {
        navigate(`/meeting/${meetingId.trim()}`)
      } else {
        alert(data.message || "Could not join meeting")
      }
    } catch (error) {
      console.error("Join meeting error:", error)
      alert("Could not connect to the server")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "#0a0a0a", color: "white" }}>
      <div style={{ textAlign: "center", padding: "40px", background: "#1a1a1a", borderRadius: "16px" }}>
        <h2>Join Meeting</h2>

        <input
          type="text"
          value={meetingId}
          onChange={(e) => setMeetingId(e.target.value)}
          placeholder="Enter meeting ID"
          disabled={loading}
          autoFocus
          style={{ padding: "10px", borderRadius: "8px", border: "1px solid #333", background: "#222", color: "white", width: "250px", marginBottom: "12px" }}
        />
        <br />
        <button
          onClick={handleJoin}
          disabled={loading}
          style={{ padding: "10px 24px", borderRadius: "8px", border: "none", background: "#3b82f6", color: "white", cursor: "pointer" }}
        >
          {loading ? "Joining..." : "Join Meeting"}
        </button>
      </div>
    </div>
  )
}

export default JoinMeeting
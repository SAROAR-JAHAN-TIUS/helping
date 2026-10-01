import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { API_URL } from "../api"

function Dashboard({ user, onLogout }) {
  const navigate = useNavigate()
  const [meetings, setMeetings] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchMeetingHistory()
  }, [])

  const fetchMeetingHistory = async () => {
    try {
      const response = await fetch(
        `${API_URL}/meetings/history?user_id=${encodeURIComponent(user.google_id)}`
      )
      const data = await response.json()
      if (data.success) {
        setMeetings(data.meetings)
      }
    } catch (error) {
      console.error("Failed to fetch meeting history:", error)
    } finally {
      setLoading(false)
    }
  }

  const createMeeting = async () => {
    try {
      const response = await fetch(`${API_URL}/meetings/create`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: user.google_id })
      })

      const data = await response.json()

      if (data.success) {
        navigate(`/meeting/${data.meeting.meeting_id}`)
      }
    } catch (error) {
      console.error("Create meeting error:", error)
    }
  }

  const formatDuration = (seconds) => {
    if (!seconds) return "—"
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}m ${secs}s`
  }

  const formatDate = (isoString) => {
    if (!isoString) return "—"
    return new Date(isoString).toLocaleString()
  }

  const getStatusColor = (status) => {
    const colors = {
      waiting: "#f59e0b",
      active: "#22c55e",
      ending: "#f97316",
      processing: "#3b82f6",
      completed: "#8b5cf6"
    }
    return colors[status] || "#888"
  }

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Sakkhat</h1>
          <p style={styles.welcome}>Welcome, {user.name}</p>
        </div>
        <div style={styles.headerRight}>
          {user.picture && (
            <img src={user.picture} alt="" style={styles.avatar} />
          )}
          <button onClick={onLogout} style={styles.logoutBtn}>Logout</button>
        </div>
      </div>

      <div style={styles.actions}>
        <button onClick={createMeeting} style={styles.primaryBtn}>
          + Create Meeting
        </button>
        <button onClick={() => navigate("/join")} style={styles.secondaryBtn}>
          Join Meeting
        </button>
      </div>

      <h2 style={styles.sectionTitle}>Meeting History</h2>

      {loading ? (
        <p style={styles.muted}>Loading...</p>
      ) : meetings.length === 0 ? (
        <p style={styles.muted}>No meetings yet. Create one to get started!</p>
      ) : (
        <div style={styles.meetingList}>
          {meetings.map((meeting) => (
            <div key={meeting.id} style={styles.meetingCard}>
              <div style={styles.meetingHeader}>
                <h3 style={styles.meetingTitle}>{meeting.title}</h3>
                <span style={{ ...styles.status, color: getStatusColor(meeting.status) }}>
                  {meeting.status}
                </span>
              </div>
              <p style={styles.meetingMeta}>
                {formatDate(meeting.created_at)} · {formatDuration(meeting.duration_seconds)} · {meeting.participants.length} participants
              </p>
              <p style={styles.participantNames}>
                {meeting.participants.join(", ")}
              </p>
              <div style={styles.meetingActions}>
                {meeting.status === "completed" && (
                  <button
                    onClick={() => navigate(`/meeting/${meeting.id}/results`)}
                    style={styles.viewBtn}
                  >
                    View Results
                  </button>
                )}
                {(meeting.status === "waiting" || meeting.status === "active") && (
                  <button
                    onClick={() => navigate(`/meeting/${meeting.id}`)}
                    style={styles.viewBtn}
                  >
                    Rejoin
                  </button>
                )}
                {meeting.status === "processing" && (
                  <button
                    onClick={() => navigate(`/meeting/${meeting.id}/results`)}
                    style={styles.viewBtn}
                  >
                    Processing...
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

const styles = {
  page: { minHeight: "100vh", background: "#0a0a0a", color: "white", padding: "24px", maxWidth: "900px", margin: "0 auto" },
  header: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "32px" },
  headerRight: { display: "flex", alignItems: "center", gap: "12px" },
  title: { margin: 0 },
  welcome: { color: "#888", margin: "4px 0 0" },
  avatar: { width: "36px", height: "36px", borderRadius: "50%" },
  logoutBtn: { padding: "8px 16px", borderRadius: "8px", border: "1px solid #333", background: "transparent", color: "#ccc", cursor: "pointer" },
  actions: { display: "flex", gap: "12px", marginBottom: "32px" },
  primaryBtn: { padding: "12px 24px", borderRadius: "8px", border: "none", background: "#3b82f6", color: "white", cursor: "pointer", fontSize: "15px", fontWeight: "600" },
  secondaryBtn: { padding: "12px 24px", borderRadius: "8px", border: "1px solid #333", background: "transparent", color: "#ccc", cursor: "pointer", fontSize: "15px" },
  sectionTitle: { marginBottom: "16px", color: "#ccc" },
  muted: { color: "#666" },
  meetingList: { display: "flex", flexDirection: "column", gap: "12px" },
  meetingCard: { background: "#1a1a1a", borderRadius: "12px", padding: "16px 20px", border: "1px solid #222" },
  meetingHeader: { display: "flex", justifyContent: "space-between", alignItems: "center" },
  meetingTitle: { margin: 0, fontSize: "16px" },
  status: { fontSize: "13px", fontWeight: "600", textTransform: "uppercase" },
  meetingMeta: { color: "#888", fontSize: "13px", margin: "6px 0 2px" },
  participantNames: { color: "#666", fontSize: "12px", margin: "0 0 8px" },
  meetingActions: { display: "flex", gap: "8px" },
  viewBtn: { padding: "6px 14px", borderRadius: "6px", border: "none", background: "#2563eb", color: "white", cursor: "pointer", fontSize: "13px" }
}

export default Dashboard
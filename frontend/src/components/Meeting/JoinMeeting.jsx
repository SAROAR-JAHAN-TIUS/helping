import { useState } from "react"
import { useNavigate } from "react-router-dom"

function JoinMeeting() {
  const navigate = useNavigate()

  const [meetingId, setMeetingId] = useState("")
  const [loading, setLoading] = useState(false)

  const user = JSON.parse(
    localStorage.getItem("user")
  )

  const handleJoin = async () => {
    if (!meetingId.trim()) {
      alert("Enter meeting ID")
      return
    }

    if (!user) {
      alert("Please sign in first")
      return
    }

    if (!user.google_id) {
      console.error("User does not have google_id:", user)
      alert("User information is incomplete. Please sign in again.")
      return
    }

    setLoading(true)

    try {
      console.log("Meeting ID:", meetingId)
      console.log("User:", user)
      console.log("Google ID:", user.google_id)

      const response = await fetch(
        `http://127.0.0.1:8000/meetings/${meetingId.trim()}/join?user_id=${encodeURIComponent(user.google_id)}`,
        {
          method: "POST"
        }
      )

      console.log("HTTP status:", response.status)

      const data = await response.json()

      console.log("Join response:", data)

      if (response.ok && data.success) {
        console.log("Successfully joined meeting")

        navigate(`/meeting/${meetingId.trim()}`)
      } else {
        alert(
          data.message || "Could not join meeting"
        )
      }

    } catch (error) {
      console.error("Join meeting error:", error)
      alert("Could not connect to the server")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="join-meeting">

      <h2>Join Meeting</h2>

      <input
        type="text"
        value={meetingId}
        onChange={(e) => setMeetingId(e.target.value)}
        placeholder="Enter meeting ID"
        disabled={loading}
        autoFocus
      />

      <button
        onClick={handleJoin}
        disabled={loading}
      >
        {loading ? "Joining..." : "Join Meeting"}
      </button>

    </div>
  )
}

export default JoinMeeting
import { useEffect, useState } from "react"
import { API_URL } from "../api"

function CalendarEvents({ meetingId }) {
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${API_URL}/meetings/${meetingId}/calendar-events`)
      .then((r) => r.json())
      .then((data) => {
        setEvents(data.events || [])
        setLoading(false)
      })
      .catch((error) => {
        console.error("Failed to load calendar events:", error)
        setLoading(false)
      })
  }, [meetingId])

  if (loading) return <p style={{ color: "#888" }}>Loading events...</p>
  if (events.length === 0) return null

  return (
    <div style={{ marginBottom: "32px" }}>
      <h2>Calendar Events</h2>
      {events.map((event, index) => (
        <div key={index} style={{ background: "#1a1a1a", padding: "14px 18px", borderRadius: "10px", marginBottom: "10px", border: "1px solid #222" }}>
          <h3 style={{ margin: "0 0 4px" }}>{event.title}</h3>
          <p style={{ margin: "4px 0", color: "#ccc" }}>{event.description}</p>
          <p style={{ margin: "4px 0", color: "#888", fontSize: "13px" }}>
            {event.start_time} → {event.end_time}
          </p>
          <button
            onClick={async () => {
              try {
                const response = await fetch(
                  `${API_URL}/meetings/${meetingId}/calendar-events/${index}/confirm`,
                  { method: "POST" }
                )
                const data = await response.json()
                if (data.success) {
                  window.open(data.event, "_blank")
                } else {
                  alert(data.message)
                }
              } catch (error) {
                console.error("Calendar error:", error)
              }
            }}
            style={{ padding: "8px 16px", borderRadius: "6px", border: "none", background: "#2563eb", color: "white", cursor: "pointer", fontSize: "13px" }}
          >
            Add to Google Calendar
          </button>
        </div>
      ))}
    </div>
  )
}

export default CalendarEvents
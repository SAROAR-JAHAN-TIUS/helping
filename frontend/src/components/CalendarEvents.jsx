import { useEffect, useState } from "react"

function CalendarEvents() {
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch("http://127.0.0.1:8000/calendar-events")
      .then(response => response.json())
      .then(data => {
        setEvents(data.events || [])
        setLoading(false)
      })
      .catch(error => {
        console.error("Failed to load calendar events:", error)
        setLoading(false)
      })
  }, [])

  if (loading) {
    return <p>Loading events...</p>
  }

  if (events.length === 0) {
    return (
      <section>
        <h2>Calendar Events</h2>
        <p>No events found in this meeting.</p>
      </section>
    )
  }

  return (
    <section>
      <h2>Calendar Events</h2>

      {events.map((event, index) => (
        <div key={index}>
          <h3>{event.title}</h3>

          <p>{event.description}</p>

          <p>
            {event.start_time} → {event.end_time}
          </p>
<button
  onClick={async () => {
    try {
      const response = await fetch(
        `http://127.0.0.1:8000/create-calendar-event/${index}/confirm`,
        {
          method: "POST"
        }
      )

      const data = await response.json()

      console.log("Calendar response:", data)

      if (data.success) {
        window.open(data.event, "_blank")
      } else {
        alert(data.message)
      }

    } catch (error) {
      console.error("Calendar error:", error)
    }
  }}
>
  Add to Google Calendar
</button>
        </div>
      ))}
    </section>
  )
}

export default CalendarEvents
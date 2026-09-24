function MeetingFiles() {
  return (
    <section>
      <h2>Meeting Files</h2>

      <button
        onClick={() =>
          window.open(
            "http://127.0.0.1:8000/meeting/report",
            "_blank"
          )
        }
      >
        View Meeting Report
      </button>

      <button
        onClick={() =>
          window.open(
            "http://127.0.0.1:8000/meeting/full-conversation",
            "_blank"
          )
        }
      >
        View Full Conversation
      </button>
    </section>
  )
}

export default MeetingFiles
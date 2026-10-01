function MeetingDashboard({ analysis }) {
  if (!analysis) return null

  return (
    <div>
      <h2>Meeting Summary</h2>
      <p>{analysis.summary}</p>
    </div>
  )
}

export default MeetingDashboard
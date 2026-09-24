import AskAI from "./AskAI"
function MeetingDashboard({analysis}) {
return (
    <section >
       <h2>Meeting Summary</h2>
        <p>{analysis.summary}</p>
  <br />
    <h2>
        Key Discussions
    </h2>
{analysis.key_discussions.map((item, index) => (
        <div key={index}>
            <h3>{item.topic}</h3>
            <p>{item.discussion}</p>
            <small>Timestamp: {item.timestamp}</small>
        </div>
    ))}
    <h2>
        Decisions
    </h2>
  {analysis.decisions.map((item, index) => (
  <div key={index}>
    <h3>{item.decision}</h3>
    <small>
      {item.speaker} · {item.timestamp}
    </small>
  </div>
))}
<h2>Action Items</h2>
      {analysis.action_items.map((item, index) => (
        <div key={index}>
          <p>{item.task}</p>
          <small>
            {item.assignee || "Unassigned"} · {item.timestamp}
          </small>
        </div>
      ))}
      <h2>Important Points</h2>
      {analysis.important_points.map((item, index) => (
        <div key={index}>
          <p>{item.point}</p>
          <small>{item.timestamp}</small>
        </div>
      ))}
<AskAI />

      </section>
      
)
}


export default MeetingDashboard
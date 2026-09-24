import { useNavigate } from "react-router-dom"
function Dashboard({ user , onLogout }) {
    const navigate = useNavigate()
    const createMeeting = async () => {
      console.log("Current user:", user)
console.log("User ID:", user?.id)
  const response = await fetch(
    "http://127.0.0.1:8000/meetings/create",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
  user_id: user.google_id
})
    }
  )

  const data = await response.json()
  console.log("Create meeting response:", data)
if (data.success) {
 const meetingId = data.meeting.meeting_id
  navigate(`/meeting/${meetingId}`)
}
  console.log("Created meeting:", data)
}
  return (
    <div>
      <h1>Meeting AI</h1>

      <h2>Welcome, {user.name}</h2>
{/* 
      <p>{user.email}</p> */}
<div>
      <button onClick={createMeeting}>
        Create Meeting
        
      </button>
</div>

<br/>
<div>
     <button onClick={() => navigate("/join")}>
  Join Meeting
</button>
      </div>
      <br/>
      <div><button onClick={onLogout}>
  Logout
</button></div>
    </div>
  )
}

export default Dashboard
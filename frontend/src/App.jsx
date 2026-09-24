import { useState } from "react"
import { Routes, Route, Navigate } from "react-router-dom"

import MeetingRoom from "./components/Meeting/MeetingRoom"
import Login from "./components/Auth/Login"
import Register from "./components/Auth/Register"
import Dashboard from "./components/Dashboard"
import JoinMeeting from "./components/Meeting/JoinMeeting"

function App() {

  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem("user")

    return savedUser ? JSON.parse(savedUser) : null
  })

  const handleLogin = (userData) => {
    localStorage.setItem(
      "user",
      JSON.stringify(userData)
    )

    setUser(userData)
  }

  const handleLogout = () => {
    localStorage.removeItem("user")
    setUser(null)
  }

  return (
    <Routes>

   
      <Route
        path="/"
        element={
          user ? (
            <Navigate to="/dashboard" replace />
          ) : (
            <Login
              onLogin={handleLogin}
              onRegister={() => {
                window.location.href = "/register"
              }}
            />
          )
        }
      />

      <Route
        path="/register"
        element={
          <Register
            onRegister={handleLogin}
            onLogin={() => {
              window.location.href = "/"
            }}
          />
        }
      />


      <Route
        path="/dashboard"
        element={
          user ? (
            <Dashboard
              user={user}
              onLogout={handleLogout}
            />
          ) : (
            <Navigate to="/" replace />
          )
        }
      />

      <Route
        path="/join"
        element={
          user ? (
            <JoinMeeting />
          ) : (
            <Navigate to="/" replace />
          )
        }
      />

      <Route
        path="/meeting/:meetingId"
        element={
          user ? (
            <MeetingRoom />
          ) : (
            <Navigate to="/" replace />
          )
        }
      />

      <Route
        path="*"
        element={<Navigate to="/" replace />}
      />

    </Routes>
  )
}

export default App
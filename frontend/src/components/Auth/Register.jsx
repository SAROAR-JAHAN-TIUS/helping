import { useState } from "react"
import { GoogleLogin } from "@react-oauth/google"

function Register({ onRegister, onLogin }) {
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [error, setError] = useState("")

  const handleEmailRegister = (e) => {
    e.preventDefault()
    setError("")

    if (!email.trim() || !password) {
      setError("Please fill out all required fields.")
      return
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.")
      return
    }

    onRegister({
      name: name.trim() || email.split("@")[0],
      email: email.trim(),
      password: password
    })
  }

  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "#0a0a0a", color: "white" }}>
      <div style={{ textAlign: "center", padding: "40px", background: "#1a1a1a", borderRadius: "16px" }}>
        <h1>Sakkhat</h1>
        <h2>Create an account</h2>

        <GoogleLogin
          text="signup_with"
          onSuccess={(credentialResponse) => {
            onRegister({ googleCredential: credentialResponse.credential })
          }}
          onError={() => {
            setError("Google sign-up failed.")
          }}
        />

        <p>— OR —</p>

        <form onSubmit={handleEmailRegister} autoComplete="off">
          {error && <p style={{ color: "#ff6b6b" }}>{error}</p>}
          <div><input type="text" placeholder="Full Name" value={name} onChange={(e) => setName(e.target.value)} style={{ padding: "8px", margin: "4px", borderRadius: "6px", border: "1px solid #333", background: "#222", color: "white" }} /></div>
          <div><input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required style={{ padding: "8px", margin: "4px", borderRadius: "6px", border: "1px solid #333", background: "#222", color: "white" }} /></div>
          <div><input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="new-password" required style={{ padding: "8px", margin: "4px", borderRadius: "6px", border: "1px solid #333", background: "#222", color: "white" }} /></div>
          <div><input type="password" placeholder="Confirm Password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} autoComplete="new-password" required style={{ padding: "8px", margin: "4px", borderRadius: "6px", border: "1px solid #333", background: "#222", color: "white" }} /></div>
          <div><button type="submit" style={{ padding: "10px 20px", margin: "8px", borderRadius: "6px", border: "none", background: "#3b82f6", color: "white", cursor: "pointer" }}>Create account</button></div>
        </form>

        <div>
          <span>Already have an account? </span>
          <button type="button" onClick={onLogin} style={{ background: "none", border: "none", color: "#3b82f6", cursor: "pointer" }}>Sign in</button>
        </div>
      </div>
    </div>
  )
}

export default Register
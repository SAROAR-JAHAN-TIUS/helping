import { useState } from "react"
import { GoogleLogin } from "@react-oauth/google"

function Register({ onRegisterSuccess, onBackToLogin }) {
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

    onRegisterSuccess({
      name: name.trim() || email.split("@")[0],
      email: email.trim(),
      password: password
    })
  }

  return (
    <div>
      <h1>Meeting AI</h1>
      <h2>Create an account</h2>

      {/* Google Sign-Up */}
      

      <p>— OR —</p>

      {/* Standard Email & Password Form */}
      <form onSubmit={handleEmailRegister} autoComplete="off">
        {error && <p style={{ color: "red" }}>{error}</p>}

        <div>
          <input
            type="text"
            placeholder="Full Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </div>

        <div>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>

        <div>
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="new-password"
            required
          />
        </div>

        <div>
          <input
            type="password"
            placeholder="Confirm Password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            autoComplete="new-password"
            required
          />
        </div>

        <div>
          <button type="submit">Create account</button>
        </div>
      </form>

      <br />
<div>
        <GoogleLogin
          text="signup_with"
          onSuccess={(credentialResponse) => {
            onRegisterSuccess({
              googleCredential: credentialResponse.credential
            })
          }}
          onError={() => {
            setError("Google sign-up failed. Please try again.")
          }}
        />
      </div>
      <br/>
      <div>
        <span>Already have an account? </span>
        <button type="button" onClick={onBackToLogin}>
          Sign in
        </button>
      </div>
    </div>
  )
}

export default Register
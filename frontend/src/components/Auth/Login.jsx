import { GoogleLogin } from "@react-oauth/google"

function Login({ onLogin, onRegister }) {
  return (
    <div>
      <h1>Meeting AI</h1>

      <h2>Sign in</h2>

    <GoogleLogin
  onSuccess={async (credentialResponse) => {
    console.log("Google login successful")

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/auth/google",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            credential: credentialResponse.credential
          })
        }
      )

      const data = await response.json()
console.log(
  "Backend response:",
  JSON.stringify(data, null, 2)
)
if (data.success) {
  localStorage.setItem(
    "user",
    JSON.stringify(data.user)
  )

  onLogin(data.user)
}else {
        console.error(data.message)
      }

    } catch (error) {
      console.error("Backend error:", error)
    }
  }}

  onError={() => {
    console.log("Google login failed")
  }}
/>

      <br />

      <button onClick={onRegister}>
        Create account
      </button>
    </div>
  )
}

export default Login
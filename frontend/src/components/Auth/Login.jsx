import { GoogleLogin } from "@react-oauth/google"
import { API_URL } from "../../api"

function Login({ onLogin }) {
  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <h1 style={styles.title}>Sakkhat</h1>
        <p style={styles.subtitle}>Meeting AI</p>

        <GoogleLogin
          onSuccess={async (credentialResponse) => {
            try {
              const response = await fetch(`${API_URL}/auth/google`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  credential: credentialResponse.credential
                })
              })

              const data = await response.json()

              if (data.success) {
                onLogin(data.user)
              } else {
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
      </div>
    </div>
  )
}

const styles = {
  page: {
    minHeight: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background: "#0a0a0a",
    color: "white"
  },
  card: {
    textAlign: "center",
    padding: "40px",
    background: "#1a1a1a",
    borderRadius: "16px",
    boxShadow: "0 4px 20px rgba(0,0,0,0.5)"
  },
  title: {
    fontSize: "32px",
    margin: "0 0 4px 0"
  },
  subtitle: {
    color: "#888",
    margin: "0 0 24px 0"
  }
}

export default Login
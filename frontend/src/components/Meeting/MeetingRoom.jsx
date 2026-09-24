import { useEffect, useRef, useState } from "react"
import { useParams, useNavigate } from "react-router-dom"

function MeetingRoom() {
  const { meetingId } = useParams()
  const navigate = useNavigate()

  // -----------------------------
  // Refs
  // -----------------------------

  const videoRef = useRef(null)
  const remoteVideoRef = useRef(null)

  const streamRef = useRef(null)
  const socketRef = useRef(null)
  const peerConnectionRef = useRef(null)

  const remoteUserIdRef = useRef(null)
  const pendingIceCandidatesRef = useRef([])

  // -----------------------------
  // State
  // -----------------------------

  const [cameraOn, setCameraOn] = useState(true)
  const [micOn, setMicOn] = useState(true)
  const [mediaError, setMediaError] = useState("")
  const [connectionStatus, setConnectionStatus] =
    useState("Connecting...")

  // -----------------------------
  // Current user
  // -----------------------------

  const user = JSON.parse(
    localStorage.getItem("user")
  )

  // -----------------------------
  // WebRTC configuration
  // -----------------------------

  const rtcConfig = {
    iceServers: [
      {
        urls: "stun:stun.l.google.com:19302"
      }
    ]
  }

  // =========================================================
  // CREATE PEER CONNECTION
  // =========================================================

  const createPeerConnection = () => {
    console.log("Creating peer connection")

    const peerConnection =
      new RTCPeerConnection(rtcConfig)

    peerConnectionRef.current = peerConnection

    // -----------------------------------------
    // Send ICE candidates through WebSocket
    // -----------------------------------------

    peerConnection.onicecandidate = (event) => {
      if (!event.candidate) {
        return
      }

      console.log("Sending ICE candidate")

      if (
        socketRef.current &&
        socketRef.current.readyState === WebSocket.OPEN
      ) {
        socketRef.current.send(
          JSON.stringify({
            type: "ice-candidate",
            candidate: event.candidate
          })
        )
      }
    }

    // -----------------------------------------
    // Receive remote audio/video
    // -----------------------------------------

    peerConnection.ontrack = (event) => {
      console.log("Remote track received")

      if (
        remoteVideoRef.current &&
        event.streams[0]
      ) {
        remoteVideoRef.current.srcObject =
          event.streams[0]

        setConnectionStatus("Connected")
      }
    }

    // -----------------------------------------
    // Connection state
    // -----------------------------------------

    peerConnection.onconnectionstatechange = () => {
      console.log(
        "WebRTC connection state:",
        peerConnection.connectionState
      )

      if (
        peerConnection.connectionState ===
        "connected"
      ) {
        setConnectionStatus("Connected")
      }

      if (
        peerConnection.connectionState ===
        "connecting"
      ) {
        setConnectionStatus("Connecting...")
      }

      if (
        peerConnection.connectionState ===
        "disconnected"
      ) {
        setConnectionStatus(
          "Participant disconnected"
        )
      }

      if (
        peerConnection.connectionState ===
        "failed"
      ) {
        setConnectionStatus(
          "Connection failed"
        )
      }
    }

    // -----------------------------------------
    // Add local camera + microphone
    // -----------------------------------------

    if (streamRef.current) {
      streamRef.current
        .getTracks()
        .forEach((track) => {
          peerConnection.addTrack(
            track,
            streamRef.current
          )
        })
    }

    return peerConnection
  }

  // =========================================================
  // CREATE OFFER
  // =========================================================

  const createOffer = async () => {
    try {
      console.log("Creating offer")

      if (!streamRef.current) {
        console.log(
          "Local stream not ready"
        )
        return
      }

      const peerConnection =
        peerConnectionRef.current ||
        createPeerConnection()

      const offer =
        await peerConnection.createOffer()

      await peerConnection.setLocalDescription(
        offer
      )

      if (
        socketRef.current &&
        socketRef.current.readyState ===
          WebSocket.OPEN
      ) {
        socketRef.current.send(
          JSON.stringify({
            type: "offer",
            offer
          })
        )

        console.log("Offer sent")
      }

    } catch (error) {
      console.error(
        "Create offer error:",
        error
      )
    }
  }

  // =========================================================
  // HANDLE OFFER
  // =========================================================

  const handleOffer = async (offer) => {
    try {
      console.log("Offer received")

      const peerConnection =
        peerConnectionRef.current ||
        createPeerConnection()

      await peerConnection.setRemoteDescription(
        new RTCSessionDescription(offer)
      )

      // Add queued ICE candidates
      for (
        const candidate of
        pendingIceCandidatesRef.current
      ) {
        try {
          await peerConnection.addIceCandidate(
            new RTCIceCandidate(candidate)
          )
        } catch (error) {
          console.error(
            "Queued ICE error:",
            error
          )
        }
      }

      pendingIceCandidatesRef.current = []

      const answer =
        await peerConnection.createAnswer()

      await peerConnection.setLocalDescription(
        answer
      )

      if (
        socketRef.current &&
        socketRef.current.readyState ===
          WebSocket.OPEN
      ) {
        socketRef.current.send(
          JSON.stringify({
            type: "answer",
            answer
          })
        )

        console.log("Answer sent")
      }

    } catch (error) {
      console.error(
        "Handle offer error:",
        error
      )
    }
  }

  // =========================================================
  // HANDLE ANSWER
  // =========================================================

  const handleAnswer = async (answer) => {
    try {
      console.log("Answer received")

      if (!peerConnectionRef.current) {
        console.log(
          "No peer connection available"
        )
        return
      }

      await peerConnectionRef.current.setRemoteDescription(
        new RTCSessionDescription(answer)
      )

      // Add queued ICE candidates
      for (
        const candidate of
        pendingIceCandidatesRef.current
      ) {
        try {
          await peerConnectionRef.current.addIceCandidate(
            new RTCIceCandidate(candidate)
          )
        } catch (error) {
          console.error(
            "Queued ICE error:",
            error
          )
        }
      }

      pendingIceCandidatesRef.current = []

    } catch (error) {
      console.error(
        "Handle answer error:",
        error
      )
    }
  }

  // =========================================================
  // HANDLE ICE CANDIDATE
  // =========================================================

  const handleIceCandidate = async (
    candidate
  ) => {
    try {
      if (!peerConnectionRef.current) {
        pendingIceCandidatesRef.current.push(
          candidate
        )

        return
      }

      if (
        !peerConnectionRef.current.remoteDescription
      ) {
        pendingIceCandidatesRef.current.push(
          candidate
        )

        return
      }

      await peerConnectionRef.current.addIceCandidate(
        new RTCIceCandidate(candidate)
      )

    } catch (error) {
      console.error(
        "ICE candidate error:",
        error
      )
    }
  }

  // =========================================================
  // WEBSOCKET SIGNALING
  // =========================================================

  useEffect(() => {
    if (!user?.google_id) {
      console.error(
        "No logged-in user found"
      )
      return
    }

    const socket = new WebSocket(
      `ws://127.0.0.1:8000/ws/meeting/${meetingId}`
    )

    socketRef.current = socket

    socket.onopen = () => {
      console.log(
        "WebSocket connected"
      )

      setConnectionStatus(
        "Waiting for participant..."
      )

      // Tell other participants who we are
      socket.send(
        JSON.stringify({
          type: "hello",
          user_id: user.google_id,
          name: user.name
        })
      )
    }

    socket.onmessage = async (event) => {
      try {
        const message =
          JSON.parse(event.data)

        console.log(
          "Signaling message:",
          message
        )

        // -------------------------------------
        // Another participant joined
        // -------------------------------------

        if (
          message.type === "hello"
        ) {
          if (
            message.user_id ===
            user.google_id
          ) {
            return
          }

          console.log(
            "Other participant:",
            message.user_id
          )

          remoteUserIdRef.current =
            message.user_id

          setConnectionStatus(
            "Participant joined"
          )

          /*
           * Deterministic caller selection.
           *
           * The user with the smaller Google ID
           * creates the offer.
           *
           * This prevents both users from
           * creating an offer simultaneously.
           */

          if (
            String(user.google_id) <
            String(message.user_id)
          ) {
            console.log(
              "I am the caller"
            )

            setTimeout(() => {
              createOffer()
            }, 300)
          } else {
            console.log(
              "I am the receiver"
            )
          }

          return
        }

        // -------------------------------------
        // Offer
        // -------------------------------------

        if (
          message.type === "offer"
        ) {
          await handleOffer(
            message.offer
          )

          return
        }

        // -------------------------------------
        // Answer
        // -------------------------------------

        if (
          message.type === "answer"
        ) {
          await handleAnswer(
            message.answer
          )

          return
        }

        // -------------------------------------
        // ICE candidate
        // -------------------------------------

        if (
          message.type ===
          "ice-candidate"
        ) {
          await handleIceCandidate(
            message.candidate
          )

          return
        }

      } catch (error) {
        console.error(
          "WebSocket message error:",
          error
        )
      }
    }

    socket.onerror = (error) => {
      console.error(
        "WebSocket error:",
        error
      )

      setConnectionStatus(
        "WebSocket error"
      )
    }

    socket.onclose = () => {
      console.log(
        "WebSocket disconnected"
      )

      setConnectionStatus(
        "Disconnected"
      )
    }

    return () => {
      console.log(
        "Closing WebSocket"
      )

      socket.close()

      socketRef.current = null
    }

  }, [meetingId])

  // =========================================================
  // CAMERA + MICROPHONE
  // =========================================================

  useEffect(() => {
    let mounted = true

    const startMedia = async () => {
      try {
        console.log(
          "Requesting camera and microphone..."
        )

        const stream =
          await navigator.mediaDevices.getUserMedia(
            {
              video: true,
              audio: true
            }
          )

        if (!mounted) {
          stream
            .getTracks()
            .forEach((track) =>
              track.stop()
            )

          return
        }

        streamRef.current = stream

        if (videoRef.current) {
          videoRef.current.srcObject =
            stream
        }

        console.log(
          "Camera and microphone started"
        )

      } catch (error) {
        console.error(
          "Camera/microphone error:",
          error
        )

        setMediaError(
          "Could not access camera or microphone. Please allow permission."
        )
      }
    }

    startMedia()

    return () => {
      mounted = false

      if (streamRef.current) {
        streamRef.current
          .getTracks()
          .forEach((track) =>
            track.stop()
          )

        streamRef.current = null
      }
    }

  }, [])

  // =========================================================
  // CAMERA TOGGLE
  // =========================================================

  const toggleCamera = () => {
    if (!streamRef.current) {
      return
    }

    const videoTracks =
      streamRef.current.getVideoTracks()

    videoTracks.forEach((track) => {
      track.enabled = !track.enabled
    })

    setCameraOn((previous) => !previous)
  }

  // =========================================================
  // MICROPHONE TOGGLE
  // =========================================================

  const toggleMic = () => {
    if (!streamRef.current) {
      return
    }

    const audioTracks =
      streamRef.current.getAudioTracks()

    audioTracks.forEach((track) => {
      track.enabled = !track.enabled
    })

    setMicOn((previous) => !previous)
  }

  // =========================================================
  // STOP MEDIA
  // =========================================================

  const stopMedia = () => {
    if (streamRef.current) {
      streamRef.current
        .getTracks()
        .forEach((track) =>
          track.stop()
        )

      streamRef.current = null
    }

    if (peerConnectionRef.current) {
      peerConnectionRef.current.close()

      peerConnectionRef.current = null
    }

    if (remoteVideoRef.current) {
      remoteVideoRef.current.srcObject =
        null
    }
  }

  // =========================================================
  // LEAVE MEETING
  // =========================================================

  const handleLeave = async () => {
    if (!user?.google_id) {
      alert(
        "Please sign in again"
      )

      return
    }

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/meetings/${meetingId}/leave?user_id=${encodeURIComponent(
          user.google_id
        )}`,
        {
          method: "POST"
        }
      )

      const data =
        await response.json()

      console.log(
        "Leave response:",
        data
      )

      if (
        response.ok &&
        data.success
      ) {
        stopMedia()

        navigate(
          "/dashboard",
          {
            replace: true
          }
        )
      } else {
        alert(
          data.message ||
            "Could not leave meeting"
        )
      }

    } catch (error) {
      console.error(
        "Leave meeting error:",
        error
      )

      alert(
        "Could not connect to server"
      )
    }
  }

  // =========================================================
  // END MEETING
  // =========================================================

  const handleEnd = async () => {
    if (!user?.google_id) {
      alert(
        "Please sign in again"
      )

      return
    }

    const confirmed =
      window.confirm(
        "Are you sure you want to end this meeting?"
      )

    if (!confirmed) {
      return
    }

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/meetings/${meetingId}/end?user_id=${encodeURIComponent(
          user.google_id
        )}`,
        {
          method: "POST"
        }
      )

      const data =
        await response.json()

      console.log(
        "End response:",
        data
      )

      if (
        response.ok &&
        data.success
      ) {
        stopMedia()

        navigate(
          "/dashboard",
          {
            replace: true
          }
        )
      } else {
        alert(
          data.message ||
            "Could not end meeting"
        )
      }

    } catch (error) {
      console.error(
        "End meeting error:",
        error
      )

      alert(
        "Could not connect to server"
      )
    }
  }

  // =========================================================
  // UI
  // =========================================================

  return (
    <div style={styles.page}>

      {/* HEADER */}
      <div style={styles.header}>

        <div>
          <h1 style={styles.title}>
            Meeting Room
          </h1>

          <p style={styles.meetingId}>
            Meeting ID:{" "}
            <strong>
              {meetingId}
            </strong>
          </p>

          <p style={styles.status}>
            Status:{" "}
            <strong>
              {connectionStatus}
            </strong>
          </p>
        </div>

        <div style={styles.user}>

          {user?.picture && (
            <img
              src={user.picture}
              alt="Profile"
              style={styles.avatar}
            />
          )}

          <span>
            {user?.name ||
              "Guest"}
          </span>

        </div>

      </div>

      {/* ERROR */}
      {mediaError && (
        <div style={styles.error}>
          {mediaError}
        </div>
      )}

      {/* VIDEO AREA */}
      <div style={styles.videoArea}>

        {/* LOCAL VIDEO */}

        <div style={styles.videoContainer}>

          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            style={{
              ...styles.video,
              display: cameraOn
                ? "block"
                : "none"
            }}
          />

          {!cameraOn && (
            <div style={styles.cameraOff}>

              <div
                style={styles.bigAvatar}
              >
                {user?.name
                  ?.charAt(0)
                  ?.toUpperCase() ||
                  "U"}
              </div>

              <p>
                Camera is off
              </p>

            </div>
          )}

          <div style={styles.nameLabel}>
            {user?.name ||
              "You"}
          </div>

        </div>

        {/* REMOTE VIDEO */}

        <div style={styles.videoContainer}>

          <video
            ref={remoteVideoRef}
            autoPlay
            playsInline
            style={styles.video}
          />

          {!remoteVideoRef.current?.srcObject && (
            <div style={styles.waiting}>

              <div
                style={
                  styles.bigAvatar
                }
              >
                ?
              </div>

              <h2>
                Waiting for participant
              </h2>

              <p>
                Share this meeting ID:
              </p>

              <strong>
                {meetingId}
              </strong>

            </div>
          )}

          <div style={styles.nameLabel}>
            Participant
          </div>

        </div>

      </div>

      {/* CONTROLS */}

      <div style={styles.controls}>

        <button
          onClick={toggleMic}
          style={styles.controlButton}
        >
          {micOn
            ? "🎤 Mute"
            : "🔇 Unmute"}
        </button>

        <button
          onClick={toggleCamera}
          style={styles.controlButton}
        >
          {cameraOn
            ? "📹 Camera Off"
            : "📹 Camera On"}
        </button>

        <button
          onClick={handleLeave}
          style={styles.leaveButton}
        >
          Leave
        </button>

        <button
          onClick={handleEnd}
          style={styles.endButton}
        >
          End Meeting
        </button>

      </div>

    </div>
  )
}

// =========================================================
// STYLES
// =========================================================

const styles = {

  page: {
    minHeight: "100vh",
    background: "#111",
    color: "white",
    padding: "20px",
    boxSizing: "border-box"
  },

  header: {
    display: "flex",
    justifyContent:
      "space-between",
    alignItems: "center",
    marginBottom: "20px"
  },

  title: {
    margin: 0
  },

  meetingId: {
    color: "#aaa"
  },

  status: {
    color: "#aaa"
  },

  user: {
    display: "flex",
    alignItems: "center",
    gap: "10px"
  },

  avatar: {
    width: "40px",
    height: "40px",
    borderRadius: "50%"
  },

  error: {
    background: "#5c2020",
    padding: "12px",
    borderRadius: "8px",
    marginBottom: "15px"
  },

  videoArea: {
    display: "grid",
    gridTemplateColumns:
      "1fr 1fr",
    gap: "20px",
    minHeight: "65vh"
  },

  videoContainer: {
    position: "relative",
    background: "#222",
    borderRadius: "12px",
    overflow: "hidden",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    minHeight: "400px"
  },

  video: {
    width: "100%",
    height: "100%",
    objectFit: "cover"
  },

  cameraOff: {
    textAlign: "center"
  },

  bigAvatar: {
    width: "100px",
    height: "100px",
    borderRadius: "50%",
    background: "#444",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "40px",
    margin: "auto"
  },

  waiting: {
    position: "absolute",
    textAlign: "center",
    padding: "20px"
  },

  nameLabel: {
    position: "absolute",
    bottom: "10px",
    left: "10px",
    background:
      "rgba(0,0,0,.6)",
    padding: "6px 10px",
    borderRadius: "6px"
  },

  controls: {
    display: "flex",
    justifyContent:
      "center",
    gap: "12px",
    marginTop: "20px",
    flexWrap: "wrap"
  },

  controlButton: {
    padding: "12px 18px",
    border: "none",
    borderRadius: "8px",
    cursor: "pointer"
  },

  leaveButton: {
    padding: "12px 18px",
    border: "none",
    borderRadius: "8px",
    cursor: "pointer",
    background: "#555",
    color: "white"
  },

  endButton: {
    padding: "12px 18px",
    border: "none",
    borderRadius: "8px",
    cursor: "pointer",
    background: "#c62828",
    color: "white"
  }
}

export default MeetingRoom
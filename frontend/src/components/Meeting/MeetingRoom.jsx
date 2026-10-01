import { useEffect, useEffectEvent, useRef, useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { API_URL, WS_URL } from "../../api"

function MeetingRoom({ user }) {
  const { meetingId } = useParams()
  const navigate = useNavigate()

  const videoRef = useRef(null)
  const streamRef = useRef(null)
  const socketRef = useRef(null)
  const peerConnectionsRef = useRef({})
  const pendingIceCandidatesRef = useRef({})
  const pendingOffersRef = useRef({})
  const audioContextRef = useRef(null)
  const audioProcessorRef = useRef(null)
  const audioSourceRef = useRef(null)
  const streamReadyRef = useRef(false)

  const [cameraOn, setCameraOn] = useState(true)
  const [micOn, setMicOn] = useState(true)
  const [mediaError, setMediaError] = useState("")
  const [connectionStatus, setConnectionStatus] = useState("Connecting...")
  const [participants, setParticipants] = useState([])
  const [meetingState, setMeetingState] = useState("active")

  const rtcConfig = {
    iceServers: [
      { urls: "stun:stun.l.google.com:19302" },
      { urls: "stun:stun1.l.google.com:19302" }
    ]
  }

  // =========================================================
  // AUDIO STREAMING
  // =========================================================

  const startAudioStreaming = (stream) => {
    if (!socketRef.current) return

    const audioTrack = stream.getAudioTracks()[0]
    if (!audioTrack) return

    const audioStream = new MediaStream([audioTrack])
    const audioContext = new AudioContext({ sampleRate: 16000 })
    audioContextRef.current = audioContext

    const source = audioContext.createMediaStreamSource(audioStream)
    audioSourceRef.current = source

    const processor = audioContext.createScriptProcessor(4096, 1, 1)
    audioProcessorRef.current = processor

    processor.onaudioprocess = (event) => {
      if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) return

      const input = event.inputBuffer.getChannelData(0)
      const pcm = new Int16Array(input.length)

      for (let i = 0; i < input.length; i++) {
        const sample = Math.max(-1, Math.min(1, input[i]))
        pcm[i] = sample < 0 ? sample * 0x8000 : sample * 0x7fff
      }

      try {
        socketRef.current.send(pcm.buffer)
      } catch (e) {
        // WebSocket may be closing
      }
    }

    source.connect(processor)
    processor.connect(audioContext.destination)
  }

  const stopAudioStreaming = () => {
    if (audioProcessorRef.current) {
      audioProcessorRef.current.disconnect()
      audioProcessorRef.current = null
    }
    if (audioSourceRef.current) {
      audioSourceRef.current.disconnect()
      audioSourceRef.current = null
    }
    if (audioContextRef.current) {
      audioContextRef.current.close()
      audioContextRef.current = null
    }
  }

  // =========================================================
  // SEND SIGNALING MESSAGE
  // =========================================================

  const sendSignal = (message) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify(message))
    }
  }

  // =========================================================
  // PARTICIPANT MANAGEMENT
  // =========================================================

  const addParticipant = (participantId, name, stream = null) => {
    setParticipants((prev) => {
      const exists = prev.find((p) => p.id === participantId)
      if (exists) {
        return prev.map((p) =>
          p.id === participantId
            ? { ...p, name, stream: stream || p.stream }
            : p
        )
      }
      return [...prev, { id: participantId, name, stream }]
    })
  }

  const removeParticipant = (participantId) => {
    const peer = peerConnectionsRef.current[participantId]
    if (peer) {
      peer.close()
      delete peerConnectionsRef.current[participantId]
    }
    delete pendingIceCandidatesRef.current[participantId]
    delete pendingOffersRef.current[participantId]
    setParticipants((prev) => prev.filter((p) => p.id !== participantId))
  }

  // =========================================================
  // PEER CONNECTION
  // =========================================================

  const createPeerConnection = (remoteUserId, remoteName) => {
    if (peerConnectionsRef.current[remoteUserId]) {
      return peerConnectionsRef.current[remoteUserId]
    }

    const pc = new RTCPeerConnection(rtcConfig)
    peerConnectionsRef.current[remoteUserId] = pc

    pc.onicecandidate = (event) => {
      if (!event.candidate) return
      sendSignal({ type: "ice-candidate", target: remoteUserId, candidate: event.candidate })
    }

    pc.ontrack = (event) => {
      const remoteStream = event.streams[0]
      if (!remoteStream) return
      addParticipant(remoteUserId, remoteName, remoteStream)
      setConnectionStatus("Connected")
    }

    pc.onconnectionstatechange = () => {
      const state = pc.connectionState
      if (state === "connected") setConnectionStatus("Connected")
      if (state === "failed") {
        // Try ICE restart
        try {
          pc.restartIce()
        } catch (e) {
          removeParticipant(remoteUserId)
        }
      }
      if (state === "closed") removeParticipant(remoteUserId)
    }

    // Add local media tracks
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => {
        pc.addTrack(track, streamRef.current)
      })
    }

    return pc
  }

  // =========================================================
  // OFFER / ANSWER / ICE
  // =========================================================

  const createOffer = async (remoteUserId, remoteName) => {
    // Guard against duplicate offers
    if (pendingOffersRef.current[remoteUserId]) return
    pendingOffersRef.current[remoteUserId] = true

    try {
      // Wait for local stream
      let attempts = 0
      while (!streamReadyRef.current && attempts < 100) {
        await new Promise((r) => setTimeout(r, 100))
        attempts++
      }

      if (!streamRef.current) {
        console.log("Local stream not ready, skipping offer")
        return
      }

      const pc = createPeerConnection(remoteUserId, remoteName)
      const offer = await pc.createOffer()
      await pc.setLocalDescription(offer)

      sendSignal({ type: "offer", target: remoteUserId, offer })
    } catch (error) {
      console.error("Create offer error:", error)
    } finally {
      delete pendingOffersRef.current[remoteUserId]
    }
  }

  const handleOffer = async (offer, remoteUserId) => {
    try {
      const participant = participants.find((p) => p.id === remoteUserId)
      const remoteName = participant?.name || "Participant"

      const pc = createPeerConnection(remoteUserId, remoteName)

      await pc.setRemoteDescription(new RTCSessionDescription(offer))

      // Flush pending ICE candidates
      const pending = pendingIceCandidatesRef.current[remoteUserId] || []
      for (const candidate of pending) {
        try {
          await pc.addIceCandidate(new RTCIceCandidate(candidate))
        } catch (e) {
          console.error("Pending ICE error:", e)
        }
      }
      pendingIceCandidatesRef.current[remoteUserId] = []

      const answer = await pc.createAnswer()
      await pc.setLocalDescription(answer)

      sendSignal({ type: "answer", target: remoteUserId, answer })
    } catch (error) {
      console.error("Handle offer error:", error)
    }
  }

  const handleAnswer = async (answer, remoteUserId) => {
    try {
      const pc = peerConnectionsRef.current[remoteUserId]
      if (!pc) return

      await pc.setRemoteDescription(new RTCSessionDescription(answer))

      const pending = pendingIceCandidatesRef.current[remoteUserId] || []
      for (const candidate of pending) {
        try {
          await pc.addIceCandidate(new RTCIceCandidate(candidate))
        } catch (e) {
          console.error("Pending ICE error:", e)
        }
      }
      pendingIceCandidatesRef.current[remoteUserId] = []
    } catch (error) {
      console.error("Handle answer error:", error)
    }
  }

  const handleIceCandidate = async (candidate, remoteUserId) => {
    try {
      const pc = peerConnectionsRef.current[remoteUserId]
      if (!pc || !pc.remoteDescription) {
        if (!pendingIceCandidatesRef.current[remoteUserId]) {
          pendingIceCandidatesRef.current[remoteUserId] = []
        }
        pendingIceCandidatesRef.current[remoteUserId].push(candidate)
        return
      }
      await pc.addIceCandidate(new RTCIceCandidate(candidate))
    } catch (error) {
      console.error("ICE candidate error:", error)
    }
  }

  const createOfferEvent = useEffectEvent(createOffer)
  const handleOfferEvent = useEffectEvent(handleOffer)

  // =========================================================
  // CLEANUP
  // =========================================================

  const stopMedia = () => {
    stopAudioStreaming()

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }

    Object.values(peerConnectionsRef.current).forEach((pc) => {
      try { pc.close() } catch (e) {}
    })
    peerConnectionsRef.current = {}

    if (videoRef.current) videoRef.current.srcObject = null
    setParticipants([])
  }

  // =========================================================
  // LEAVE MEETING
  // =========================================================

  const handleLeave = async () => {
    stopMedia()

    if (socketRef.current) {
      try { socketRef.current.close() } catch (e) {}
      socketRef.current = null
    }

    try {
      await fetch(
        `${API_URL}/meetings/${meetingId}/leave?user_id=${encodeURIComponent(user.google_id)}`,
        { method: "POST" }
      )
    } catch (error) {
      console.error("Leave meeting error:", error)
    }

    navigate("/dashboard", { replace: true })
  }

  // =========================================================
  // END MEETING
  // =========================================================

  const handleEnd = async () => {
    try {
      const response = await fetch(
        `${API_URL}/meetings/${meetingId}/end?user_id=${encodeURIComponent(user.google_id)}`,
        { method: "POST" }
      )

      const data = await response.json()

      if (!response.ok || !data.success) {
        alert(data.message || "Could not end meeting")
        return
      }

      setMeetingState("ending")

      stopMedia()

      if (socketRef.current) {
        try { socketRef.current.close() } catch (e) {}
        socketRef.current = null
      }

      navigate(`/meeting/${meetingId}/results`, { replace: true })
    } catch (error) {
      console.error("End meeting error:", error)
      alert("Could not connect to server")
    }
  }

  // =========================================================
  // WEBSOCKET SIGNALING
  // =========================================================

  useEffect(() => {
    if (!user?.google_id) return

    const socket = new WebSocket(`${WS_URL}/ws/meeting/${meetingId}`)
    socketRef.current = socket

    socket.onopen = () => {
      setConnectionStatus("Waiting for participants...")
      sendSignal({ type: "hello", user_id: user.google_id, name: user.name })
    }

    socket.onmessage = async (event) => {
      try {
        const message = JSON.parse(event.data)

        if (message.type === "hello") {
          const remoteUserId = String(message.user_id)
          if (remoteUserId === String(user.google_id)) return
          const remoteName = message.name || "Participant"
          addParticipant(remoteUserId, remoteName)

          if (String(user.google_id) < remoteUserId) {
            setTimeout(() => createOfferEvent(remoteUserId, remoteName), 500)
          }
          return
        }

        if (message.type === "existing-participants") {
          for (const p of message.participants) {
            const remoteUserId = String(p.user_id)
            if (remoteUserId === String(user.google_id)) continue
            const remoteName = p.name || "Participant"
            addParticipant(remoteUserId, remoteName)

            if (String(user.google_id) < remoteUserId) {
              setTimeout(() => createOfferEvent(remoteUserId, remoteName), 500)
            }
          }
          return
        }

        if (message.type === "participant-joined") {
          const remoteUserId = String(message.user_id)
          if (remoteUserId === String(user.google_id)) return
          const remoteName = message.name || "Participant"
          addParticipant(remoteUserId, remoteName)

          if (String(user.google_id) < remoteUserId) {
            setTimeout(() => createOfferEvent(remoteUserId, remoteName), 800)
          }
          return
        }

        if (message.type === "offer") {
          await handleOfferEvent(message.offer, message.from)
          return
        }

        if (message.type === "answer") {
          await handleAnswer(message.answer, message.from)
          return
        }

        if (message.type === "ice-candidate") {
          await handleIceCandidate(message.candidate, message.from)
          return
        }

        if (message.type === "participant-left") {
          removeParticipant(message.user_id)
          return
        }

        if (message.type === "meeting-ended") {
          setMeetingState("ending")
          stopMedia()
          if (socketRef.current) {
            try { socketRef.current.close() } catch (e) {}
            socketRef.current = null
          }
          navigate(`/meeting/${meetingId}/results`, { replace: true })
          return
        }
      } catch (error) {
        console.error("WebSocket message error:", error)
      }
    }

    socket.onerror = () => setConnectionStatus("WebSocket error")
    socket.onclose = () => setConnectionStatus("Disconnected")

    return () => {
      socket.close()
      socketRef.current = null
      Object.values(peerConnectionsRef.current).forEach((pc) => pc.close())
      peerConnectionsRef.current = {}
    }
  }, [meetingId, user?.google_id, user?.name])

  // =========================================================
  // CAMERA + MICROPHONE
  // =========================================================

  useEffect(() => {
    let mounted = true

    const startMedia = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: true
        })

        if (!mounted) {
          stream.getTracks().forEach((t) => t.stop())
          return
        }

        streamRef.current = stream
        streamReadyRef.current = true

        startAudioStreaming(stream)

        if (videoRef.current) {
          videoRef.current.srcObject = stream
        }

        // Add tracks to existing peer connections
        Object.values(peerConnectionsRef.current).forEach((pc) => {
          stream.getTracks().forEach((track) => {
            const senders = pc.getSenders()
            const hasTrack = senders.some((s) => s.track?.kind === track.kind)
            if (!hasTrack) {
              pc.addTrack(track, stream)
            }
          })
        })
      } catch (error) {
        console.error("Media error:", error)
        setMediaError("Could not access camera or microphone.")
      }
    }

    startMedia()

    return () => {
      mounted = false
      stopAudioStreaming()
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop())
        streamRef.current = null
      }
      streamReadyRef.current = false
    }
  }, [])

  // =========================================================
  // TOGGLES
  // =========================================================

  const toggleCamera = () => {
    if (!streamRef.current) return
    streamRef.current.getVideoTracks().forEach((t) => { t.enabled = !t.enabled })
    setCameraOn((prev) => !prev)
  }

  const toggleMic = () => {
    if (!streamRef.current) return
    streamRef.current.getAudioTracks().forEach((t) => { t.enabled = !t.enabled })
    setMicOn((prev) => !prev)
  }

  // =========================================================
  // VIDEO TILE
  // =========================================================

  const VideoTile = ({ participant }) => {
    const videoElementRef = (element) => {
      if (element && participant.stream && element.srcObject !== participant.stream) {
        element.srcObject = participant.stream
      }
    }

    return (
      <div style={styles.videoContainer}>
        {participant.stream ? (
          <video ref={videoElementRef} autoPlay playsInline style={styles.video} />
        ) : (
          <div style={styles.waiting}>
            <div style={styles.bigAvatar}>
              {participant.name?.charAt(0)?.toUpperCase() || "P"}
            </div>
            <p>Connecting...</p>
          </div>
        )}
        <div style={styles.nameLabel}>{participant.name}</div>
      </div>
    )
  }

  // =========================================================
  // RENDER
  // =========================================================

  if (meetingState === "ending") {
    return (
      <div style={{ ...styles.page, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ textAlign: "center" }}>
          <h2>Meeting Ending...</h2>
          <p style={{ color: "#888" }}>Redirecting to results...</p>
        </div>
      </div>
    )
  }

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Meeting Room</h1>
          <p style={styles.meetingId}>ID: <strong>{meetingId}</strong></p>
          <p style={styles.statusText}>Status: <strong>{connectionStatus}</strong></p>
          <p style={styles.statusText}>Participants: <strong>{participants.length + 1}</strong>/10</p>
        </div>
        <div style={styles.userInfo}>
          {user?.picture && <img src={user.picture} alt="" style={styles.avatar} />}
          <span>{user?.name || "Guest"}</span>
        </div>
      </div>

      {mediaError && <div style={styles.error}>{mediaError}</div>}

      <div style={styles.videoArea}>
        <div style={styles.videoContainer}>
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            style={{ ...styles.video, display: cameraOn ? "block" : "none" }}
          />
          {!cameraOn && (
            <div style={styles.cameraOff}>
              <div style={styles.bigAvatar}>
                {user?.name?.charAt(0)?.toUpperCase() || "U"}
              </div>
              <p>Camera is off</p>
            </div>
          )}
          <div style={styles.nameLabel}>{user?.name || "You"}</div>
        </div>

        {participants.map((participant) => (
          <VideoTile key={participant.id} participant={participant} />
        ))}
      </div>

      {participants.length === 0 && (
        <div style={styles.waitingMessage}>Waiting for participants...</div>
      )}

      <div style={styles.controls}>
        <button onClick={toggleMic} style={styles.controlButton}>
          {micOn ? "🎤 Mute" : "🔇 Unmute"}
        </button>
        <button onClick={toggleCamera} style={styles.controlButton}>
          {cameraOn ? "📹 Camera Off" : "📹 Camera On"}
        </button>
        <button onClick={handleLeave} style={styles.leaveButton}>
          Leave
        </button>
        <button onClick={handleEnd} style={styles.endButton}>
          End Meeting
        </button>
      </div>
    </div>
  )
}

const styles = {
  page: { minHeight: "100vh", background: "#111", color: "white", padding: "20px", boxSizing: "border-box" },
  header: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" },
  title: { margin: 0 },
  meetingId: { color: "#aaa", margin: "4px 0" },
  statusText: { color: "#aaa", margin: "2px 0" },
  userInfo: { display: "flex", alignItems: "center", gap: "10px" },
  avatar: { width: "40px", height: "40px", borderRadius: "50%" },
  error: { background: "#5c2020", padding: "12px", borderRadius: "8px", marginBottom: "15px" },
  videoArea: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "15px", minHeight: "65vh" },
  videoContainer: { position: "relative", background: "#222", borderRadius: "12px", overflow: "hidden", display: "flex", alignItems: "center", justifyContent: "center", minHeight: "250px" },
  video: { width: "100%", height: "100%", objectFit: "cover" },
  cameraOff: { textAlign: "center" },
  bigAvatar: { width: "90px", height: "90px", borderRadius: "50%", background: "#444", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "36px", margin: "auto" },
  waiting: { textAlign: "center", padding: "20px" },
  waitingMessage: { textAlign: "center", color: "#aaa", marginTop: "15px" },
  nameLabel: { position: "absolute", bottom: "10px", left: "10px", background: "rgba(0,0,0,.7)", padding: "6px 10px", borderRadius: "6px" },
  controls: { display: "flex", justifyContent: "center", gap: "12px", marginTop: "20px", flexWrap: "wrap" },
  controlButton: { padding: "12px 20px", borderRadius: "8px", border: "none", background: "#333", color: "white", cursor: "pointer", fontSize: "14px" },
  leaveButton: { padding: "12px 20px", borderRadius: "8px", border: "none", background: "#dc2626", color: "white", cursor: "pointer", fontSize: "14px" },
  endButton: { padding: "12px 20px", borderRadius: "8px", border: "none", background: "#b91c1c", color: "white", cursor: "pointer", fontSize: "14px", fontWeight: "bold" }
}

export default MeetingRoom
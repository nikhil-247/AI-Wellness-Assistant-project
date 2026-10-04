import { useEffect, useMemo, useRef, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";

const moods = ["calm", "happy", "stressed", "sad", "tired", "motivated"];

const music = {
  calm: "Lo-fi / ambient",
  happy: "Upbeat pop",
  stressed: "Slow instrumental",
  sad: "Comforting acoustic",
  tired: "Soft piano",
  motivated: "Positive focus",
};

function App() {
  const [message, setMessage] = useState("");
  const [mood, setMood] = useState("calm");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(false);
  const [story, setStory] = useState("");
  const recognitionRef = useRef(null);

  const browserSupportsVoice = useMemo(
    () => "webkitSpeechRecognition" in window || "SpeechRecognition" in window,
    []
  );

  useEffect(() => {
    const Recognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!Recognition) return;

    const recognition = new Recognition();
    recognition.interimResults = false;
    recognition.lang = "en-IN";

    recognition.onresult = (event) => {
      setMessage(event.results[0][0].transcript);
      setListening(false);
    };

    recognition.onerror = () => setListening(false);
    recognition.onend = () => setListening(false);

    recognitionRef.current = recognition;

    return () => recognition.abort();
  }, []);

  async function sendMessage() {
    const trimmed = message.trim();
    if (!trimmed || loading) return;

    const userMessage = { role: "user", content: trimmed };
    const nextHistory = [...messages, userMessage];

    setMessages(nextHistory);
    setMessage("");
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: trimmed,
          mood,
          history: messages,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Unable to generate a response");
      }

      setMessages([
        ...nextHistory,
        { role: "assistant", content: data.reply },
      ]);
    } catch (error) {
      setMessages([
        ...nextHistory,
        {
          role: "assistant",
          content: `I couldn't respond right now. ${error.message}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function startVoiceInput() {
    if (!recognitionRef.current) return;
    setListening(true);
    recognitionRef.current.start();
  }

  async function generateStory() {
    setLoading(true);
    setStory("");

    try {
      const response = await fetch(`${API_BASE}/api/story`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mood,
          theme: "a quiet evening under the stars",
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Unable to generate a story");
      }

      setStory(data.story);
    } catch (error) {
      setStory(error.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="shell">
      <section className="hero">
        <div>
          <p className="eyebrow">Vyom 2025 · AI Agent Showcase Winner</p>
          <h1>Self Love</h1>
          <p className="subtitle">
            A lightweight AI wellness companion for conversation, reflection,
            voice interaction, and small daily wellness moments.
          </p>
        </div>
        <div className="badge">AI Wellness Companion</div>
      </section>

      <section className="grid">
        <div className="card chat-card">
          <div className="card-header">
            <div>
              <h2>Talk it out</h2>
              <p>Share what is on your mind.</p>
            </div>
            <button
              className="secondary"
              onClick={startVoiceInput}
              disabled={!browserSupportsVoice || listening}
            >
              {listening ? "Listening…" : "🎙 Voice"}
            </button>
          </div>

          <div className="mood-row">
            {moods.map((item) => (
              <button
                key={item}
                className={item === mood ? "mood active" : "mood"}
                onClick={() => setMood(item)}
              >
                {item}
              </button>
            ))}
          </div>

          <div className="messages">
            {messages.length === 0 && (
              <div className="empty">
                <strong>How are you feeling today?</strong>
                <span>Pick a mood and start a conversation.</span>
              </div>
            )}

            {messages.map((item, index) => (
              <div
                key={index}
                className={item.role === "user" ? "message user" : "message assistant"}
              >
                {item.content}
              </div>
            ))}
          </div>

          <div className="composer">
            <textarea
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  sendMessage();
                }
              }}
              placeholder="Type how you're feeling…"
              rows="3"
            />
            <button className="primary" onClick={sendMessage} disabled={loading}>
              {loading ? "Thinking…" : "Send"}
            </button>
          </div>
        </div>

        <aside className="side-column">
          <div className="card">
            <p className="eyebrow">Mood match</p>
            <h3>{music[mood]}</h3>
            <p>
              A simple mood-based direction for what to listen to while you
              reset.
            </p>
          </div>

          <div className="card">
            <p className="eyebrow">Bedtime story</p>
            <h3>Wind down with a short story</h3>
            <button className="secondary full" onClick={generateStory} disabled={loading}>
              Generate story
            </button>
            {story && <p className="story">{story}</p>}
          </div>

          <div className="card reminder">
            <p className="eyebrow">Wellness reminder</p>
            <h3>Take a 5-minute reset</h3>
            <p>Step away from the screen, breathe, stretch, and come back when you feel ready.</p>
          </div>
        </aside>
      </section>

      <footer>
        Prototype for wellness support — not medical advice or a diagnostic tool.
      </footer>
    </main>
  );
}

export default App;

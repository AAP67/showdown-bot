"use client"

import { useState, useEffect, useRef } from "react"
import { db } from "./firebase"
import { collection, query, orderBy, limit, onSnapshot, doc } from "firebase/firestore"

const C = {
  red: "#E3350D", blue: "#3B4CCA", yellow: "#FFCB05",
  dark: "#1a1a2e", darker: "#0f0f1e", card: "#232342",
  cardLight: "#2d2d52", text: "#e8e8f0", muted: "#8888aa",
}

const TYPE_COLORS = {
  normal: "#A8A878", fire: "#F08030", water: "#6890F0", electric: "#F8D030",
  grass: "#78C850", ice: "#98D8D8", fighting: "#C03028", poison: "#A040A0",
  ground: "#E0C068", flying: "#A890F0", psychic: "#F85888", bug: "#A8B820",
  rock: "#B8A038", ghost: "#705898", dragon: "#7038F8", dark: "#705848",
  steel: "#B8B8D0", fairy: "#EE99AC",
}

function Pokeball({ size = 40, spinning = false }) {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100"
      style={spinning ? { animation: "spin 2s linear infinite" } : {}}>
      <circle cx="50" cy="50" r="48" fill={C.red} stroke="#222" strokeWidth="3"/>
      <rect x="0" y="47" width="100" height="6" fill="#222"/>
      <circle cx="50" cy="50" r="48" fill="white" clipPath="inset(50% 0 0 0)"/>
      <rect x="0" y="47" width="100" height="6" fill="#222"/>
      <circle cx="50" cy="50" r="16" fill="#222"/>
      <circle cx="50" cy="50" r="11" fill="white"/>
      <circle cx="50" cy="50" r="6" fill="#222"/>
    </svg>
  )
}

function TypeBadge({ type }) {
  return (
    <span style={{
      background: TYPE_COLORS[type?.toLowerCase()] || "#888",
      color: "white", padding: "2px 10px", borderRadius: "4px",
      fontSize: "11px", fontWeight: 700, textTransform: "uppercase",
      letterSpacing: "0.5px", textShadow: "0 1px 2px rgba(0,0,0,0.4)",
    }}>{type}</span>
  )
}

function StatBar({ label, value, color = C.yellow }) {
  return (
    <div style={{ marginBottom: "8px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", marginBottom: "3px" }}>
        <span style={{ color: C.muted, fontFamily: "'Press Start 2P', monospace", fontSize: "9px" }}>{label}</span>
        <span style={{ color: C.text, fontWeight: 700 }}>{value}%</span>
      </div>
      <div style={{ background: "#111", borderRadius: "4px", height: "8px", overflow: "hidden" }}>
        <div style={{
          width: `${Math.min(value, 100)}%`, height: "100%",
          background: `linear-gradient(90deg, ${color}, ${color}dd)`,
          borderRadius: "4px", transition: "width 0.8s ease",
          boxShadow: `0 0 8px ${color}44`,
        }}/>
      </div>
    </div>
  )
}

// ─── Landing Page ──────────────────────────────────────────────────────────

function LandingPage({ onLaunch, liveStats }) {
  return (
    <div style={{
      minHeight: "100vh",
      background: `radial-gradient(ellipse at 50% 0%, ${C.dark} 0%, ${C.darker} 70%)`,
      position: "relative", overflow: "hidden",
    }}>
      <div style={{
        position: "fixed", top: 0, left: 0, right: 0, bottom: 0, pointerEvents: "none", zIndex: 1,
        background: "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px)",
      }}/>

      {[...Array(6)].map((_, i) => (
        <div key={i} style={{
          position: "absolute", top: `${15 + i * 15}%`, left: `${5 + i * 18}%`,
          opacity: 0.06, animation: `float ${3 + i * 0.5}s ease-in-out infinite`,
          animationDelay: `${i * 0.3}s`,
        }}>
          <Pokeball size={60 + i * 20} />
        </div>
      ))}

      <nav style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        padding: "20px 40px", position: "relative", zIndex: 2,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <Pokeball size={32} />
          <span style={{ fontFamily: "'Press Start 2P', monospace", fontSize: "12px", color: C.yellow }}>SHOWDOWN AI</span>
        </div>
        <button onClick={onLaunch} style={{
          background: "transparent", border: `1px solid ${C.yellow}55`,
          color: C.yellow, padding: "8px 20px", borderRadius: "4px",
          cursor: "pointer", fontFamily: "'Press Start 2P', monospace", fontSize: "9px",
        }}>DASHBOARD →</button>
      </nav>

      <div style={{
        display: "flex", flexDirection: "column", alignItems: "center",
        justifyContent: "center", minHeight: "80vh", textAlign: "center",
        padding: "0 20px", position: "relative", zIndex: 2,
      }}>
        <div style={{ animation: "slideUp 0.8s ease forwards" }}>
          <div style={{
            fontFamily: "'Press Start 2P', monospace", fontSize: "10px",
            color: C.red, letterSpacing: "6px", marginBottom: "20px",
          }}>AI-POWERED COMPETITIVE POKEMON</div>

          <h1 style={{ fontSize: "clamp(36px, 6vw, 72px)", fontWeight: 900, margin: "0 0 10px 0", lineHeight: 1.1, animation: "glowText 3s ease-in-out infinite" }}>
            <span style={{ color: C.yellow }}>SHOWDOWN</span><br/>
            <span style={{ color: "white" }}>BATTLE BOT</span>
          </h1>

          <p style={{ fontSize: "16px", color: C.muted, maxWidth: "500px", margin: "20px auto 40px", lineHeight: 1.7 }}>
            An autonomous AI agent that plays Pokemon Showdown using Claude LLM reasoning,
            opponent set prediction, and smart heuristics. Live battle data from real ladder games.
          </p>

          <div style={{ display: "flex", gap: "30px", justifyContent: "center", marginBottom: "40px", flexWrap: "wrap" }}>
            {[
              { label: "BATTLES", value: liveStats.total_battles || "0", color: C.blue },
              { label: "WIN RATE", value: liveStats.win_rate ? `${liveStats.win_rate}%` : "—", color: C.yellow },
              { label: "ENGINE", value: "Claude", color: C.red },
            ].map((s, i) => (
              <div key={i} style={{
                background: C.card, border: `1px solid ${s.color}33`,
                borderRadius: "8px", padding: "16px 28px", minWidth: "120px",
              }}>
                <div style={{ fontFamily: "'Press Start 2P', monospace", fontSize: "8px", color: C.muted, marginBottom: "8px" }}>{s.label}</div>
                <div style={{ fontSize: "22px", fontWeight: 900, color: s.color }}>{s.value}</div>
              </div>
            ))}
          </div>

          <div style={{ display: "flex", gap: "16px", justifyContent: "center", flexWrap: "wrap" }}>
            <button onClick={onLaunch} style={{
              background: `linear-gradient(135deg, ${C.red}, ${C.red}cc)`,
              border: "none", color: "white", padding: "14px 36px", borderRadius: "6px",
              cursor: "pointer", fontFamily: "'Press Start 2P', monospace", fontSize: "11px",
              animation: "pulse 2s ease-in-out infinite",
            }}>⚔️ LAUNCH DASHBOARD</button>
            <button onClick={() => window.open("https://github.com/AAP67/showdown-bot", "_blank")} style={{
              background: "transparent", border: `2px solid ${C.text}33`,
              color: C.text, padding: "14px 36px", borderRadius: "6px",
              cursor: "pointer", fontFamily: "'Press Start 2P', monospace", fontSize: "11px",
            }}>📁 VIEW SOURCE</button>
          </div>

          <div style={{ marginTop: "60px", display: "flex", gap: "24px", flexWrap: "wrap", justifyContent: "center" }}>
            {["Python", "poke-env", "Claude API", "Firebase", "Next.js"].map((t, i) => (
              <span key={i} style={{
                background: C.card, padding: "6px 16px", borderRadius: "20px",
                fontSize: "12px", color: C.muted, border: `1px solid ${C.cardLight}`,
              }}>{t}</span>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── Dashboard ────────────────────────────────────────────────────────────

function Dashboard({ onBack, battles, liveStats }) {
  const wins = battles.filter(b => b.won).length
  const losses = battles.filter(b => !b.won).length
  const winRate = battles.length > 0 ? ((wins / battles.length) * 100).toFixed(1) : 0
  const avgTurns = battles.length > 0 ? (battles.reduce((s, b) => s + b.turns, 0) / battles.length).toFixed(1) : 0
  const llmRate = liveStats.llm_decision_rate || 0

  return (
    <div style={{ minHeight: "100vh", background: C.darker }}>
      <div style={{
        background: C.dark, borderBottom: `2px solid ${C.red}`,
        padding: "12px 24px", display: "flex", justifyContent: "space-between", alignItems: "center",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px", cursor: "pointer" }} onClick={onBack}>
          <Pokeball size={28} />
          <span style={{ fontFamily: "'Press Start 2P', monospace", fontSize: "10px", color: C.yellow }}>SHOWDOWN AI</span>
          <span style={{
            fontFamily: "'Press Start 2P', monospace", fontSize: "8px",
            background: C.red, color: "white", padding: "3px 8px", borderRadius: "3px",
          }}>LIVE</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#4CAF50", animation: "blink 1s ease-in-out infinite" }}/>
          <span style={{ fontFamily: "'Press Start 2P', monospace", fontSize: "8px", color: "#4CAF50" }}>
            {liveStats.username || "CONNECTED"}
          </span>
        </div>
      </div>

      <div style={{ padding: "24px", maxWidth: "1200px", margin: "0 auto" }}>
        {/* Stat cards */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "16px", marginBottom: "24px" }}>
          {[
            { label: "BATTLES", value: battles.length, icon: "⚔️", color: C.blue },
            { label: "WINS", value: wins, icon: "✅", color: "#4CAF50" },
            { label: "LOSSES", value: losses, icon: "❌", color: C.red },
            { label: "WIN RATE", value: `${winRate}%`, icon: "📊", color: C.yellow },
            { label: "AVG TURNS", value: avgTurns, icon: "🔄", color: "#9C27B0" },
            { label: "LLM RATE", value: `${llmRate}%`, icon: "🧠", color: "#00BCD4" },
          ].map((stat, i) => (
            <div key={i} style={{
              background: C.card, border: `1px solid ${stat.color}22`,
              borderRadius: "8px", padding: "16px", borderLeft: `3px solid ${stat.color}`,
            }}>
              <div style={{ fontFamily: "'Press Start 2P', monospace", fontSize: "8px", color: C.muted, marginBottom: "8px" }}>
                {stat.icon} {stat.label}
              </div>
              <div style={{ fontSize: "28px", fontWeight: 900, color: stat.color }}>{stat.value}</div>
            </div>
          ))}
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
          {/* Performance */}
          <div style={{ background: C.card, borderRadius: "8px", padding: "20px", border: `1px solid ${C.cardLight}` }}>
            <h3 style={{ fontFamily: "'Press Start 2P', monospace", fontSize: "11px", color: C.yellow, margin: "0 0 20px 0" }}>📊 PERFORMANCE</h3>
            <StatBar label="WIN RATE" value={parseFloat(winRate) || 0} color="#4CAF50"/>
            <StatBar label="LLM DECISIONS" value={parseFloat(llmRate) || 0} color="#00BCD4"/>

            <div style={{ marginTop: "20px" }}>
              <div style={{ fontFamily: "'Press Start 2P', monospace", fontSize: "8px", color: C.muted, marginBottom: "12px" }}>LAST 20 BATTLES</div>
              <div style={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
                {battles.slice(0, 20).map((b, i) => (
                  <div key={i} style={{
                    width: "24px", height: "24px", borderRadius: "4px",
                    background: b.won ? "#4CAF5033" : C.red + "33",
                    border: `1px solid ${b.won ? "#4CAF50" : C.red}`,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: "10px", animation: "slideIn 0.3s ease",
                  }}>{b.won ? "W" : "L"}</div>
                ))}
                {battles.length === 0 && <span style={{ color: C.muted, fontSize: "12px" }}>No battles yet — run the bot!</span>}
              </div>
            </div>
          </div>

          {/* API Stats */}
          <div style={{ background: C.card, borderRadius: "8px", padding: "20px", border: `1px solid ${C.cardLight}` }}>
            <h3 style={{ fontFamily: "'Press Start 2P', monospace", fontSize: "11px", color: C.yellow, margin: "0 0 20px 0" }}>🧠 AI ENGINE</h3>
            {[
              { label: "API Calls", value: liveStats.total_api_calls || 0 },
              { label: "Tokens Used", value: (liveStats.total_tokens || 0).toLocaleString() },
              { label: "Est. Cost", value: `$${((liveStats.total_tokens || 0) * 0.000003).toFixed(4)}` },
              { label: "LLM Decision Rate", value: `${liveStats.llm_decision_rate || 0}%` },
            ].map((s, i) => (
              <div key={i} style={{
                display: "flex", justifyContent: "space-between", padding: "8px 0",
                borderBottom: `1px solid ${C.cardLight}`,
              }}>
                <span style={{ fontSize: "13px", color: C.muted }}>{s.label}</span>
                <span style={{ fontSize: "13px", fontWeight: 700, color: C.text }}>{s.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Battle Log */}
        <div style={{ marginTop: "24px", background: C.card, borderRadius: "8px", padding: "20px", border: `1px solid ${C.cardLight}` }}>
          <h3 style={{ fontFamily: "'Press Start 2P', monospace", fontSize: "11px", color: C.yellow, margin: "0 0 16px 0" }}>📜 BATTLE LOG — LIVE FROM LADDER</h3>
          <div style={{ maxHeight: "400px", overflowY: "auto" }}>
            {battles.length === 0 ? (
              <div style={{ textAlign: "center", padding: "40px", color: C.muted }}>
                <Pokeball size={48} />
                <p style={{ fontFamily: "'Press Start 2P', monospace", fontSize: "9px", marginTop: "16px" }}>NO BATTLES YET</p>
                <p style={{ fontSize: "12px", marginTop: "8px" }}>Run the bot locally with `python bot_v5.py` → `ladder`</p>
              </div>
            ) : (
              battles.map((b, i) => (
                <div key={b.id || i} style={{
                  display: "flex", alignItems: "center", gap: "12px",
                  padding: "10px 12px", borderBottom: `1px solid ${C.cardLight}`,
                  animation: i === 0 ? "slideIn 0.3s ease" : "none",
                }}>
                  <span style={{
                    fontFamily: "'Press Start 2P', monospace", fontSize: "9px",
                    color: b.won ? "#4CAF50" : C.red, minWidth: "36px",
                  }}>
                    {b.won ? "WIN" : "LOSS"}
                  </span>
                  <span style={{ fontSize: "13px", fontWeight: 600, minWidth: "100px" }}>
                    {b.lead || "—"}
                  </span>
                  <span style={{ fontSize: "11px", color: C.muted }}>vs</span>
                  <span style={{ fontSize: "13px", fontWeight: 600, minWidth: "100px" }}>
                    {b.opponent || b.opp_lead || "—"}
                  </span>
                  <div style={{ display: "flex", gap: "4px" }}>
                    {(b.opp_lead_types || []).map(t => <TypeBadge key={t} type={t}/>)}
                  </div>
                  <span style={{
                    fontSize: "10px", padding: "2px 6px", borderRadius: "3px",
                    background: "#00BCD422", color: "#00BCD4",
                    border: "1px solid #00BCD444",
                  }}>
                    {b.bot_version || "v5"}
                  </span>
                  <span style={{ marginLeft: "auto", fontSize: "11px", color: C.muted }}>
                    {b.turns}t
                  </span>
                  {b.won && (
                    <span style={{ fontSize: "11px", color: "#4CAF50" }}>{b.remaining}/6</span>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── App ──────────────────────────────────────────────────────────────────

export default function Page() {
  const [page, setPage] = useState("landing")
  const [battles, setBattles] = useState([])
  const [liveStats, setLiveStats] = useState({})

  // Real-time listener for battles
  useEffect(() => {
    const q = query(collection(db, "battles"), orderBy("timestamp", "desc"), limit(50))
    const unsubBattles = onSnapshot(q, (snapshot) => {
      const data = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }))
      setBattles(data)
    }, (error) => {
      console.error("Firestore battles error:", error)
    })

    // Real-time listener for stats
    const unsubStats = onSnapshot(doc(db, "bot_stats", "latest"), (snapshot) => {
      if (snapshot.exists()) {
        setLiveStats(snapshot.data())
      }
    }, (error) => {
      console.error("Firestore stats error:", error)
    })

    return () => { unsubBattles(); unsubStats() }
  }, [])

  if (page === "landing") {
    return <LandingPage onLaunch={() => setPage("dashboard")} liveStats={liveStats} />
  }

  return <Dashboard onBack={() => setPage("landing")} battles={battles} liveStats={liveStats} />
}
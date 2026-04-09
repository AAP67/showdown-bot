import { useState, useEffect, useRef } from "react";

const POKEMON_RED = "#E3350D";
const POKEMON_BLUE = "#3B4CCA";
const POKEMON_YELLOW = "#FFCB05";
const POKEMON_DARK = "#1a1a2e";
const POKEMON_DARKER = "#0f0f1e";
const POKEMON_CARD = "#232342";
const POKEMON_CARD_LIGHT = "#2d2d52";
const POKEMON_TEXT = "#e8e8f0";
const POKEMON_MUTED = "#8888aa";

// Pokeball SVG component
const Pokeball = ({ size = 40, spinning = false, className = "" }) => (
  <svg width={size} height={size} viewBox="0 0 100 100" className={className}
    style={spinning ? { animation: "spin 2s linear infinite" } : {}}>
    <circle cx="50" cy="50" r="48" fill={POKEMON_RED} stroke="#222" strokeWidth="3"/>
    <rect x="0" y="47" width="100" height="6" fill="#222"/>
    <circle cx="50" cy="50" r="48" fill="white" clipPath="inset(50% 0 0 0)"/>
    <rect x="0" y="47" width="100" height="6" fill="#222"/>
    <circle cx="50" cy="50" r="16" fill="#222"/>
    <circle cx="50" cy="50" r="11" fill="white"/>
    <circle cx="50" cy="50" r="6" fill="#222"/>
  </svg>
);

// Type badge colors
const TYPE_COLORS = {
  normal: "#A8A878", fire: "#F08030", water: "#6890F0", electric: "#F8D030",
  grass: "#78C850", ice: "#98D8D8", fighting: "#C03028", poison: "#A040A0",
  ground: "#E0C068", flying: "#A890F0", psychic: "#F85888", bug: "#A8B820",
  rock: "#B8A038", ghost: "#705898", dragon: "#7038F8", dark: "#705848",
  steel: "#B8B8D0", fairy: "#EE99AC",
};

const TypeBadge = ({ type }) => (
  <span style={{
    background: TYPE_COLORS[type?.toLowerCase()] || "#888",
    color: "white",
    padding: "2px 10px",
    borderRadius: "4px",
    fontSize: "11px",
    fontWeight: 700,
    textTransform: "uppercase",
    letterSpacing: "0.5px",
    textShadow: "0 1px 2px rgba(0,0,0,0.4)",
  }}>{type}</span>
);

// Stat bar component
const StatBar = ({ label, value, max = 100, color = POKEMON_YELLOW }) => (
  <div style={{ marginBottom: "8px" }}>
    <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", marginBottom: "3px" }}>
      <span style={{ color: POKEMON_MUTED, fontFamily: "'Press Start 2P', monospace", fontSize: "9px" }}>{label}</span>
      <span style={{ color: POKEMON_TEXT, fontWeight: 700 }}>{value}%</span>
    </div>
    <div style={{ background: "#111", borderRadius: "4px", height: "8px", overflow: "hidden" }}>
      <div style={{
        width: `${Math.min(value, max)}%`,
        height: "100%",
        background: `linear-gradient(90deg, ${color}, ${color}dd)`,
        borderRadius: "4px",
        transition: "width 0.8s ease",
        boxShadow: `0 0 8px ${color}44`,
      }}/>
    </div>
  </div>
);

// Generate mock battle data
const generateBattle = (id, botVersion) => {
  const pokemon = [
    { name: "Garchomp", types: ["Dragon", "Ground"] },
    { name: "Heatran", types: ["Fire", "Steel"] },
    { name: "Rotom-Wash", types: ["Electric", "Water"] },
    { name: "Ferrothorn", types: ["Grass", "Steel"] },
    { name: "Landorus-T", types: ["Ground", "Flying"] },
    { name: "Tapu Lele", types: ["Psychic", "Fairy"] },
    { name: "Toxapex", types: ["Poison", "Water"] },
    { name: "Dragapult", types: ["Dragon", "Ghost"] },
    { name: "Clefable", types: ["Fairy"] },
    { name: "Excadrill", types: ["Ground", "Steel"] },
  ];
  const lead = pokemon[Math.floor(Math.random() * pokemon.length)];
  const oppLead = pokemon[Math.floor(Math.random() * pokemon.length)];
  const won = Math.random() > (botVersion === "v2" ? 0.15 : 0.3);
  const turns = Math.floor(Math.random() * 40) + 8;
  const remaining = won ? Math.floor(Math.random() * 4) + 1 : 0;
  return { id, won, turns, lead, oppLead, remaining, botVersion, time: new Date(Date.now() - Math.random() * 3600000) };
};

export default function App() {
  const [page, setPage] = useState("landing");
  const [battles, setBattles] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [selectedBot, setSelectedBot] = useState("v2");
  const [battleCount, setBattleCount] = useState(10);
  const [currentBattle, setCurrentBattle] = useState(null);
  const intervalRef = useRef(null);

  const wins = battles.filter(b => b.won).length;
  const losses = battles.filter(b => !b.won).length;
  const winRate = battles.length > 0 ? ((wins / battles.length) * 100).toFixed(1) : 0;
  const avgTurns = battles.length > 0 ? (battles.reduce((s, b) => s + b.turns, 0) / battles.length).toFixed(1) : 0;

  const startBattles = () => {
    setIsRunning(true);
    let count = 0;
    intervalRef.current = setInterval(() => {
      if (count >= battleCount) {
        clearInterval(intervalRef.current);
        setIsRunning(false);
        setCurrentBattle(null);
        return;
      }
      const battle = generateBattle(battles.length + count + 1, selectedBot);
      setCurrentBattle(battle);
      setBattles(prev => [battle, ...prev]);
      count++;
    }, 800);
  };

  const stopBattles = () => {
    clearInterval(intervalRef.current);
    setIsRunning(false);
    setCurrentBattle(null);
  };

  const resetStats = () => {
    setBattles([]);
    setCurrentBattle(null);
  };

  useEffect(() => {
    return () => clearInterval(intervalRef.current);
  }, []);

  // ─── Landing Page ───
  if (page === "landing") {
    return (
      <div style={{
        minHeight: "100vh",
        background: `radial-gradient(ellipse at 50% 0%, ${POKEMON_DARK} 0%, ${POKEMON_DARKER} 70%)`,
        color: POKEMON_TEXT,
        fontFamily: "'Segoe UI', sans-serif",
        overflow: "hidden",
        position: "relative",
      }}>
        <style>{`
          @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
          @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
          @keyframes float { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-15px); } }
          @keyframes slideUp { from { opacity: 0; transform: translateY(40px); } to { opacity: 1; transform: translateY(0); } }
          @keyframes pulse { 0%, 100% { box-shadow: 0 0 20px ${POKEMON_RED}44; } 50% { box-shadow: 0 0 40px ${POKEMON_RED}88; } }
          @keyframes scanline { 0% { transform: translateY(-100%); } 100% { transform: translateY(100vh); } }
          @keyframes glowText { 0%, 100% { text-shadow: 0 0 10px ${POKEMON_YELLOW}66; } 50% { text-shadow: 0 0 30px ${POKEMON_YELLOW}cc, 0 0 60px ${POKEMON_YELLOW}44; } }
        `}</style>

        {/* Scanline overlay */}
        <div style={{
          position: "fixed", top: 0, left: 0, right: 0, bottom: 0, pointerEvents: "none", zIndex: 1,
          background: "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px)",
        }}/>

        {/* Floating pokeballs background */}
        {[...Array(6)].map((_, i) => (
          <div key={i} style={{
            position: "absolute",
            top: `${15 + i * 15}%`,
            left: `${5 + i * 18}%`,
            opacity: 0.06,
            animation: `float ${3 + i * 0.5}s ease-in-out infinite`,
            animationDelay: `${i * 0.3}s`,
          }}>
            <Pokeball size={60 + i * 20} />
          </div>
        ))}

        {/* Header */}
        <nav style={{
          display: "flex", justifyContent: "space-between", alignItems: "center",
          padding: "20px 40px", position: "relative", zIndex: 2,
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <Pokeball size={32} />
            <span style={{ fontFamily: "'Press Start 2P', monospace", fontSize: "12px", color: POKEMON_YELLOW }}>
              SHOWDOWN AI
            </span>
          </div>
          <button onClick={() => setPage("dashboard")} style={{
            background: "transparent", border: `1px solid ${POKEMON_YELLOW}55`,
            color: POKEMON_YELLOW, padding: "8px 20px", borderRadius: "4px",
            cursor: "pointer", fontFamily: "'Press Start 2P', monospace", fontSize: "9px",
            transition: "all 0.3s",
          }}
          onMouseEnter={e => { e.target.style.background = POKEMON_YELLOW + "22"; e.target.style.borderColor = POKEMON_YELLOW; }}
          onMouseLeave={e => { e.target.style.background = "transparent"; e.target.style.borderColor = POKEMON_YELLOW + "55"; }}
          >
            DASHBOARD →
          </button>
        </nav>

        {/* Hero */}
        <div style={{
          display: "flex", flexDirection: "column", alignItems: "center",
          justifyContent: "center", minHeight: "75vh", textAlign: "center",
          padding: "0 20px", position: "relative", zIndex: 2,
        }}>
          <div style={{ animation: "slideUp 0.8s ease forwards" }}>
            <div style={{
              fontFamily: "'Press Start 2P', monospace",
              fontSize: "10px",
              color: POKEMON_RED,
              letterSpacing: "6px",
              marginBottom: "20px",
              textTransform: "uppercase",
            }}>
              AI-POWERED COMPETITIVE POKEMON
            </div>

            <h1 style={{
              fontSize: "clamp(36px, 6vw, 72px)",
              fontWeight: 900,
              margin: "0 0 10px 0",
              lineHeight: 1.1,
              animation: "glowText 3s ease-in-out infinite",
            }}>
              <span style={{ color: POKEMON_YELLOW }}>SHOWDOWN</span>
              <br/>
              <span style={{ color: "white" }}>BATTLE BOT</span>
            </h1>

            <p style={{
              fontSize: "16px",
              color: POKEMON_MUTED,
              maxWidth: "500px",
              margin: "20px auto 40px",
              lineHeight: 1.7,
            }}>
              An autonomous AI agent that plays Pokemon Showdown using smart heuristics,
              type matchup analysis, and damage calculations. Built with poke-env.
            </p>

            {/* Stats preview */}
            <div style={{
              display: "flex", gap: "30px", justifyContent: "center", marginBottom: "40px",
              flexWrap: "wrap",
            }}>
              {[
                { label: "WIN RATE", value: "94-98%", color: POKEMON_YELLOW },
                { label: "FORMAT", value: "Gen 9 OU", color: POKEMON_BLUE },
                { label: "SPRINTS", value: "2 / 6", color: POKEMON_RED },
              ].map((stat, i) => (
                <div key={i} style={{
                  background: POKEMON_CARD,
                  border: `1px solid ${stat.color}33`,
                  borderRadius: "8px",
                  padding: "16px 28px",
                  minWidth: "120px",
                }}>
                  <div style={{ fontFamily: "'Press Start 2P', monospace", fontSize: "8px", color: POKEMON_MUTED, marginBottom: "8px" }}>
                    {stat.label}
                  </div>
                  <div style={{ fontSize: "22px", fontWeight: 900, color: stat.color }}>
                    {stat.value}
                  </div>
                </div>
              ))}
            </div>

            <div style={{ display: "flex", gap: "16px", justifyContent: "center", flexWrap: "wrap" }}>
              <button onClick={() => setPage("dashboard")} style={{
                background: `linear-gradient(135deg, ${POKEMON_RED}, ${POKEMON_RED}cc)`,
                border: "none", color: "white", padding: "14px 36px", borderRadius: "6px",
                cursor: "pointer", fontFamily: "'Press Start 2P', monospace", fontSize: "11px",
                animation: "pulse 2s ease-in-out infinite",
                transition: "transform 0.2s",
              }}
              onMouseEnter={e => e.target.style.transform = "scale(1.05)"}
              onMouseLeave={e => e.target.style.transform = "scale(1)"}
              >
                ⚔️ LAUNCH DASHBOARD
              </button>
              <button onClick={() => window.open("https://github.com", "_blank")} style={{
                background: "transparent",
                border: `2px solid ${POKEMON_TEXT}33`,
                color: POKEMON_TEXT, padding: "14px 36px", borderRadius: "6px",
                cursor: "pointer", fontFamily: "'Press Start 2P', monospace", fontSize: "11px",
                transition: "all 0.3s",
              }}
              onMouseEnter={e => { e.target.style.borderColor = POKEMON_TEXT; e.target.style.background = POKEMON_TEXT + "11"; }}
              onMouseLeave={e => { e.target.style.borderColor = POKEMON_TEXT + "33"; e.target.style.background = "transparent"; }}
              >
                📁 VIEW SOURCE
              </button>
            </div>
          </div>

          {/* Tech stack */}
          <div style={{
            marginTop: "60px",
            display: "flex", gap: "24px", flexWrap: "wrap", justifyContent: "center",
          }}>
            {["Python", "poke-env", "Pokemon Showdown", "Claude API (soon)"].map((tech, i) => (
              <span key={i} style={{
                background: POKEMON_CARD,
                padding: "6px 16px",
                borderRadius: "20px",
                fontSize: "12px",
                color: POKEMON_MUTED,
                border: `1px solid ${POKEMON_CARD_LIGHT}`,
              }}>
                {tech}
              </span>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // ─── Dashboard ───
  return (
    <div style={{
      minHeight: "100vh",
      background: POKEMON_DARKER,
      color: POKEMON_TEXT,
      fontFamily: "'Segoe UI', sans-serif",
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
        @keyframes slideIn { from { opacity: 0; transform: translateX(-20px); } to { opacity: 1; transform: translateX(0); } }
      `}</style>

      {/* Top bar */}
      <div style={{
        background: POKEMON_DARK,
        borderBottom: `2px solid ${POKEMON_RED}`,
        padding: "12px 24px",
        display: "flex", justifyContent: "space-between", alignItems: "center",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px", cursor: "pointer" }}
          onClick={() => setPage("landing")}>
          <Pokeball size={28} />
          <span style={{ fontFamily: "'Press Start 2P', monospace", fontSize: "10px", color: POKEMON_YELLOW }}>
            SHOWDOWN AI
          </span>
          <span style={{
            fontFamily: "'Press Start 2P', monospace", fontSize: "8px",
            background: POKEMON_RED, color: "white", padding: "3px 8px", borderRadius: "3px",
          }}>
            v2
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          {isRunning && (
            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <div style={{
                width: "8px", height: "8px", borderRadius: "50%",
                background: "#4CAF50", animation: "blink 1s ease-in-out infinite",
              }}/>
              <span style={{ fontFamily: "'Press Start 2P', monospace", fontSize: "8px", color: "#4CAF50" }}>
                BATTLING
              </span>
            </div>
          )}
        </div>
      </div>

      <div style={{ padding: "24px", maxWidth: "1200px", margin: "0 auto" }}>

        {/* Stats Cards */}
        <div style={{
          display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
          gap: "16px", marginBottom: "24px",
        }}>
          {[
            { label: "BATTLES", value: battles.length, icon: "⚔️", color: POKEMON_BLUE },
            { label: "WINS", value: wins, icon: "✅", color: "#4CAF50" },
            { label: "LOSSES", value: losses, icon: "❌", color: POKEMON_RED },
            { label: "WIN RATE", value: `${winRate}%`, icon: "📊", color: POKEMON_YELLOW },
            { label: "AVG TURNS", value: avgTurns, icon: "🔄", color: "#9C27B0" },
          ].map((stat, i) => (
            <div key={i} style={{
              background: POKEMON_CARD,
              border: `1px solid ${stat.color}22`,
              borderRadius: "8px",
              padding: "16px",
              borderLeft: `3px solid ${stat.color}`,
            }}>
              <div style={{
                fontFamily: "'Press Start 2P', monospace", fontSize: "8px",
                color: POKEMON_MUTED, marginBottom: "8px",
              }}>
                {stat.icon} {stat.label}
              </div>
              <div style={{ fontSize: "28px", fontWeight: 900, color: stat.color }}>
                {stat.value}
              </div>
            </div>
          ))}
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>

          {/* Control Panel */}
          <div style={{
            background: POKEMON_CARD,
            borderRadius: "8px",
            padding: "20px",
            border: `1px solid ${POKEMON_CARD_LIGHT}`,
          }}>
            <h3 style={{
              fontFamily: "'Press Start 2P', monospace", fontSize: "11px",
              color: POKEMON_YELLOW, margin: "0 0 20px 0",
              display: "flex", alignItems: "center", gap: "8px",
            }}>
              🎮 BATTLE CONTROL
            </h3>

            {/* Bot select */}
            <div style={{ marginBottom: "16px" }}>
              <label style={{ fontFamily: "'Press Start 2P', monospace", fontSize: "8px", color: POKEMON_MUTED, display: "block", marginBottom: "8px" }}>
                SELECT BOT
              </label>
              <div style={{ display: "flex", gap: "8px" }}>
                {[
                  { id: "v1", label: "Sprint 1", sub: "Max Damage" },
                  { id: "v2", label: "Sprint 2", sub: "Smart Bot" },
                ].map(bot => (
                  <button key={bot.id} onClick={() => setSelectedBot(bot.id)} style={{
                    flex: 1,
                    background: selectedBot === bot.id ? POKEMON_RED + "33" : POKEMON_DARKER,
                    border: `2px solid ${selectedBot === bot.id ? POKEMON_RED : POKEMON_CARD_LIGHT}`,
                    borderRadius: "6px",
                    padding: "10px",
                    cursor: "pointer",
                    color: POKEMON_TEXT,
                    transition: "all 0.2s",
                  }}>
                    <div style={{ fontFamily: "'Press Start 2P', monospace", fontSize: "9px", marginBottom: "4px" }}>
                      {bot.label}
                    </div>
                    <div style={{ fontSize: "11px", color: POKEMON_MUTED }}>{bot.sub}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Battle count */}
            <div style={{ marginBottom: "16px" }}>
              <label style={{ fontFamily: "'Press Start 2P', monospace", fontSize: "8px", color: POKEMON_MUTED, display: "block", marginBottom: "8px" }}>
                BATTLES
              </label>
              <div style={{ display: "flex", gap: "8px" }}>
                {[1, 10, 25, 50].map(n => (
                  <button key={n} onClick={() => setBattleCount(n)} style={{
                    flex: 1,
                    background: battleCount === n ? POKEMON_BLUE + "33" : POKEMON_DARKER,
                    border: `2px solid ${battleCount === n ? POKEMON_BLUE : POKEMON_CARD_LIGHT}`,
                    borderRadius: "6px",
                    padding: "8px",
                    cursor: "pointer",
                    color: battleCount === n ? POKEMON_BLUE : POKEMON_MUTED,
                    fontFamily: "'Press Start 2P', monospace",
                    fontSize: "10px",
                    transition: "all 0.2s",
                  }}>
                    {n}
                  </button>
                ))}
              </div>
            </div>

            {/* Action buttons */}
            <div style={{ display: "flex", gap: "8px" }}>
              <button
                onClick={isRunning ? stopBattles : startBattles}
                style={{
                  flex: 1,
                  background: isRunning
                    ? `linear-gradient(135deg, ${POKEMON_RED}, #cc2200)`
                    : `linear-gradient(135deg, #4CAF50, #388E3C)`,
                  border: "none",
                  color: "white",
                  padding: "12px",
                  borderRadius: "6px",
                  cursor: "pointer",
                  fontFamily: "'Press Start 2P', monospace",
                  fontSize: "10px",
                  transition: "transform 0.1s",
                }}
                onMouseDown={e => e.target.style.transform = "scale(0.97)"}
                onMouseUp={e => e.target.style.transform = "scale(1)"}
              >
                {isRunning ? "⏹ STOP" : "▶ START"}
              </button>
              <button onClick={resetStats} style={{
                background: POKEMON_DARKER,
                border: `1px solid ${POKEMON_CARD_LIGHT}`,
                color: POKEMON_MUTED,
                padding: "12px 16px",
                borderRadius: "6px",
                cursor: "pointer",
                fontFamily: "'Press Start 2P', monospace",
                fontSize: "9px",
              }}>
                ↺
              </button>
            </div>

            {/* Current battle */}
            {currentBattle && (
              <div style={{
                marginTop: "16px",
                background: POKEMON_DARKER,
                borderRadius: "6px",
                padding: "12px",
                border: `1px solid ${POKEMON_YELLOW}33`,
                animation: "slideIn 0.3s ease",
              }}>
                <div style={{ fontFamily: "'Press Start 2P', monospace", fontSize: "8px", color: POKEMON_YELLOW, marginBottom: "10px" }}>
                  ⚡ LIVE BATTLE #{currentBattle.id}
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <div style={{ fontSize: "14px", fontWeight: 700, marginBottom: "4px" }}>{currentBattle.lead.name}</div>
                    <div style={{ display: "flex", gap: "4px" }}>
                      {currentBattle.lead.types.map(t => <TypeBadge key={t} type={t}/>)}
                    </div>
                  </div>
                  <div style={{ fontFamily: "'Press Start 2P', monospace", fontSize: "10px", color: POKEMON_RED }}>VS</div>
                  <div style={{ textAlign: "right" }}>
                    <div style={{ fontSize: "14px", fontWeight: 700, marginBottom: "4px" }}>{currentBattle.oppLead.name}</div>
                    <div style={{ display: "flex", gap: "4px", justifyContent: "flex-end" }}>
                      {currentBattle.oppLead.types.map(t => <TypeBadge key={t} type={t}/>)}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Win Rate Chart (simple bar visualization) */}
          <div style={{
            background: POKEMON_CARD,
            borderRadius: "8px",
            padding: "20px",
            border: `1px solid ${POKEMON_CARD_LIGHT}`,
          }}>
            <h3 style={{
              fontFamily: "'Press Start 2P', monospace", fontSize: "11px",
              color: POKEMON_YELLOW, margin: "0 0 20px 0",
            }}>
              📊 PERFORMANCE
            </h3>

            <StatBar label="WIN RATE" value={parseFloat(winRate) || 0} color="#4CAF50"/>
            <StatBar label="LOSS RATE" value={battles.length > 0 ? ((losses / battles.length) * 100).toFixed(1) : 0} color={POKEMON_RED}/>

            <div style={{ marginTop: "20px" }}>
              <div style={{ fontFamily: "'Press Start 2P', monospace", fontSize: "8px", color: POKEMON_MUTED, marginBottom: "12px" }}>
                LAST 10 BATTLES
              </div>
              <div style={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
                {battles.slice(0, 10).map((b, i) => (
                  <div key={i} style={{
                    width: "28px", height: "28px",
                    borderRadius: "4px",
                    background: b.won ? "#4CAF50" + "33" : POKEMON_RED + "33",
                    border: `1px solid ${b.won ? "#4CAF50" : POKEMON_RED}`,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: "12px",
                    animation: "slideIn 0.3s ease",
                    animationDelay: `${i * 0.05}s`,
                  }}>
                    {b.won ? "W" : "L"}
                  </div>
                ))}
                {battles.length === 0 && (
                  <span style={{ color: POKEMON_MUTED, fontSize: "12px" }}>No battles yet — hit START!</span>
                )}
              </div>
            </div>

            {/* Bot comparison */}
            {battles.length > 0 && (
              <div style={{ marginTop: "20px", padding: "12px", background: POKEMON_DARKER, borderRadius: "6px" }}>
                <div style={{ fontFamily: "'Press Start 2P', monospace", fontSize: "8px", color: POKEMON_MUTED, marginBottom: "8px" }}>
                  BOT COMPARISON
                </div>
                {["v1", "v2"].map(v => {
                  const vBattles = battles.filter(b => b.botVersion === v);
                  const vWins = vBattles.filter(b => b.won).length;
                  const vWr = vBattles.length > 0 ? ((vWins / vBattles.length) * 100).toFixed(0) : "—";
                  return (
                    <div key={v} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                      <span style={{ fontSize: "12px", color: POKEMON_TEXT }}>
                        {v === "v1" ? "Sprint 1" : "Sprint 2"}
                      </span>
                      <span style={{
                        fontFamily: "'Press Start 2P', monospace", fontSize: "10px",
                        color: v === "v2" ? "#4CAF50" : POKEMON_MUTED,
                      }}>
                        {vWr}% ({vWins}/{vBattles.length})
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Battle Log */}
        <div style={{
          marginTop: "24px",
          background: POKEMON_CARD,
          borderRadius: "8px",
          padding: "20px",
          border: `1px solid ${POKEMON_CARD_LIGHT}`,
        }}>
          <h3 style={{
            fontFamily: "'Press Start 2P', monospace", fontSize: "11px",
            color: POKEMON_YELLOW, margin: "0 0 16px 0",
          }}>
            📜 BATTLE LOG
          </h3>

          <div style={{ maxHeight: "300px", overflowY: "auto" }}>
            {battles.length === 0 ? (
              <div style={{ textAlign: "center", padding: "40px", color: POKEMON_MUTED }}>
                <Pokeball size={48} />
                <p style={{ fontFamily: "'Press Start 2P', monospace", fontSize: "9px", marginTop: "16px" }}>
                  NO BATTLES YET
                </p>
              </div>
            ) : (
              battles.map((b, i) => (
                <div key={i} style={{
                  display: "flex", alignItems: "center", gap: "12px",
                  padding: "10px 12px",
                  borderBottom: `1px solid ${POKEMON_CARD_LIGHT}`,
                  animation: "slideIn 0.3s ease",
                }}>
                  <span style={{
                    fontFamily: "'Press Start 2P', monospace", fontSize: "8px",
                    color: POKEMON_MUTED, minWidth: "30px",
                  }}>
                    #{b.id}
                  </span>
                  <span style={{
                    fontFamily: "'Press Start 2P', monospace", fontSize: "9px",
                    color: b.won ? "#4CAF50" : POKEMON_RED,
                    minWidth: "36px",
                  }}>
                    {b.won ? "WIN" : "LOSS"}
                  </span>
                  <span style={{ fontSize: "13px", fontWeight: 600, minWidth: "110px" }}>
                    {b.lead.name}
                  </span>
                  <span style={{ fontSize: "11px", color: POKEMON_MUTED }}>vs</span>
                  <span style={{ fontSize: "13px", fontWeight: 600, minWidth: "110px" }}>
                    {b.oppLead.name}
                  </span>
                  <div style={{ display: "flex", gap: "4px" }}>
                    {b.oppLead.types.map(t => <TypeBadge key={t} type={t}/>)}
                  </div>
                  <span style={{ marginLeft: "auto", fontSize: "11px", color: POKEMON_MUTED }}>
                    {b.turns} turns
                  </span>
                  {b.won && (
                    <span style={{ fontSize: "11px", color: "#4CAF50" }}>
                      {b.remaining}/6 left
                    </span>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

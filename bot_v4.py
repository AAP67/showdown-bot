"""
Pokemon Showdown Bot — Sprint 4
LLM-powered + opponent modeling (Smogon set prediction).

Usage:
  python bot_v4.py
"""

import asyncio
import json
import os
import re
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from poke_env.player import Player, RandomPlayer
from poke_env import AccountConfiguration, ServerConfiguration
from poke_env.data import GenData
from poke_env.battle import MoveCategory, SideCondition, PokemonType
from opponent_model import OpponentPredictor

try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    print("  ⚠️  anthropic package not found. Install with: pip install anthropic")


GEN_DATA = GenData.from_gen(9)
TYPE_CHART = GEN_DATA.type_chart


# ─── Battle Logger ───────────────────────────────────────────────────────────

class BattleLog:
    def __init__(self, verbose=True):
        self.entries = []
        self.verbose = verbose

    def log(self, turn, action_type, detail, reasoning=""):
        entry = {
            "turn": turn,
            "time": datetime.now().strftime("%H:%M:%S"),
            "type": action_type,
            "detail": detail,
            "reasoning": reasoning,
        }
        self.entries.append(entry)
        if self.verbose:
            tag = "⚔️  MOVE" if action_type == "move" else "🔄 SWITCH"
            print(f"  Turn {turn:>3} │ {tag} │ {detail}")
            if reasoning:
                print(f"          │        │ ↳ {reasoning}")

    def summary(self):
        if self.verbose:
            print(f"\n  Total actions: {len(self.entries)}")


# ─── Damage Estimator (fallback) ─────────────────────────────────────────────

def estimate_damage(move, attacker, defender):
    if move.base_power == 0:
        return 0
    power = move.base_power
    stab = 1.5 if move.type in attacker.types else 1.0
    effectiveness = 1.0
    for def_type in defender.types:
        if def_type:
            effectiveness *= move.type.damage_multiplier(def_type, type_chart=TYPE_CHART)
    if move.category == MoveCategory.PHYSICAL:
        atk = (attacker.stats or {}).get("atk", None) or attacker.base_stats.get("atk", 100)
        dfn = (defender.stats or {}).get("def", None) or defender.base_stats.get("def", 100)
        atk = (atk or 100) * _boost_multiplier(attacker.boosts.get("atk", 0))
        dfn = (dfn or 100) * _boost_multiplier(defender.boosts.get("def", 0))
    elif move.category == MoveCategory.SPECIAL:
        atk = (attacker.stats or {}).get("spa", None) or attacker.base_stats.get("spa", 100)
        dfn = (defender.stats or {}).get("spd", None) or defender.base_stats.get("spd", 100)
        atk = (atk or 100) * _boost_multiplier(attacker.boosts.get("spa", 0))
        dfn = (dfn or 100) * _boost_multiplier(defender.boosts.get("spd", 0))
    else:
        atk, dfn = 100, 100
    return power * stab * effectiveness * (atk / max(dfn, 1))


def _boost_multiplier(boost_level):
    if boost_level >= 0:
        return (2 + boost_level) / 2
    else:
        return 2 / (2 - boost_level)


# ─── Battle State Formatter ──────────────────────────────────────────────────

def format_battle_state(battle, predictor=None):
    """Convert battle state into a structured text prompt for the LLM."""
    active = battle.active_pokemon
    opponent = battle.opponent_active_pokemon

    lines = []
    lines.append("=== CURRENT BATTLE STATE ===")
    lines.append("")

    # Your active pokemon
    lines.append(f"YOUR ACTIVE: {active.species}")
    lines.append(f"  Types: {', '.join(t.name for t in active.types if t)}")
    lines.append(f"  HP: {active.current_hp_fraction * 100:.0f}%")
    if active.stats:
        lines.append(f"  Stats: {dict(active.stats)}")
    boosts = {k: v for k, v in active.boosts.items() if v != 0}
    if boosts:
        lines.append(f"  Boosts: {boosts}")
    if active.status:
        lines.append(f"  Status: {active.status}")
    if active.item:
        lines.append(f"  Item: {active.item}")
    if active.ability:
        lines.append(f"  Ability: {active.ability}")
    lines.append("")

    # Opponent's active pokemon
    if opponent:
        lines.append(f"OPPONENT ACTIVE: {opponent.species}")
        lines.append(f"  Types: {', '.join(t.name for t in opponent.types if t)}")
        lines.append(f"  HP: {opponent.current_hp_fraction * 100:.0f}%")
        opp_boosts = {k: v for k, v in opponent.boosts.items() if v != 0}
        if opp_boosts:
            lines.append(f"  Boosts: {opp_boosts}")
        if opponent.status:
            lines.append(f"  Status: {opponent.status}")
        revealed_moves = [m.id for m in opponent.moves.values()]
        if revealed_moves:
            lines.append(f"  Revealed moves: {', '.join(revealed_moves)}")
        if opponent.item:
            lines.append(f"  Item: {opponent.item}")
        if opponent.ability:
            lines.append(f"  Ability: {opponent.ability}")

        # Add opponent predictions
        if predictor:
            lines.append("")
            lines.append(predictor.format_prediction(opponent))
    lines.append("")

    # Available moves
    lines.append("AVAILABLE MOVES:")
    for i, move in enumerate(battle.available_moves):
        eff = 1.0
        if opponent:
            for t in opponent.types:
                if t:
                    eff *= move.type.damage_multiplier(t, type_chart=TYPE_CHART)
        stab = " (STAB)" if move.type in active.types else ""
        eff_label = ""
        if eff >= 2:
            eff_label = " [SUPER EFFECTIVE]"
        elif eff < 1 and eff > 0:
            eff_label = " [NOT VERY EFFECTIVE]"
        elif eff == 0:
            eff_label = " [IMMUNE]"
        cat = "Physical" if move.category == MoveCategory.PHYSICAL else "Special" if move.category == MoveCategory.SPECIAL else "Status"
        lines.append(f"  {i+1}. {move.id} | {move.type.name} | {move.base_power}BP | {cat}{stab}{eff_label} | Accuracy: {move.accuracy if move.accuracy else 100}%")
    lines.append("")

    # Available switches
    lines.append("AVAILABLE SWITCHES:")
    for i, mon in enumerate(battle.available_switches):
        hp = f"{mon.current_hp_fraction * 100:.0f}%"
        types = ', '.join(t.name for t in mon.types if t)
        status = f" [{mon.status}]" if mon.status else ""
        moves_list = ', '.join(m.id for m in mon.moves.values())
        lines.append(f"  {i+1}. {mon.species} | {types} | HP: {hp}{status} | Moves: {moves_list}")
    lines.append("")

    # Field conditions
    side_conds = list(battle.side_conditions.keys())
    opp_conds = list(battle.opponent_side_conditions.keys()) if hasattr(battle, 'opponent_side_conditions') else []
    if side_conds:
        lines.append(f"YOUR SIDE: {', '.join(str(s) for s in side_conds)}")
    if opp_conds:
        lines.append(f"OPPONENT SIDE: {', '.join(str(s) for s in opp_conds)}")
    if battle.weather:
        lines.append(f"WEATHER: {battle.weather}")
    if battle.fields:
        lines.append(f"TERRAIN: {', '.join(str(f) for f in battle.fields)}")

    # Opponent team predictions
    if predictor:
        opp_team = battle.opponent_team
        if opp_team:
            remaining = [p for p in opp_team.values() if not p.fainted and p != opponent]
            fainted = [p for p in opp_team.values() if p.fainted]
            lines.append(f"\nOPPONENT TEAM: {len(remaining) + (1 if opponent and not opponent.fainted else 0)} remaining, {len(fainted)} fainted")
            for p in remaining:
                predictor.update(p)
                lines.append(f"  - {p.species} ({', '.join(t.name for t in p.types if t)}) HP: {p.current_hp_fraction * 100:.0f}%")
                lines.append(predictor.format_prediction(p))

    return "\n".join(lines)


# ─── LLM Decision Engine ────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a competitive Pokemon battle AI. Given a battle state, pick the best action.

You now have access to OPPONENT SET PREDICTIONS showing likely unrevealed moves, items, and abilities with probability percentages. Use these to anticipate threats:
- If opponent likely has a super effective move, consider switching preemptively
- If opponent likely has a Choice item, they may be locked into one move
- If opponent likely has recovery, plan for a longer fight

CRITICAL: You MUST respond in EXACTLY this format with NO other text before it:

ACTION: move <move_name>
REASON: <one sentence>

or

ACTION: switch <pokemon_name>
REASON: <one sentence>

Do NOT write analysis, bullet points, or numbered lists. Do NOT use markdown. Just the two lines: ACTION and REASON. Use exact move/pokemon names from the state provided."""


class LLMEngine:
    def __init__(self):
        self.client = None
        self.call_count = 0
        self.total_tokens = 0

        if HAS_ANTHROPIC:
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if api_key:
                self.client = Anthropic(api_key=api_key)
                print("  ✅ Claude API connected")
            else:
                print("  ⚠️  ANTHROPIC_API_KEY not set. LLM will be disabled.")

    def decide(self, battle_state_text, available_moves, available_switches):
        if not self.client:
            return None, None, "LLM unavailable"

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=300,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": battle_state_text}],
            )

            self.call_count += 1
            self.total_tokens += response.usage.input_tokens + response.usage.output_tokens

            text = response.content[0].text.strip()

            # Parse ACTION line
            action_match = re.search(r"ACTION:\s*(move|switch)\s+(.+)", text, re.IGNORECASE)
            reason_match = re.search(r"REASON:\s*(.+)", text, re.IGNORECASE)

            # Fallback: try without move/switch keyword
            if not action_match:
                action_match_simple = re.search(r"ACTION:\s*(.+)", text, re.IGNORECASE)
                if action_match_simple:
                    raw_action = action_match_simple.group(1).strip().lower().replace(" ", "").replace("-", "")
                    for move in available_moves:
                        if move.id.lower().replace(" ", "").replace("-", "") == raw_action or raw_action in move.id.lower() or move.id.lower() in raw_action:
                            action_match = type('Match', (), {'group': lambda self, n: {1: 'move', 2: move.id}[n]})()
                            break
                    if not action_match:
                        for mon in available_switches:
                            mon_name = mon.species.lower().replace(" ", "").replace("-", "")
                            if mon_name == raw_action or raw_action in mon_name or mon_name in raw_action:
                                action_match = type('Match', (), {'group': lambda self, n: {1: 'switch', 2: mon.species}[n]})()
                                break

            if not action_match:
                return None, None, f"Could not parse: {text[:100]}"

            action_type = action_match.group(1).lower()
            action_name = action_match.group(2).strip().lower().replace(" ", "").replace("-", "")
            reasoning = reason_match.group(1).strip() if reason_match else "no reason given"

            if action_type == "move":
                for move in available_moves:
                    if move.id.lower().replace(" ", "").replace("-", "") == action_name:
                        return "move", move, reasoning
                for move in available_moves:
                    if action_name in move.id.lower() or move.id.lower() in action_name:
                        return "move", move, f"(fuzzy) {reasoning}"

            elif action_type == "switch":
                for mon in available_switches:
                    mon_name = mon.species.lower().replace(" ", "").replace("-", "")
                    if mon_name == action_name or action_name in mon_name or mon_name in action_name:
                        return "switch", mon, reasoning

            return None, None, f"Invalid action: {action_type} {action_name}"

        except Exception as e:
            return None, None, f"API error: {str(e)[:80]}"


# ─── LLM + Opponent Modeling Bot ─────────────────────────────────────────────

class LLMPredictBot(Player):
    """
    Sprint 4 bot: LLM decisions enhanced with opponent set predictions.
    """

    def __init__(self, battle_log: BattleLog, llm_engine: LLMEngine, **kwargs):
        super().__init__(**kwargs)
        self.battle_log = battle_log
        self.llm = llm_engine
        self.predictor = OpponentPredictor()
        self.llm_decisions = 0
        self.fallback_decisions = 0
        self._current_battle_tag = None

    def choose_move(self, battle):
        turn = battle.turn

        # Reset predictor for new battles
        if battle.battle_tag != self._current_battle_tag:
            self.predictor.reset()
            self._current_battle_tag = battle.battle_tag

        opponent = battle.opponent_active_pokemon
        active = battle.active_pokemon

        # Update predictor with opponent info
        if opponent:
            self.predictor.update(opponent)

        # Forced switch
        if battle.available_switches and not battle.available_moves:
            switch = self._llm_switch(battle, turn, forced=True)
            return self.create_order(switch)

        if not battle.available_moves:
            return self.choose_random_move(battle)

        # Build state with predictions
        state_text = format_battle_state(battle, self.predictor)

        action_type, action, reasoning = self.llm.decide(
            state_text, battle.available_moves, battle.available_switches
        )

        if action_type == "move" and action:
            self.llm_decisions += 1
            stab = " STAB" if action.type in active.types else ""
            self.battle_log.log(
                turn, "move",
                f"{action.id} ({action.base_power}BP{stab}) [LLM+PRED]",
                f"🧠 {reasoning}"
            )
            return self.create_order(action)

        elif action_type == "switch" and action:
            self.llm_decisions += 1
            self.battle_log.log(
                turn, "switch",
                f"{action.species} [LLM+PRED]",
                f"🧠 {reasoning}"
            )
            return self.create_order(action)

        # Fallback
        self.fallback_decisions += 1
        return self._heuristic_fallback(battle, turn, reasoning)

    def _llm_switch(self, battle, turn, forced=False):
        if not battle.available_switches:
            return battle.available_switches[0] if battle.available_switches else None

        state_text = format_battle_state(battle, self.predictor)
        action_type, action, reasoning = self.llm.decide(
            state_text, [], battle.available_switches
        )

        if action_type == "switch" and action:
            self.llm_decisions += 1
            label = "forced" if forced else "proactive"
            self.battle_log.log(turn, "switch", f"{action.species} [LLM+PRED]", f"🧠 {reasoning} ({label})")
            return action

        self.fallback_decisions += 1
        switch = battle.available_switches[0]
        self.battle_log.log(turn, "switch", f"{switch.species} [FALLBACK]", "LLM unavailable")
        return switch

    def _heuristic_fallback(self, battle, turn, llm_error=""):
        active = battle.active_pokemon
        opponent = battle.opponent_active_pokemon

        if battle.available_moves:
            best_move = max(
                battle.available_moves,
                key=lambda m: estimate_damage(m, active, opponent) if opponent else m.base_power
            )
            stab = " STAB" if best_move.type in active.types else ""
            self.battle_log.log(
                turn, "move",
                f"{best_move.id} ({best_move.base_power}BP{stab}) [FALLBACK]",
                f"⚙️ heuristic ({llm_error})"
            )
            return self.create_order(best_move)

        return self.choose_random_move(battle)


# ─── Sprint 3 Bot (for benchmarking) ─────────────────────────────────────────

class LLMBot(Player):
    """Sprint 3 LLM bot without predictions (for comparison)."""

    def __init__(self, battle_log: BattleLog, llm_engine: LLMEngine, **kwargs):
        super().__init__(**kwargs)
        self.battle_log = battle_log
        self.llm = llm_engine
        self.llm_decisions = 0
        self.fallback_decisions = 0

    def choose_move(self, battle):
        turn = battle.turn
        opponent = battle.opponent_active_pokemon
        active = battle.active_pokemon

        if battle.available_switches and not battle.available_moves:
            switch = battle.available_switches[0]
            self.battle_log.log(turn, "switch", switch.species, "forced switch")
            return self.create_order(switch)

        if not battle.available_moves:
            return self.choose_random_move(battle)

        state_text = format_battle_state(battle, predictor=None)
        action_type, action, reasoning = self.llm.decide(
            state_text, battle.available_moves, battle.available_switches
        )

        if action_type == "move" and action:
            self.llm_decisions += 1
            stab = " STAB" if action.type in active.types else ""
            self.battle_log.log(turn, "move", f"{action.id} ({action.base_power}BP{stab}) [LLM]", f"🧠 {reasoning}")
            return self.create_order(action)
        elif action_type == "switch" and action:
            self.llm_decisions += 1
            self.battle_log.log(turn, "switch", f"{action.species} [LLM]", f"🧠 {reasoning}")
            return self.create_order(action)

        self.fallback_decisions += 1
        if battle.available_moves:
            best_move = max(battle.available_moves, key=lambda m: estimate_damage(m, active, opponent) if opponent else m.base_power)
            self.battle_log.log(turn, "move", f"{best_move.id} [FALLBACK]", f"⚙️ {reasoning}")
            return self.create_order(best_move)
        return self.choose_random_move(battle)


# ─── CLI Controller ──────────────────────────────────────────────────────────

LOCAL_SERVER = ServerConfiguration(
    "ws://localhost:8000/showdown/websocket",
    "https://localhost:8000/api/login"
)


async def run_battle(bot_class, bot_name, num_battles=1, use_local=True, verbose=True, llm_engine=None):
    blog = BattleLog(verbose=verbose)

    server = LOCAL_SERVER if use_local else None
    bot_config = AccountConfiguration(bot_name, None)
    opp_config = AccountConfiguration(f"Opp{bot_name}", None)

    bot_kwargs = {"battle_format": "gen9randombattle", "account_configuration": bot_config}
    opp_kwargs = {"battle_format": "gen9randombattle", "account_configuration": opp_config}

    if server:
        bot_kwargs["server_configuration"] = server
        opp_kwargs["server_configuration"] = server

    if llm_engine and bot_class in (LLMBot, LLMPredictBot):
        bot = bot_class(battle_log=blog, llm_engine=llm_engine, **bot_kwargs)
    else:
        bot = bot_class(battle_log=blog, **bot_kwargs)

    opponent = RandomPlayer(**opp_kwargs)

    if verbose:
        print(f"\n{'='*55}")
        print(f"  🎮 {bot_name} — Starting {num_battles} battle(s)")
        print(f"{'='*55}\n")

    await bot.battle_against(opponent, n_battles=num_battles)

    wins = bot.n_won_battles
    total = bot.n_finished_battles
    wr = (wins / total * 100) if total else 0

    print(f"\n  📊 {bot_name}: {wins}W / {total - wins}L ({wr:.0f}% WR)")

    if hasattr(bot, 'llm_decisions'):
        total_decisions = bot.llm_decisions + bot.fallback_decisions
        llm_pct = (bot.llm_decisions / total_decisions * 100) if total_decisions else 0
        print(f"  🧠 LLM decisions: {bot.llm_decisions}/{total_decisions} ({llm_pct:.0f}%)")
        print(f"  📡 API calls: {bot.llm.call_count} | Tokens: {bot.llm.total_tokens}")

    return wins, total


async def benchmark(num_battles=5, use_local=True, llm_engine=None):
    print(f"\n{'='*55}")
    print(f"  🏆 BENCHMARK — {num_battles} battles each vs RandomPlayer")
    print(f"{'='*55}")

    print(f"\n  ── Sprint 3 (LLM only) ──")
    s3_wins, s3_total = await run_battle(
        LLMBot, "Sprint3Bot", num_battles, use_local, verbose=False, llm_engine=llm_engine
    )

    print(f"\n  ── Sprint 4 (LLM + Predictions) ──")
    s4_wins, s4_total = await run_battle(
        LLMPredictBot, "Sprint4Bot", num_battles, use_local, verbose=False, llm_engine=llm_engine
    )

    s3_wr = s3_wins / s3_total * 100 if s3_total else 0
    s4_wr = s4_wins / s4_total * 100 if s4_total else 0
    diff = s4_wr - s3_wr

    print(f"\n{'='*55}")
    print(f"  📊 RESULTS")
    print(f"  Sprint 3 (LLM):        {s3_wr:.0f}% WR ({s3_wins}/{s3_total})")
    print(f"  Sprint 4 (LLM+Pred):   {s4_wr:.0f}% WR ({s4_wins}/{s4_total})")
    print(f"  Improvement:           {diff:+.0f}%")
    print(f"{'='*55}\n")


def main():
    print("""
╔═══════════════════════════════════════════════╗
║       🎮  POKEMON SHOWDOWN BOT v4  🎮        ║
║       Sprint 4 — Opponent Modeling            ║
╚═══════════════════════════════════════════════╝
""")

    llm_engine = LLMEngine() if HAS_ANTHROPIC else None

    print("""
Commands:
  start [n]      — Run n battles with LLM+Predict Bot (default: 1)
  bench [n]      — Benchmark Sprint3 vs Sprint4 (default: 5 each)
  local          — Toggle local/public server
  stats          — Show LLM usage stats
  quit           — Exit
""")

    use_local = True

    while True:
        try:
            cmd = input("showdown-bot> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not cmd:
            continue

        parts = cmd.split()
        action = parts[0]

        if action in ("quit", "exit", "q"):
            print("GG! Exiting.")
            break

        elif action == "start":
            n = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
            try:
                asyncio.run(run_battle(LLMPredictBot, "PredictBot", n, use_local, llm_engine=llm_engine))
            except Exception as e:
                print(f"\n  ❗ Error: {e}\n")

        elif action == "bench":
            n = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 5
            try:
                asyncio.run(benchmark(n, use_local, llm_engine=llm_engine))
            except Exception as e:
                print(f"\n  ❗ Error: {e}\n")

        elif action == "stats":
            if llm_engine:
                print(f"\n  🧠 LLM Stats:")
                print(f"  API calls: {llm_engine.call_count}")
                print(f"  Total tokens: {llm_engine.total_tokens}")
                est_cost = llm_engine.total_tokens * 0.000003
                print(f"  Est. cost: ${est_cost:.4f}\n")
            else:
                print("  LLM not connected.\n")

        elif action == "local":
            use_local = not use_local
            print(f"  Server: {'local' if use_local else 'public'}")

        else:
            print("  Unknown command. Try: start, bench, stats, local, quit")


if __name__ == "__main__":
    main()

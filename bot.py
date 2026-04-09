"""
Pokemon Showdown Bot — Sprint 1
Max-damage heuristic bot with interactive CLI control layer.

Prerequisites:
  1. Run a local Pokemon Showdown server (see README)
  2. pip install poke-env

Usage:
  python bot.py
"""

import asyncio
import signal
import sys
from datetime import datetime
from poke_env.data import GenData
from poke_env.player import Player, RandomPlayer
from poke_env import AccountConfiguration, ServerConfiguration


# ─── Battle Logger ───────────────────────────────────────────────────────────

class BattleLog:
    """Stores and prints each action the bot takes."""

    def __init__(self):
        self.entries = []

    def log(self, turn, action_type, detail, reasoning=""):
        entry = {
            "turn": turn,
            "time": datetime.now().strftime("%H:%M:%S"),
            "type": action_type,
            "detail": detail,
            "reasoning": reasoning,
        }
        self.entries.append(entry)
        tag = "⚔️  MOVE" if action_type == "move" else "🔄 SWITCH"
        print(f"  Turn {turn:>3} │ {tag} │ {detail}")
        if reasoning:
            print(f"          │        │ ↳ {reasoning}")

    def summary(self):
        print(f"\n  Total actions: {len(self.entries)}")


# ─── Max Damage Heuristic Bot ────────────────────────────────────────────────

class MaxDamageBot(Player):
    """
    Picks the move that deals the most damage.
    Falls back to a random move if damage calc isn't available.
    """

    def __init__(self, battle_log: BattleLog, **kwargs):
        super().__init__(**kwargs)
        self.battle_log = battle_log

    def choose_move(self, battle):
        turn = battle.turn

        # If forced to switch (fainted), pick best type matchup
        if battle.available_switches and not battle.available_moves:
            switch = self._best_switch(battle)
            self.battle_log.log(turn, "switch", switch.species, "forced switch — no moves available")
            return self.create_order(switch)

        # Score each available move by estimated damage
        if battle.available_moves:
            best_move = max(
                battle.available_moves,
                key=lambda m: m.base_power * (1.5 if m.type in battle.active_pokemon.types else 1.0)
            )

            # Consider switching if best move is weak
            if best_move.base_power < 50 and battle.available_switches:
                switch = self._best_switch(battle)
                if switch:
                    self.battle_log.log(
                        turn, "switch", switch.species,
                        f"best move {best_move.id} only has {best_move.base_power} BP"
                    )
                    return self.create_order(switch)

            stab = "STAB" if best_move.type in battle.active_pokemon.types else ""
            self.battle_log.log(
                turn, "move", f"{best_move.id} ({best_move.base_power} BP {stab})",
                f"{battle.active_pokemon.species} vs {battle.opponent_active_pokemon.species if battle.opponent_active_pokemon else '???'}"
            )
            return self.create_order(best_move)

        # Fallback
        return self.choose_random_move(battle)

    def _best_switch(self, battle):
        """Pick the switch with the best type advantage vs opponent."""
        opponent = battle.opponent_active_pokemon
        if not opponent or not battle.available_switches:
            return battle.available_switches[0] if battle.available_switches else None

        def score(mon):
            s = 0
            for t in opponent.types:
                if t:
                    for my_t in mon.types:
                        if my_t:
                            s += my_t.damage_multiplier(t, type_chart=GenData.from_gen(9).type_chart)
            return -s

        return min(battle.available_switches, key=score)


# ─── CLI Controller ──────────────────────────────────────────────────────────

LOCAL_SERVER = ServerConfiguration(
    "ws://localhost:8000/showdown/websocket",
    "https://localhost:8000/api/login"
)
# For public server (uncomment if not running local):
# from poke_env import ShowdownServerConfiguration
# SERVER = ShowdownServerConfiguration


async def run_battle(num_battles=1, use_local=True):
    """Run battles and print action log."""
    blog = BattleLog()

    server = LOCAL_SERVER if use_local else None
    bot_config = AccountConfiguration("BotPlayer", None)
    opp_config = AccountConfiguration("RandomOpponent", None)

    bot_kwargs = {"battle_format": "gen9randombattle", "account_configuration": bot_config}
    opp_kwargs = {"battle_format": "gen9randombattle", "account_configuration": opp_config}

    if server:
        bot_kwargs["server_configuration"] = server
        opp_kwargs["server_configuration"] = server

    bot = MaxDamageBot(battle_log=blog, **bot_kwargs)
    opponent = RandomPlayer(**opp_kwargs)

    print(f"\n{'='*55}")
    print(f"  🎮 SHOWDOWN BOT — Starting {num_battles} battle(s)")
    print(f"  Format: gen9randombattle")
    print(f"  Server: {'local' if use_local else 'public'}")
    print(f"{'='*55}\n")

    for i in range(num_battles):
        print(f"\n── Battle {i+1}/{num_battles} ──────────────────────────────")
        await bot.battle_against(opponent, n_battles=1)

        # Print result
        last_battle = list(bot.battles.values())[-1]
        result = "✅ WIN" if last_battle.won else "❌ LOSS" if last_battle.lost else "➖ TIE"
        print(f"\n  Result: {result}")
        print(f"  Pokemon remaining: {sum(1 for m in last_battle.team.values() if not m.fainted)}/6")
        blog.summary()

    # Overall stats
    wins = bot.n_won_battles
    total = bot.n_finished_battles
    print(f"\n{'='*55}")
    print(f"  📊 Overall: {wins}W / {total - wins}L ({wins/total*100:.0f}% WR)" if total else "  No battles completed")
    print(f"{'='*55}\n")


def main():
    print("""
╔═══════════════════════════════════════════════╗
║       🎮  POKEMON SHOWDOWN BOT  🎮           ║
║       Sprint 1 — Max Damage Heuristic         ║
╚═══════════════════════════════════════════════╝

Commands:
  start [n]    — Run n battles (default: 1)
  local        — Toggle local/public server
  quit         — Exit

Prerequisite: local Showdown server on localhost:8000
  → See README.md for setup instructions
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
                asyncio.run(run_battle(num_battles=n, use_local=use_local))
            except Exception as e:
                print(f"\n  ❗ Error: {e}")
                print("  Make sure your Showdown server is running.\n")

        elif action == "local":
            use_local = not use_local
            print(f"  Server: {'local (localhost:8000)' if use_local else 'public (play.pokemonshowdown.com)'}")

        else:
            print("  Unknown command. Try: start, local, quit")


if __name__ == "__main__":
    main()

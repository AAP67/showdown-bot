"""
Pokemon Showdown Bot — Sprint 2
Smarter heuristics: damage calc, type-aware switching, hazard awareness, opponent tracking.

Usage:
  python bot_v2.py
"""

import asyncio
from datetime import datetime
from poke_env.player import Player, RandomPlayer
from poke_env import AccountConfiguration, ServerConfiguration
from poke_env.data import GenData
from poke_env.battle import MoveCategory, SideCondition, PokemonType


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


# ─── Damage Estimator ────────────────────────────────────────────────────────

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

    stat_ratio = atk / max(dfn, 1)
    return power * stab * effectiveness * stat_ratio


def _boost_multiplier(boost_level):
    if boost_level >= 0:
        return (2 + boost_level) / 2
    else:
        return 2 / (2 - boost_level)


# ─── Hazard Calculator ───────────────────────────────────────────────────────

def estimate_hazard_damage(mon, side_conditions):
    if mon.item and "heavydutyboots" in mon.item.lower().replace(" ", "").replace("-", ""):
        return 0.0

    damage = 0.0

    if SideCondition.STEALTH_ROCK in side_conditions:
        rock_mult = 1.0
        rock_type = PokemonType.ROCK
        for t in mon.types:
            if t:
                rock_mult *= rock_type.damage_multiplier(t, type_chart=TYPE_CHART)
        damage += rock_mult * 0.125

    if SideCondition.SPIKES in side_conditions:
        if PokemonType.FLYING not in mon.types:
            damage += 0.125

    if SideCondition.TOXIC_SPIKES in side_conditions:
        if PokemonType.POISON not in mon.types and PokemonType.STEEL not in mon.types:
            if PokemonType.FLYING not in mon.types:
                damage += 0.05

    return min(damage, 1.0)


# ─── Opponent Tracker ────────────────────────────────────────────────────────

def get_opponent_info(battle):
    opp = battle.opponent_active_pokemon
    if not opp:
        return {}

    return {
        "species": opp.species,
        "types": [t.name if t else None for t in opp.types],
        "revealed_moves": [m.id for m in opp.moves.values()],
        "item": opp.item if opp.item else "unknown",
        "ability": opp.ability if opp.ability else "unknown",
        "hp_pct": opp.current_hp_fraction,
        "boosts": dict(opp.boosts),
    }


# ─── Smart Bot ───────────────────────────────────────────────────────────────

class SmartBot(Player):
    def __init__(self, battle_log: BattleLog, **kwargs):
        super().__init__(**kwargs)
        self.battle_log = battle_log

    def choose_move(self, battle):
        turn = battle.turn
        opponent = battle.opponent_active_pokemon
        active = battle.active_pokemon

        if battle.available_switches and not battle.available_moves:
            switch = self._best_switch(battle)
            self.battle_log.log(turn, "switch", switch.species, "forced switch")
            return self.create_order(switch)

        if not battle.available_moves:
            return self.choose_random_move(battle)

        move_scores = []
        for move in battle.available_moves:
            if opponent:
                dmg = estimate_damage(move, active, opponent)
            else:
                dmg = move.base_power
            move_scores.append((move, dmg))

        move_scores.sort(key=lambda x: x[1], reverse=True)
        best_move, best_dmg = move_scores[0]

        should_switch, switch_reason = self._should_switch(battle, best_dmg)

        if should_switch and battle.available_switches:
            switch = self._best_switch(battle)
            if switch:
                self.battle_log.log(turn, "switch", switch.species, switch_reason)
                return self.create_order(switch)

        eff_label = ""
        if opponent:
            eff = 1.0
            for t in opponent.types:
                if t:
                    eff *= best_move.type.damage_multiplier(t, type_chart=TYPE_CHART)
            if eff >= 2:
                eff_label = " SE"
            elif eff < 1:
                eff_label = " NVE"

        stab = " STAB" if best_move.type in active.types else ""
        cat = "P" if best_move.category == MoveCategory.PHYSICAL else "S" if best_move.category == MoveCategory.SPECIAL else "?"

        self.battle_log.log(
            turn, "move",
            f"{best_move.id} ({best_move.base_power}BP {cat}{stab}{eff_label}, dmg={best_dmg:.0f})",
            f"{active.species} vs {opponent.species if opponent else '???'}"
        )
        return self.create_order(best_move)

    def _should_switch(self, battle, best_dmg):
        opponent = battle.opponent_active_pokemon
        active = battle.active_pokemon

        if not opponent or not battle.available_switches:
            return False, ""

        for opp_type in opponent.types:
            if opp_type:
                mult = opp_type.damage_multiplier(active.types[0], type_chart=TYPE_CHART)
                if len(active.types) > 1 and active.types[1]:
                    mult *= opp_type.damage_multiplier(active.types[1], type_chart=TYPE_CHART)
                if mult >= 2.0:
                    best_switch = self._best_switch(battle)
                    if best_switch and self._defensive_score(best_switch, opponent) < self._defensive_score(active, opponent):
                        return True, f"opponent {opponent.species} has SE STAB vs {active.species}"

        if best_dmg < 30:
            best_switch = self._best_switch(battle)
            if best_switch:
                return True, f"best move only scores {best_dmg:.0f} damage estimate"

        return False, ""

    def _defensive_score(self, mon, opponent):
        score = 0
        for opp_type in opponent.types:
            if opp_type:
                for my_type in mon.types:
                    if my_type:
                        score += opp_type.damage_multiplier(my_type, type_chart=TYPE_CHART)
        return score

    def _best_switch(self, battle):
        opponent = battle.opponent_active_pokemon
        if not battle.available_switches:
            return None

        my_side = battle.side_conditions

        def score(mon):
            def_score = self._defensive_score(mon, opponent) if opponent else 0
            hazard_cost = estimate_hazard_damage(mon, my_side) * 10
            hp_penalty = (1 - mon.current_hp_fraction) * 5

            offense_bonus = 0
            if opponent:
                for move in mon.moves.values():
                    if move.base_power > 0:
                        eff = 1.0
                        for t in opponent.types:
                            if t:
                                eff *= move.type.damage_multiplier(t, type_chart=TYPE_CHART)
                        if eff >= 2:
                            offense_bonus = -3
                            break

            return def_score + hazard_cost + hp_penalty + offense_bonus

        return min(battle.available_switches, key=score)


# ─── Sprint 1 Bot (for benchmarking) ─────────────────────────────────────────

class MaxDamageBot(Player):
    def __init__(self, battle_log: BattleLog, **kwargs):
        super().__init__(**kwargs)
        self.battle_log = battle_log

    def choose_move(self, battle):
        turn = battle.turn

        if battle.available_switches and not battle.available_moves:
            switch = battle.available_switches[0]
            self.battle_log.log(turn, "switch", switch.species, "forced switch")
            return self.create_order(switch)

        if battle.available_moves:
            best_move = max(
                battle.available_moves,
                key=lambda m: m.base_power * (1.5 if m.type in battle.active_pokemon.types else 1.0)
            )
            stab = "STAB" if best_move.type in battle.active_pokemon.types else ""
            self.battle_log.log(turn, "move", f"{best_move.id} ({best_move.base_power} BP {stab})")
            return self.create_order(best_move)

        return self.choose_random_move(battle)


# ─── CLI Controller ──────────────────────────────────────────────────────────

LOCAL_SERVER = ServerConfiguration(
    "ws://localhost:8000/showdown/websocket",
    "https://localhost:8000/api/login"
)


async def run_battle(bot_class, bot_name, num_battles=1, use_local=True, verbose=True):
    blog = BattleLog(verbose=verbose)

    server = LOCAL_SERVER if use_local else None
    bot_config = AccountConfiguration(bot_name, None)
    opp_config = AccountConfiguration(f"Opp{bot_name}", None)

    bot_kwargs = {"battle_format": "gen9randombattle", "account_configuration": bot_config}
    opp_kwargs = {"battle_format": "gen9randombattle", "account_configuration": opp_config}

    if server:
        bot_kwargs["server_configuration"] = server
        opp_kwargs["server_configuration"] = server

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
    return wins, total


async def benchmark(num_battles=50, use_local=True):
    print(f"\n{'='*55}")
    print(f"  🏆 BENCHMARK — {num_battles} battles each vs RandomPlayer")
    print(f"{'='*55}")

    print(f"\n  ── Sprint 1 (MaxDamage) ──")
    s1_wins, s1_total = await run_battle(
        MaxDamageBot, "Sprint1Bot", num_battles, use_local, verbose=False
    )

    print(f"\n  ── Sprint 2 (SmartBot) ──")
    s2_wins, s2_total = await run_battle(
        SmartBot, "Sprint2Bot", num_battles, use_local, verbose=False
    )

    s1_wr = s1_wins / s1_total * 100 if s1_total else 0
    s2_wr = s2_wins / s2_total * 100 if s2_total else 0
    diff = s2_wr - s1_wr

    print(f"\n{'='*55}")
    print(f"  📊 RESULTS")
    print(f"  Sprint 1 (MaxDamage):  {s1_wr:.0f}% WR ({s1_wins}/{s1_total})")
    print(f"  Sprint 2 (SmartBot):   {s2_wr:.0f}% WR ({s2_wins}/{s2_total})")
    print(f"  Improvement:           {diff:+.0f}%")
    print(f"{'='*55}\n")


def main():
    print("""
╔═══════════════════════════════════════════════╗
║       🎮  POKEMON SHOWDOWN BOT v2  🎮        ║
║       Sprint 2 — Smart Heuristics             ║
╚═══════════════════════════════════════════════╝

Commands:
  start [n]      — Run n battles with SmartBot (default: 1)
  bench [n]      — Benchmark Sprint1 vs Sprint2 (default: 50 each)
  local          — Toggle local/public server
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
                asyncio.run(run_battle(SmartBot, "SmartBot", n, use_local))
            except Exception as e:
                print(f"\n  ❗ Error: {e}\n")

        elif action == "bench":
            n = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 50
            try:
                asyncio.run(benchmark(n, use_local))
            except Exception as e:
                print(f"\n  ❗ Error: {e}\n")

        elif action == "local":
            use_local = not use_local
            print(f"  Server: {'local' if use_local else 'public'}")

        else:
            print("  Unknown command. Try: start, bench, local, quit")


if __name__ == "__main__":
    main()
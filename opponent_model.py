"""
Opponent Modeling Module — Sprint 4
Predicts opponent's unrevealed moves, items, and abilities using
common set data for Gen 9 Random Battles.
"""

# ─── Common Random Battle Sets ──────────────────────────────────────────────
# Format: pokemon_name -> list of possible sets with probabilities
# Each set: { moves: [], item: str, ability: str, weight: float }
# Weight represents relative frequency (higher = more common)
#
# This is a curated subset. In production you'd parse Showdown's
# randbats data directly from their GitHub repo.

RANDOM_SETS = {
    "heatran": {
        "moves": {
            "magmastorm": 0.65, "lavaplume": 0.45, "earthpower": 0.70,
            "flashcannon": 0.35, "stealthrock": 0.50, "taunt": 0.30,
            "toxic": 0.25, "willowisp": 0.20, "eruption": 0.15,
            "flamethrower": 0.40, "protect": 0.20,
        },
        "items": {"leftovers": 0.50, "airballoon": 0.20, "choicespecs": 0.15, "choicescarf": 0.10, "shucaberry": 0.05},
        "abilities": {"flashfire": 0.70, "flamebody": 0.30},
    },
    "landorustherian": {
        "moves": {
            "earthquake": 0.90, "uturn": 0.75, "stealthrock": 0.60,
            "stoneedge": 0.40, "flypress": 0.20, "knockoff": 0.30,
            "superpower": 0.15, "swordsdance": 0.20, "defog": 0.15,
        },
        "items": {"leftovers": 0.35, "choicescarf": 0.30, "choiceband": 0.15, "rockyhelmet": 0.15, "earthplate": 0.05},
        "abilities": {"intimidate": 0.95, "sheerforce": 0.05},
    },
    "toxapex": {
        "moves": {
            "scald": 0.85, "recover": 0.90, "toxic": 0.60, "toxicspikes": 0.50,
            "haze": 0.45, "knockoff": 0.30, "banefulbunker": 0.40,
            "infestation": 0.10,
        },
        "items": {"blacksludge": 0.80, "rockyhelmet": 0.15, "shedshell": 0.05},
        "abilities": {"regenerator": 0.85, "merciless": 0.10, "limber": 0.05},
    },
    "dragapult": {
        "moves": {
            "shadowball": 0.60, "dracometeor": 0.55, "fireblast": 0.40,
            "thunderbolt": 0.35, "uturn": 0.45, "dragondarts": 0.50,
            "willowisp": 0.30, "hex": 0.20, "phantomforce": 0.25,
            "reflect": 0.15, "lightscreen": 0.15, "thunderwave": 0.20,
        },
        "items": {"choicespecs": 0.30, "choiceband": 0.20, "lifeorb": 0.20, "lightclay": 0.15, "colburberry": 0.10, "focussash": 0.05},
        "abilities": {"infiltrator": 0.50, "clearbody": 0.40, "cursedbody": 0.10},
    },
    "clefable": {
        "moves": {
            "moonblast": 0.80, "softboiled": 0.75, "calmmind": 0.55,
            "thunderwave": 0.45, "stealthrock": 0.40, "flamethrower": 0.35,
            "knockoff": 0.30, "moonlight": 0.20, "wish": 0.25,
            "protect": 0.20, "teleport": 0.15,
        },
        "items": {"leftovers": 0.60, "lifeorb": 0.20, "heavydutyboots": 0.15, "lightclay": 0.05},
        "abilities": {"magicguard": 0.60, "unaware": 0.35, "friendguard": 0.05},
    },
    "garchomp": {
        "moves": {
            "earthquake": 0.90, "outrage": 0.40, "dragonclaw": 0.35,
            "stoneedge": 0.50, "scaleshot": 0.30, "swordsdance": 0.45,
            "stealthrock": 0.40, "fireblast": 0.20, "firefang": 0.25,
            "ironhead": 0.15,
        },
        "items": {"choicescarf": 0.25, "choiceband": 0.20, "lifeorb": 0.20, "rockyhelmet": 0.15, "focussash": 0.10, "leftovers": 0.10},
        "abilities": {"roughskin": 0.70, "sandveil": 0.30},
    },
    "corviknight": {
        "moves": {
            "bravebird": 0.70, "bodypress": 0.55, "roost": 0.80,
            "defog": 0.50, "uturn": 0.45, "ironhead": 0.30,
            "bulkup": 0.35, "taunt": 0.20, "thunderwave": 0.15,
        },
        "items": {"leftovers": 0.45, "rockyhelmet": 0.30, "heavydutyboots": 0.20, "sharpbeak": 0.05},
        "abilities": {"pressure": 0.50, "unnerve": 0.30, "mirrorarmor": 0.20},
    },
    "ferrothorn": {
        "moves": {
            "stealthrock": 0.60, "leechseed": 0.70, "protect": 0.50,
            "gyroball": 0.55, "knockoff": 0.45, "spikes": 0.40,
            "powerwhip": 0.35, "thunderwave": 0.25, "bodypress": 0.15,
        },
        "items": {"leftovers": 0.65, "rockyhelmet": 0.25, "shedshell": 0.10},
        "abilities": {"ironbarbs": 0.95, "anticipation": 0.05},
    },
    "rotomwash": {
        "moves": {
            "hydropump": 0.75, "voltswitch": 0.80, "willowisp": 0.55,
            "thunderbolt": 0.40, "trick": 0.30, "painsplit": 0.25,
            "defog": 0.20, "nastyplot": 0.15,
        },
        "items": {"leftovers": 0.50, "choicescarf": 0.20, "choicespecs": 0.15, "heavydutyboots": 0.10, "wikiberry": 0.05},
        "abilities": {"levitate": 1.0},
    },
    "grimmsnarl": {
        "moves": {
            "spiritbreak": 0.65, "reflect": 0.70, "lightscreen": 0.70,
            "thunderwave": 0.55, "taunt": 0.40, "darkestlariat": 0.30,
            "foulplay": 0.25, "trick": 0.20, "bulkup": 0.15,
        },
        "items": {"lightclay": 0.60, "leftovers": 0.20, "choiceband": 0.10, "laggingtail": 0.10},
        "abilities": {"prankster": 0.90, "frisk": 0.10},
    },
    "greatwhite": {
        "moves": {
            "closecombat": 0.80, "psychicfangs": 0.60, "icepunch": 0.50,
            "liquidation": 0.70, "flipturn": 0.40, "wavecrash": 0.30,
        },
        "items": {"choiceband": 0.50, "lifeorb": 0.30, "mysticwater": 0.20},
        "abilities": {"sheerforce": 0.60, "swiftswim": 0.40},
    },
    "chansey": {
        "moves": {
            "softboiled": 0.95, "stealthrock": 0.50, "thunderwave": 0.55,
            "toxic": 0.60, "seismictoss": 0.70, "healbell": 0.30,
            "wish": 0.25, "protect": 0.20, "teleport": 0.35,
        },
        "items": {"eviolite": 0.95, "heavydutyboots": 0.05},
        "abilities": {"naturalcure": 0.70, "serenegrace": 0.30},
    },
    "blissey": {
        "moves": {
            "softboiled": 0.90, "toxic": 0.55, "seismictoss": 0.65,
            "stealthrock": 0.40, "thunderwave": 0.45, "teleport": 0.35,
            "healbell": 0.25, "flamethrower": 0.20, "icebeam": 0.15,
        },
        "items": {"leftovers": 0.50, "heavydutyboots": 0.30, "shedshell": 0.15, "rockyhelmet": 0.05},
        "abilities": {"naturalcure": 0.70, "serenegrace": 0.30},
    },
    "weavile": {
        "moves": {
            "tripleaxel": 0.70, "knockoff": 0.85, "iciclecrash": 0.50,
            "icepunch": 0.30, "swordsdance": 0.45, "iceshards": 0.40,
            "lowkick": 0.35, "poisonjab": 0.20,
        },
        "items": {"choiceband": 0.40, "heavydutyboots": 0.25, "lifeorb": 0.20, "focussash": 0.15},
        "abilities": {"pressure": 0.90, "pickpocket": 0.10},
    },
    "excadrill": {
        "moves": {
            "earthquake": 0.90, "ironhead": 0.70, "swordsdance": 0.55,
            "rockslide": 0.40, "rapidsppin": 0.50, "stealthrock": 0.35,
            "rockblast": 0.20, "toxic": 0.10,
        },
        "items": {"leftovers": 0.30, "focussash": 0.25, "choicescarf": 0.20, "airballoon": 0.15, "lifeorb": 0.10},
        "abilities": {"moldbreaker": 0.50, "sandrush": 0.35, "sandforce": 0.15},
    },
}


# ─── Opponent Predictor ──────────────────────────────────────────────────────

class OpponentPredictor:
    """
    Tracks what's been revealed about each opponent Pokemon
    and predicts unrevealed moves/items/abilities.
    """

    def __init__(self):
        self.revealed = {}  # species -> { moves: set, item: str|None, ability: str|None }

    def update(self, pokemon):
        """Update tracking with newly revealed info."""
        species = self._normalize(pokemon.species)

        if species not in self.revealed:
            self.revealed[species] = {
                "moves": set(),
                "item": None,
                "ability": None,
            }

        # Track revealed moves
        for move in pokemon.moves.values():
            self.revealed[species]["moves"].add(move.id.lower())

        # Track item
        if pokemon.item:
            self.revealed[species]["item"] = pokemon.item.lower()

        # Track ability
        if pokemon.ability:
            self.revealed[species]["ability"] = pokemon.ability.lower()

    def predict(self, pokemon):
        """
        Return predictions for a pokemon.
        Returns dict with predicted_moves, predicted_item, predicted_ability,
        and confidence scores.
        """
        species = self._normalize(pokemon.species)

        # Update with current info
        self.update(pokemon)

        revealed = self.revealed.get(species, {"moves": set(), "item": None, "ability": None})
        set_data = RANDOM_SETS.get(species)

        if not set_data:
            return self._unknown_prediction(species, revealed)

        # Predict moves
        revealed_moves = revealed["moves"]
        predicted_moves = []

        for move, prob in sorted(set_data["moves"].items(), key=lambda x: -x[1]):
            if move in revealed_moves:
                predicted_moves.append({"move": move, "probability": 1.0, "revealed": True})
            else:
                # Adjust probability based on how many slots are left
                slots_used = len(revealed_moves)
                slots_left = 4 - slots_used
                if slots_left > 0:
                    # Boost probability for moves that commonly pair with revealed ones
                    adjusted_prob = min(prob * 1.2, 0.99) if slots_left <= 2 else prob
                    predicted_moves.append({"move": move, "probability": round(adjusted_prob, 2), "revealed": False})

        # Predict item
        if revealed["item"]:
            predicted_item = {"item": revealed["item"], "probability": 1.0, "revealed": True}
        else:
            top_item = max(set_data["items"].items(), key=lambda x: x[1])
            predicted_item = {"item": top_item[0], "probability": round(top_item[1], 2), "revealed": False}

        # Predict ability
        if revealed["ability"]:
            predicted_ability = {"ability": revealed["ability"], "probability": 1.0, "revealed": True}
        else:
            top_ability = max(set_data["abilities"].items(), key=lambda x: x[1])
            predicted_ability = {"ability": top_ability[0], "probability": round(top_ability[1], 2), "revealed": False}

        return {
            "species": species,
            "known": species in RANDOM_SETS,
            "predicted_moves": predicted_moves[:8],  # top 8 likely moves
            "predicted_item": predicted_item,
            "predicted_ability": predicted_ability,
            "revealed_count": len(revealed_moves),
            "confidence": self._confidence_score(revealed),
        }

    def format_prediction(self, pokemon):
        """Format prediction as text for LLM prompt."""
        pred = self.predict(pokemon)

        if not pred["known"]:
            return f"  No usage data available for {pred['species']}"

        lines = []
        lines.append(f"  PREDICTED SET for {pred['species']} (confidence: {pred['confidence']}):")

        # Moves
        unrevealed = [m for m in pred["predicted_moves"] if not m["revealed"]]
        revealed = [m for m in pred["predicted_moves"] if m["revealed"]]

        if revealed:
            lines.append(f"    Known moves: {', '.join(m['move'] for m in revealed)}")

        if unrevealed:
            top_unrevealed = unrevealed[:4]
            move_strs = [f"{m['move']}({m['probability']*100:.0f}%)" for m in top_unrevealed]
            lines.append(f"    Likely unrevealed: {', '.join(move_strs)}")

        # Item
        item = pred["predicted_item"]
        if item["revealed"]:
            lines.append(f"    Item: {item['item']} (confirmed)")
        else:
            lines.append(f"    Likely item: {item['item']} ({item['probability']*100:.0f}%)")

        # Ability
        ability = pred["predicted_ability"]
        if ability["revealed"]:
            lines.append(f"    Ability: {ability['ability']} (confirmed)")
        else:
            lines.append(f"    Likely ability: {ability['ability']} ({ability['probability']*100:.0f}%)")

        return "\n".join(lines)

    def format_team_predictions(self, battle):
        """Format predictions for all known opponent pokemon."""
        lines = ["\n=== OPPONENT SET PREDICTIONS ==="]

        opp_team = battle.opponent_team
        if not opp_team:
            return "\n  No opponent team data yet."

        for pokemon in opp_team.values():
            if not pokemon.fainted:
                self.update(pokemon)
                lines.append(self.format_prediction(pokemon))
                lines.append("")

        return "\n".join(lines)

    def _normalize(self, species):
        """Normalize species name for lookup."""
        return species.lower().replace(" ", "").replace("-", "").replace(".", "")

    def _confidence_score(self, revealed):
        """How confident are we in the prediction? Based on revealed info."""
        score = 0
        score += len(revealed["moves"]) * 20  # each revealed move = +20%
        if revealed["item"]:
            score += 15
        if revealed["ability"]:
            score += 15
        return f"{min(score, 100)}%"

    def _unknown_prediction(self, species, revealed):
        """Return basic prediction for unknown pokemon."""
        return {
            "species": species,
            "known": False,
            "predicted_moves": [{"move": m, "probability": 1.0, "revealed": True} for m in revealed["moves"]],
            "predicted_item": {"item": revealed["item"] or "unknown", "probability": 0.0, "revealed": bool(revealed["item"])},
            "predicted_ability": {"ability": revealed["ability"] or "unknown", "probability": 0.0, "revealed": bool(revealed["ability"])},
            "revealed_count": len(revealed["moves"]),
            "confidence": "low",
        }

    def reset(self):
        """Reset between battles."""
        self.revealed = {}

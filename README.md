# Pokemon Showdown Bot — Sprint 1

Max-damage heuristic bot with interactive CLI.

## Setup

### 1. Install dependencies
```bash
pip install poke-env
```

### 2. Run a local Showdown server
```bash
git clone https://github.com/smogon/pokemon-showdown.git
cd pokemon-showdown
npm install
cp config/config-example.js config/config.js
node pokemon-showdown start --no-security
```

The server runs on `localhost:8000` by default.

### 3. Run the bot
```bash
python bot.py
```

## CLI Commands

| Command     | Description                        |
|-------------|------------------------------------|
| `start`     | Run 1 battle                       |
| `start 10`  | Run 10 battles                     |
| `local`     | Toggle local/public server         |
| `quit`      | Exit                               |

## What the bot does

- Picks the highest base-power move each turn (with STAB bonus)
- Switches out if best move is weak (<50 BP)
- Switches to best type matchup when forced
- Logs every action with reasoning to the terminal

## Next sprints

- **Sprint 2**: Proper damage calc, hazard awareness, opponent tracking
- **Sprint 3**: LLM decision layer (Claude API)
- **Sprint 4**: Opponent set prediction via Smogon usage stats
- **Sprint 5**: Ladder deployment + dashboard

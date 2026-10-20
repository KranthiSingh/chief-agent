# Chief

## What it is
A personal skill-tracker AI agent built in Python on the Claude API.

Talk to it in plain English to log a session, ask about your progress, or check a streak.

Claude decides which tool to use. The tools are my own Python functions that read and write plain Markdown log files. I built it because I'm working on many skills at once and wanted one place to track them, and it runs on the real logs I keep every day.

## How it works

The user's message and tool definitions get sent to Claude, Claude asks for a tool, my code runs it and sends the result back. This process repeats until Claude has what it needs and replies with a final answer. I set a cap of 5 rounds so it can't loop forever.

Tools:
- `read_logs`: Reads the log for one skill so Claude can answer questions about my progress. E.g. "how many programming sessions have I done this week?"
- `log_session`: Adds today's session to a skill's log: minutes, what I did, and optional notes. E.g. "Did 20 min yoga"
- `compute_streak`: Counts the days in a row, up to today, on which my logged minutes hit a minimum that I choose. E.g. "what's my ai-eng streak with at least 60 min?"

## Example
```
Welcome to Chief
Are we adding a new session or would you like to know something about your skills?
What's my ai-eng streak with at least 45min?
**ai-engineering streak: 2 days** at 45+ min/day.

Short, but it's a start - one more solid session today or tomorrow and you're at 3. Want me to log a session?
Tokens used: 2310 input, 241 output
```

## Setup
You would need:
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (it installs Python 3.12+ for you if needed)
- an [Anthropic API key](https://console.anthropic.com/)

1. Clone the repo and install the dependencies:
```
git clone https://github.com/KranthiSingh/chief-agent.git
cd chief-agent
uv sync
```

2. Create a `.env` file in the project folder with two lines:
```
ANTHROPIC_API_KEY=your-key-here
LIFE_OPS_DIR=/path/to/your/tracker
```
`.env` is git-ignored, so your key stays out of the repo and never gets committed.
If `LIFE_OPS_DIR` is missing, the agent stops at startup and tells you how to set it.

3. Set up your log folder. Inside `LIFE_OPS_DIR`, each skill gets its own folder with a `log.md`:
```
your-tracker/
    skills/
        yoga/
            log.md
        programming/
            log.md
```
Skill folder names use lowercase letters, digits, and hyphens (e.g. ai-engineering).
Each log entry is one line, which the agent reads and writes:
```
- 2026-10-20 | 30 min | built the streak tool | tested both branches
```
(date | minutes | what you did | notes, or `-` for no notes)
The agent only writes to logs that already exist, so create a `log.md` for each skill first.

## Run
```
uv run --env-file .env chief
```
Then type a message, e.g. `Did 20min yoga - surya namaskar` or `what's my programming streak with at least 30min?`

## Status
Working: the three tools, input validation (skill names are allowlisted to block path traversal), fail-fast config, and a token count per run.

Next:
- An eval suite that checks Claude picks the right tool with the right arguments
- A `weekly_minutes` tool, so totals come from code instead of the model's arithmetic
- A richer `compute_streak` result, so Claude knows whether today counted
- Send tool errors back to Claude so it can retry, instead of stopping
- A Streamlit dashboard
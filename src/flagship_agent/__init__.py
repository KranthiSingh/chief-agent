import os
from datetime import date, timedelta
from pathlib import Path

import anthropic
from pydantic import BaseModel, Field


class Session(BaseModel):
    skill: str = Field(description="The skill folder name, e.g. 'yoga' or 'ai-engineering'")
    minutes: int = Field(description="Minutes spent on this session as a whole number e.g. '20'. Convert hours to minutes example 2h = 120")
    what: str = Field(description="What was done during the session, e.g. 'stretched', 'surya namaskar'. Keep extra details for notes. Never use the '|' character")
    notes: str = Field(default="", description="Any notes or extra information. Leave empty if the user gave none. Never use the '|' character.")


def log_path(skill: str) -> Path:
    life_ops_dir = os.environ.get("LIFE_OPS_DIR")
    if not life_ops_dir:
        raise RuntimeError("LIFE_OPS_DIR is not set. Please add it to your .env file, e.g. LIFE_OPS_DIR=/path/to/life-ops")
    base = Path(life_ops_dir)
    return base / "skills" / skill / "log.md"


def read_logs(skill: str) -> str:
    path = log_path(skill)
    if not path.exists():
        return f"No log found for this skill: {skill}"
    else:
        return path.read_text()


def format_entry(session: Session) -> str:
    today = date.today()
    if session.notes:
        notes = session.notes
    else:
        notes = "-"
    return f"- {today} | {session.minutes} min | {session.what} | {notes}"


def append_log(session: Session) -> str:
    path = log_path(session.skill)
    if not path.exists():
        return f"No log found for this skill: {session.skill}"
    else:
        with open(path, "a") as f:
            f.write(format_entry(session) + "\n")
        return f"Logged: {session.skill}, {session.minutes} min"


def parse_line(line: str) -> tuple[str, int]:
    row = line.split(" | ")
    day = row[0].removeprefix("- ")
    duration = row[1].split()
    if duration[0] == "?":
        minutes = 0
    else:
        minutes = int(duration[0])
    return day, minutes

def compute_streak(skill: str, minimum: int) -> int:
    text = read_logs(skill)
    totals = {}
    entries = text.splitlines()
    for line in entries:
        if not line.startswith("- 20"):
            continue
        day, minutes = parse_line(line)
        totals[day] = totals.get(day, 0) + minutes
    current_day = date.today()
    if totals.get(current_day.isoformat(), 0) < minimum:
        current_day = date.today() - timedelta(days=1)
    streak = 0
    while totals.get(current_day.isoformat(), 0) >= minimum:
        streak += 1
        current_day = current_day - timedelta(days=1)
    return streak


def main() -> None:
    client = anthropic.Anthropic()

    read_logs_tool = {
        "name": "read_logs",
        "description": "Read the log entries for one skill. Use this when the user asks for progress or history for a specific skill.",
        "input_schema": {
            "type": "object",
            "properties": {
                "skill": {"type": "string", "description": "The skill folder name e.g. 'yoga'"}
            },
            "required": ["skill"]
        }
    }

    log_session_tool = {
        "name": "log_session",
        "description": "Append a new session to the log. Use this when the user wants to add a new session to a specific skill, e.g. did 30min of dance practice",
        "input_schema": Session.model_json_schema(),
    }

    compute_streak_tool = {
        "name": "compute_streak",
        "description": "Compute the current streak for one skill, which is the number of days in a row, up to today, with at least 'minimum' minutes logged. If today hasn't reached the minimum yet, counting starts from yesterday. Use this when the user asks about their streak or consistency, e.g. 'Have I been keeping up with ai-engineering?'. If the user gives no minimum, ask them for one.",
        "input_schema": {
            "type": "object",
            "properties": {
                "skill": {"type": "string", "description": "The skill folder name e.g. programming"},
                "minimum": {"type": "integer", "description": "Minutes a day needed to count towards the streak"}
            },
            "required": ["skill", "minimum"]
        }
    }

    system_prompt = "You are a personal AI assistant acting as my skills coach. Be informative but concise, and motivating but realistic."

    print("Welcome to <name> \nAre we adding a new session or would you like to know something about your skills?")
    user_message = input()
    messages=[{"role": "user", "content": user_message}]

    turns = 0
    total_input = 0
    total_output = 0

    while turns < 5:
        turns += 1

        response = client.messages.create(
            model="claude-opus-5",
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
            tools=[read_logs_tool, log_session_tool, compute_streak_tool]
        )

        total_input += response.usage.input_tokens
        total_output += response.usage.output_tokens
        tool_results = []

        for block in response.content:
            if block.type == "text":
                print(block.text)
            elif block.type == "tool_use":
                if block.name == "read_logs":
                    skill = block.input["skill"]
                    result = read_logs(skill)
                elif block.name == "log_session":
                    session = Session.model_validate(block.input)
                    result = append_log(session)
                elif block.name == "compute_streak":
                    skill = block.input["skill"]
                    minimum = block.input["minimum"]
                    result = str(compute_streak(skill, minimum))
                else:
                    result = f"Unknown tool: {block.name}"
                tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result
                })

        if response.stop_reason != "tool_use":
            break

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    print(f"Tokens used: {total_input} input, {total_output} output")
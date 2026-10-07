import anthropic

from pathlib import Path
from pydantic import BaseModel, Field
from datetime import date


class Session(BaseModel):
    skill: str = Field(description="The skill folder name, e.g. 'yoga' or 'ai-engineering'")
    minutes: int = Field(description="Minutes spent on this session as a whole number e.g. '20'. Convert hours to minutes example 2h = 120")
    what: str = Field(description="What was done during the session, e.g. 'stretched', 'surya namaskar'. Keep extra details for notes. Never use the '|' character")
    notes: str = Field(default="", description="Any notes or extra information. Leave empty if the user gave none. Never use the '|' character.")


def read_logs(skill: str) -> str:
    path = Path.home() / "Projects" / "life-ops" / "skills" / skill / "log.md"
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
    path = Path.home() / "Projects" / "life-ops" / "skills" / session.skill / "log.md"
    if not path.exists():
        return f"No log found for this skill: {session.skill}"
    else:
        with open(path, "a") as f:
            f.write(format_entry(session) + "\n")
        return f"Logged: {session.skill}, {session.minutes} min"


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

    system_prompt = "You are a personal AI assistant acting as my skills coach. Be informative but concise, and motivating but realistic."

    messages=[{"role": "user", "content": "Hello"}]
    
    turns = 0
    while turns < 5:
        turns += 1

        response = client.messages.create(
            model="claude-opus-5",
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
            tools=[read_logs_tool]
        ) 

        tool_results = []
        for block in response.content:
            if block.type == "text":
                print(block.text)
            elif block.type == "tool_use":
                print(block.name, block.input)
                skill = block.input["skill"]
                result = read_logs(skill)
                tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result
                })

        if response.stop_reason != "tool_use":
            break

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    print(response.stop_reason)
    print(response.usage.input_tokens)
    print(response.usage.output_tokens)
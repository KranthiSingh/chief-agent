import anthropic

from pathlib import Path

def read_logs(skill: str) -> str:
    path = Path.home() / "Projects" / "life-ops" / "skills" / skill / "log.md"
    if not path.exists():
        return f"No log found for this skill: {skill}"
    else:
        return path.read_text()

def main() -> None:
    client = anthropic.Anthropic()
    print(read_logs("dance"))
    print(read_logs("chess"))

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

    response = client.messages.create(
        model="claude-opus-5",
        max_tokens=1024,
        system="You are a personal AI assistant acting as a skills coach. Be informative but concise and motivating but realistic.",
        messages=[{"role": "user", "content": "How is my yoga going this week?"}],
        tools=[read_logs_tool]
    ) 

    for block in response.content:
        if block.type == "text":
            print(block.text)
        elif block.type == "tool_use":
            print(block.name, block.input)

    print(response.stop_reason)
    print(response.usage.input_tokens)
    print(response.usage.output_tokens)
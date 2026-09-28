import anthropic

def main() -> None:
    client = anthropic.Anthropic()

    response = client.messages.create(
        model="claude-opus-5",
        max_tokens=1024,
        system="You are a personal AI assistant acting as a skills coach. Be informative but concise and motivating but realistic.",
        messages=[{"role": "user", "content": "did 20min yoga"}]
    ) 

    for block in response.content:
        if block.type == "text":
            print(block.text)
    print(response.stop_reason)
    print(response.usage.input_tokens)
    print(response.usage.output_tokens)
from openai import OpenAI


class OpenAIAgent:
    def __init__(self, api_key: str, model: str):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.tools = [

        ]

    def run_full_turn(self, system_message, messages, model=None):
        response = self.client.chat.completions.create(
            model=model if model else self.model,
            messages=[{"role": "system", "content": system_message}] + messages,
            tools=self.tools,
        )
        message = response.choices[0].message
        messages.append(message)

        if message.content: print("Assistant:", message.content)

        return message

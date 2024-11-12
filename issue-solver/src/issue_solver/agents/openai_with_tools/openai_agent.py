from openai import OpenAI

from issue_solver.agents.openai_with_tools.tools.tool_schema import function_to_schema, bash_tool_schema, \
    edit_tool_schema


class OpenAIAgent:
    def __init__(self, api_key: str, model: str):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.tools = [
            bash_tool_schema(),
            edit_tool_schema()
        ]

    def run_full_turn(self, system_message, messages, model=None):
        response = self.client.chat.completions.create(
            model=model if model else self.model,
            messages=[{"role": "system", "content": system_message}] + messages,
            functions=self.tools  # Ajoute les tools en tant que fonctions
        )
        message = response.choices[0].message
        messages.append(message)

        if message.content:
            print("Assistant:", message.content)

        return message


def prepare_tools(tools: list) -> list:
    tool_schemas = [function_to_schema(tool) for tool in tools]
    return tool_schemas

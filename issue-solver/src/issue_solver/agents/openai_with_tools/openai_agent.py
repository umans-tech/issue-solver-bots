import json

from openai import OpenAI

from issue_solver.agents.claude_tools.tools.bash import BashTool
from issue_solver.agents.claude_tools.tools.edit import EditTool
from issue_solver.agents.openai_with_tools.tools.tool_schema import bash_tool_schema, edit_tool_schema


class OpenAIAgent:
    def __init__(self, api_key: str, model: str):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        # Convert tools to schema
        self.tools = [bash_tool_schema(), edit_tool_schema()]
        self.bash_tool = BashTool()
        self.edit_tool = EditTool()

    async def run_full_turn(self, system_message, messages, model=None):
        response = self.client.chat.completions.create(
            model=model if model else self.model,
            messages=[{"role": "system", "content": system_message}] + messages,
            functions=self.tools
        )
        message = response.choices[0].message
        messages.append(message)

        # Vérifie si le modèle demande un appel de fonction
        if "function_call" in message:
            function_call = message["function_call"]
            function_name = function_call.get("name")
            arguments = json.loads(function_call.get("arguments", "{}"))

            # Exécute la commande appropriée avec process_tool_call
            tool_result = await self.process_tool_call(function_name, arguments)

            # Ajoute le résultat de l'outil dans les messages
            messages.append({
                "role": "function",
                "name": function_name,
                "content": tool_result.output or tool_result.error
            })

            # Relance une itération pour traiter la prochaine commande si nécessaire
            return await self.run_full_turn(system_message, messages, model)

        if message.content:
            print("Assistant:", message.content)

        return message

    async def process_tool_call(self, tool_name, tool_input):
        """Détermine et exécute le bon outil en fonction du nom."""
        if tool_name == "bash_command":
            return await self.bash_tool(**tool_input)
        elif tool_name == "edit_file":
            return await self.edit_tool(**tool_input)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

from issue_solver.agents.openai_with_tools.openai_agent import OpenAIAgent


def main() -> None:
    print("Hello from issue-solver openai with tools!")
    open_ai_agent = OpenAIAgent(api_key="api_key", model="model")

    messages = []
    while True:
        user = input("User: ")
        messages.append({"role": "user", "content": user})

        open_ai_agent.run_full_turn(system_message, messages)

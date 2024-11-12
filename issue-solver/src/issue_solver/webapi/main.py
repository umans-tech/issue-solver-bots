import os

from fastapi import FastAPI

from issue_solver.agents.openai_with_tools.openai_agent import OpenAIAgent
from issue_solver.agents.openai_with_tools.setup import resolution_approach_prompt

app = FastAPI()

@app.post("/resolutions")
def solve_issue_move_next(repo_location: str, issue_description: str):
    open_ai_agent = OpenAIAgent(api_key=os.environ["OPENAI_API_KEY"], model="gpt-4o-mini")
    system_message = resolution_approach_prompt(location=repo_location, pr_description=issue_description)
    one_turn_messages = open_ai_agent.run_full_turn(system_message=system_message, messages=[])
    return one_turn_messages

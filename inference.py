import os
import json
import asyncio
from openai import OpenAI
from environment import DependencyHellEnvironment
from scenarios import get_all_scenarios

# Read credentials from environment variables as the spec requires
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.environ.get("HF_TOKEN", "")

client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN or os.environ.get("OPENAI_API_KEY", "sk-placeholder"),
)


SYSTEM_PROMPT = """You are an expert Python dependency resolver.
You will be given a broken requirements.txt and must fix it by taking actions.

Available actions (respond with valid JSON only):
1. {"action_type": "pin_version", "package": "numpy", "version": "1.24.3"}
2. {"action_type": "remove_package", "package": "somepackage"}
3. {"action_type": "add_package", "package": "somepackage", "version": "1.0.0"}
4. {"action_type": "run_install"}

Rules:
- Analyze the current requirements and error messages carefully
- Pin conflicting packages to compatible versions
- Call run_install to test your solution and get a reward signal
- A score of 1.0 means all packages install successfully
- Respond with ONLY a JSON object, no explanation, no markdown
"""


def ask_llm(observation_text: str, history: list[dict]) -> dict:
    history.append({"role": "user", "content": observation_text})

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history,
        max_tokens=200,
        temperature=0.2,
    )

    raw = response.choices[0].message.content.strip()
    history.append({"role": "assistant", "content": raw})

    # Strip markdown code fences if the model wraps its JSON
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    
    return json.loads(raw.strip())


def observation_to_text(obs_dict: dict) -> str:
    reqs = "\n".join(obs_dict.get("requirements", []))
    errors = "\n".join(obs_dict.get("install_errors", []))
    successful = obs_dict.get("successful_imports", 0)
    total = obs_dict.get("total_packages", 0)
    message = obs_dict.get("message", "")

    return f"""Current requirements:
{reqs}

Last install errors:
{errors if errors else "None yet"}

Import success: {successful}/{total}
Status: {message}

What is your next action? Respond with JSON only."""


def run_task(task_id: str, difficulty: str) -> float:
    env = DependencyHellEnvironment()
    obs = env.reset(task_id=task_id)

    # Strict [START] log format as required by the spec
    print(json.dumps({
        "type": "START",
        "task_id": task_id,
        "difficulty": difficulty,
    }))

    conversation_history = []
    final_reward = 0.0
    step_num = 0

    while True:
        obs_dict = obs.model_dump()
        obs_text = observation_to_text(obs_dict)

        # Get action from LLM
        try:
            action_dict = ask_llm(obs_text, conversation_history)
        except Exception as e:
            # If LLM fails or returns invalid JSON, fall back to run_install
            action_dict = {"action_type": "run_install"}

        # Strict [STEP] log format as required by the spec
        print(json.dumps({
            "type": "STEP",
            "task_id": task_id,
            "step": step_num,
            "action": action_dict,
            "observation": obs_dict,
            "reward": final_reward,
        }))

        # Parse and execute action
        try:
            from models import Action, ActionType
            action = Action(**action_dict)
        except Exception:
            action = Action(action_type=ActionType.run_install)

        obs, reward, done, info = env.step(action)

        if reward > 0:
            final_reward = reward

        step_num += 1

        if done:
            break

    # Strict [END] log format as required by the spec
    print(json.dumps({
        "type": "END",
        "task_id": task_id,
        "difficulty": difficulty,
        "final_reward": final_reward,
        "steps_taken": step_num,
    }))

    return final_reward


def main():
    scenarios = get_all_scenarios()
    all_scores = {}

    print(json.dumps({"type": "START", "task_id": "ALL", "difficulty": "all"}))

    for scenario in scenarios:
        score = run_task(scenario.task_id, scenario.difficulty)
        all_scores[scenario.task_id] = score

    print(json.dumps({
        "type": "END",
        "task_id": "ALL",
        "difficulty": "all",
        "scores": all_scores,
        "mean_score": round(sum(all_scores.values()) / len(all_scores), 4),
    }))


if __name__ == "__main__":
    main()
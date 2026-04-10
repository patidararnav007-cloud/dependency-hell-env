import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q"])

try:
    from openai import OpenAI
except ImportError:
    install("openai>=1.0.0")
    from openai import OpenAI

import os
from environment import DependencyHellEnvironment
from scenarios import get_all_scenarios
from models import Action, ActionType

API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.getenv("HF_TOKEN", "")

client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN or os.getenv("OPENAI_API_KEY", "sk-placeholder"),
)

SYSTEM_PROMPT = """You are an expert Python dependency resolver.
Fix the broken requirements.txt by taking actions.

Available actions (respond with valid JSON only):
1. {"action_type": "pin_version", "package": "numpy", "version": "1.24.3"}
2. {"action_type": "remove_package", "package": "somepackage"}
3. {"action_type": "add_package", "package": "somepackage", "version": "1.0.0"}
4. {"action_type": "run_install"}

Respond with ONLY a JSON object, no explanation, no markdown."""


def ask_llm(obs_text: str, history: list) -> dict:
    import json
    history.append({"role": "user", "content": obs_text})
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history,
            max_tokens=200,
            temperature=0.2,
        )
        raw = response.choices[0].message.content.strip()
        history.append({"role": "assistant", "content": raw})
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception:
        return {"action_type": "run_install"}


def run_task(task_id: str, difficulty: str) -> float:
    env = DependencyHellEnvironment()
    obs = env.reset(task_id=task_id)

    print(f"[START] task={task_id} env=dependency-hell-env model={MODEL_NAME}", flush=True)

    history = []
    rewards = []
    final_reward = 0.0
    step_num = 0

    while True:
        obs_text = f"Requirements: {obs.requirements}\nErrors: {obs.install_errors}\nScore: {obs.successful_imports}/{obs.total_packages}\n{obs.message}"

        try:
            action_dict = ask_llm(obs_text, history)
            action = Action(**action_dict)
        except Exception:
            action = Action(action_type=ActionType.run_install)

        obs, reward, done, info = env.step(action)
        rewards.append(reward)

        if reward > 0:
            final_reward = reward

        step_num += 1
        done_str = str(done).lower()

        print(f"[STEP] step={step_num} action={action.action_type} reward={reward:.2f} done={done_str} error=null", flush=True)

        if done:
            break

    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    success = str(final_reward >= 0.5).lower()
    print(f"[END] success={success} steps={step_num} score={final_reward:.2f} rewards={rewards_str}", flush=True)

    return final_reward


def main():
    scenarios = get_all_scenarios()
    for scenario in scenarios:
        run_task(scenario.task_id, scenario.difficulty)


if __name__ == "__main__":
    main()
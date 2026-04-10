import subprocess
import sys
import os
import json
import time

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q"],
                         timeout=60)

try:
    import requests
except ImportError:
    install("requests")
    import requests

try:
    from openai import OpenAI
except ImportError:
    install("openai>=1.0.0")
    from openai import OpenAI


API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.getenv("HF_TOKEN", "")
ENV_URL = os.getenv("ENV_URL", "https://arnav-dev-01-dependency-hell-env.hf.space")

client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN or os.getenv("OPENAI_API_KEY", "sk-placeholder"),
)

SYSTEM_PROMPT = """You are an expert Python dependency resolver.
Fix broken requirements.txt by taking actions.

Available actions (respond with valid JSON only):
1. {"action_type": "pin_version", "package": "numpy", "version": "1.24.3"}
2. {"action_type": "remove_package", "package": "somepackage"}
3. {"action_type": "add_package", "package": "somepackage", "version": "1.0.0"}
4. {"action_type": "run_install"}

Respond with ONLY a JSON object, no explanation, no markdown."""

TASKS = [
    {"task_id": "easy_01", "difficulty": "easy"},
    {"task_id": "easy_02", "difficulty": "easy"},
    {"task_id": "medium_01", "difficulty": "medium"},
    {"task_id": "medium_02", "difficulty": "medium"},
    {"task_id": "hard_01", "difficulty": "hard"},
]


def reset_env(task_id: str) -> dict:
    resp = requests.post(
        f"{ENV_URL}/reset",
        params={"task_id": task_id},
        timeout=30,
    )
    return resp.json()


def step_env(action: dict) -> dict:
    resp = requests.post(
        f"{ENV_URL}/step",
        json=action,
        timeout=30,
    )
    return resp.json()


def ask_llm(obs_text: str, history: list) -> dict:
    history.append({"role": "user", "content": obs_text})
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history,
            max_tokens=150,
            temperature=0.2,
            timeout=20,
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
    print(f"[START] task={task_id} env=dependency-hell-env model={MODEL_NAME}", flush=True)

    try:
        obs = reset_env(task_id)
    except Exception as e:
        print(f"[STEP] step=1 action=reset reward=0.00 done=true error={e}", flush=True)
        print(f"[END] success=false steps=1 score=0.00 rewards=0.00", flush=True)
        return 0.0

    history = []
    rewards = []
    final_reward = 0.0
    step_num = 0
    max_steps = 8

    for _ in range(max_steps):
        obs_text = (
            f"Requirements: {obs.get('requirements', [])}\n"
            f"Errors: {obs.get('install_errors', [])}\n"
            f"Score: {obs.get('successful_imports', 0)}/{obs.get('total_packages', 0)}\n"
            f"{obs.get('message', '')}"
        )

        try:
            action_dict = ask_llm(obs_text, history)
        except Exception:
            action_dict = {"action_type": "run_install"}

        try:
            result = step_env(action_dict)
            obs = result.get("observation", obs)
            reward = float(result.get("reward", 0.0))
            done = result.get("done", False)
        except Exception as e:
            reward = 0.0
            done = True

        rewards.append(reward)
        if reward > 0:
            final_reward = reward

        step_num += 1
        done_str = str(done).lower()
        action_str = action_dict.get("action_type", "unknown")

        print(f"[STEP] step={step_num} action={action_str} reward={reward:.2f} done={done_str} error=null", flush=True)

        if done:
            break

        time.sleep(0.5)

    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    success = str(final_reward >= 0.5).lower()
    print(f"[END] success={success} steps={step_num} score={final_reward:.2f} rewards={rewards_str}", flush=True)

    return final_reward


def main():
    for task in TASKS:
        try:
            run_task(task["task_id"], task["difficulty"])
        except Exception as e:
            print(f"[START] task={task['task_id']} env=dependency-hell-env model={MODEL_NAME}", flush=True)
            print(f"[STEP] step=1 action=error reward=0.00 done=true error={e}", flush=True)
            print(f"[END] success=false steps=1 score=0.00 rewards=0.00", flush=True)


if __name__ == "__main__":
    main()
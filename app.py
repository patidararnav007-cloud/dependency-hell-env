import uvicorn
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from models import Action, Observation, EnvironmentState
from environment import DependencyHellEnvironment


env = DependencyHellEnvironment()


@asynccontextmanager
async def lifespan(app: FastAPI):
    env.reset()
    yield


app = FastAPI(
    title="Dependency Hell Environment",
    description="An OpenEnv-compatible RL environment for resolving Python dependency conflicts.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
def health_check():
    return {"status": "ok", "environment": "dependency-hell-env"}


@app.post("/reset", response_model=Observation)
def reset(task_id: str = None):
    try:
        observation = env.reset(task_id=task_id)
        return observation
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/reset", response_model=Observation)
def reset_get(task_id: str = None):
    try:
        observation = env.reset(task_id=task_id)
        return observation
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/step", response_model=dict)
def step(action: Action):
    try:
        observation, reward, done, info = env.step(action)
        return {
            "observation": observation.model_dump(),
            "reward": reward,
            "done": done,
            "info": info,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/state", response_model=EnvironmentState)
def state():
    try:
        return env.state()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks")
def list_tasks():
    from scenarios import get_all_scenarios
    return [
        {
            "task_id": s.task_id,
            "difficulty": s.difficulty,
            "description": s.description,
            "max_steps": s.max_steps,
        }
        for s in get_all_scenarios()
    ]


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
import random
from models import Action, ActionType, Observation, EnvironmentState
from scenarios import get_all_scenarios, get_scenario, Scenario
from grader import score_requirements


class DependencyHellEnvironment:

    def __init__(self):
        self.current_scenario: Scenario = None
        self.requirements: list[str] = []
        self.install_errors: list[str] = []
        self.successful_imports: int = 0
        self.steps_taken: int = 0
        self.done: bool = False

    def reset(self, task_id: str = None) -> Observation:
        if task_id is None:
            self.current_scenario = random.choice(get_all_scenarios())
        else:
            self.current_scenario = get_scenario(task_id)

        self.requirements = list(self.current_scenario.broken_requirements)
        self.install_errors = []
        self.successful_imports = 0
        self.steps_taken = 0
        self.done = False

        return self._build_observation("Environment reset. Fix the broken requirements.")

    def step(self, action: Action) -> tuple[Observation, float, bool, dict]:
        if self.done:
            obs = self._build_observation("Episode already finished. Call reset() to start again.")
            return obs, 0.01, True, {}

        self.steps_taken += 1
        reward = 0.01
        message = ""

        if action.action_type == ActionType.pin_version:
            message = self._handle_pin(action)

        elif action.action_type == ActionType.remove_package:
            message = self._handle_remove(action)

        elif action.action_type == ActionType.add_package:
            message = self._handle_add(action)

        elif action.action_type == ActionType.run_install:
            reward, message = self._handle_run_install()

        if self.steps_taken >= self.current_scenario.max_steps:
            self.done = True
            message += " Max steps reached. Episode ending."

        obs = self._build_observation(message)
        info = {
            "steps_taken": self.steps_taken,
            "max_steps": self.current_scenario.max_steps,
            "task_id": self.current_scenario.task_id,
        }

        return obs, reward, self.done, info

    def state(self) -> EnvironmentState:
        return EnvironmentState(
            requirements=self.requirements,
            install_errors=self.install_errors,
            successful_imports=self.successful_imports,
            total_packages=len(self.requirements),
            steps_taken=self.steps_taken,
            done=self.done,
            task_id=self.current_scenario.task_id if self.current_scenario else "",
            difficulty=self.current_scenario.difficulty if self.current_scenario else "",
        )

    def _handle_pin(self, action: Action) -> str:
        if not action.package or not action.version:
            return "pin_version requires both package and version fields."

        updated = False
        for i, req in enumerate(self.requirements):
            pkg_name = req.split("==")[0].split(">=")[0].split("<=")[0].strip()
            if pkg_name.lower() == action.package.lower():
                self.requirements[i] = f"{action.package}=={action.version}"
                updated = True
                break

        if not updated:
            return f"Package '{action.package}' not found. Use add_package to add new ones."

        return f"Pinned {action.package}=={action.version}."

    def _handle_remove(self, action: Action) -> str:
        if not action.package:
            return "remove_package requires a package name."

        before = len(self.requirements)
        self.requirements = [
            r for r in self.requirements
            if r.split("==")[0].split(">=")[0].strip().lower() != action.package.lower()
        ]

        if len(self.requirements) == before:
            return f"Package '{action.package}' not found in requirements."

        return f"Removed {action.package}."

    def _handle_add(self, action: Action) -> str:
        if not action.package:
            return "add_package requires a package name."

        entry = f"{action.package}=={action.version}" if action.version else action.package
        self.requirements.append(entry)
        return f"Added {entry}."

    def _handle_run_install(self) -> tuple[float, str]:
        score, errors, successful = score_requirements(self.requirements)

        self.install_errors = errors
        self.successful_imports = successful
        total = len(self.requirements)

        if score >= 0.99:
            self.done = True
            return 0.99, f"Perfect install! All {total}/{total} packages work. Episode complete."

        message = f"{successful}/{total} packages installed successfully."
        if errors:
            message += f" Errors: {errors[0]}"

        return score, message

    def _build_observation(self, message: str) -> Observation:
        return Observation(
            requirements=self.requirements,
            install_errors=self.install_errors,
            successful_imports=self.successful_imports,
            total_packages=len(self.requirements),
            message=message,
        )
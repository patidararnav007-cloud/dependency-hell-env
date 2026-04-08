from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class ActionType(str, Enum):
    pin_version = "pin_version"
    remove_package = "remove_package"
    add_package = "add_package"
    run_install = "run_install"


class Action(BaseModel):
    action_type: ActionType
    package: Optional[str] = None
    version: Optional[str] = None


class Observation(BaseModel):
    requirements: list[str] = Field(description="Current list of package requirements")
    install_errors: list[str] = Field(description="Errors from last install attempt")
    successful_imports: int = Field(description="Number of packages that imported successfully")
    total_packages: int = Field(description="Total packages in requirements")
    message: str = Field(description="Human readable status message")


class EnvironmentState(BaseModel):
    requirements: list[str]
    install_errors: list[str]
    successful_imports: int
    total_packages: int
    steps_taken: int
    done: bool
    task_id: str
    difficulty: str
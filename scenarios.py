from dataclasses import dataclass, field


@dataclass
class Scenario:
    task_id: str
    difficulty: str
    description: str
    broken_requirements: list[str]
    solution_requirements: list[str]
    max_steps: int


def get_all_scenarios() -> list[Scenario]:
    return [

        Scenario(
            task_id="easy_01",
            difficulty="easy",
            description="Fix a numpy/tensorflow version conflict",
            broken_requirements=[
                "numpy==1.19.0",
                "tensorflow==2.12.0",
                "pandas==1.3.0",
            ],
            solution_requirements=[
                "numpy==1.23.5",
                "tensorflow==2.12.0",
                "pandas==1.3.0",
            ],
            max_steps=10,
        ),

        Scenario(
            task_id="easy_02",
            difficulty="easy",
            description="Pin an unpinned dependency causing install failure",
            broken_requirements=[
                "flask==2.0.0",
                "werkzeug==3.0.0",
            ],
            solution_requirements=[
                "flask==2.0.0",
                "werkzeug==2.0.3",
            ],
            max_steps=10,
        ),

        Scenario(
            task_id="medium_01",
            difficulty="medium",
            description="Resolve a three-way diamond dependency conflict",
            broken_requirements=[
                "scipy==1.6.0",
                "statsmodels==0.14.0",
                "scikit-learn==1.3.0",
            ],
            solution_requirements=[
                "scipy==1.11.0",
                "statsmodels==0.14.0",
                "scikit-learn==1.3.0",
            ],
            max_steps=20,
        ),

        Scenario(
            task_id="medium_02",
            difficulty="medium",
            description="Fix a broken data pipeline environment",
            broken_requirements=[
                "apache-airflow==2.7.0",
                "sqlalchemy==2.0.0",
                "alembic==1.12.0",
                "flask==3.0.0",
            ],
            solution_requirements=[
                "apache-airflow==2.7.0",
                "sqlalchemy==1.4.49",
                "alembic==1.12.0",
                "flask==2.3.3",
            ],
            max_steps=20,
        ),

        Scenario(
            task_id="hard_01",
            difficulty="hard",
            description="Untangle a 8-package ML environment with cascading conflicts",
            broken_requirements=[
                "torch==1.13.0",
                "torchvision==0.14.0",
                "numpy==1.24.0",
                "Pillow==10.0.0",
                "scipy==1.9.0",
                "scikit-learn==1.2.0",
                "matplotlib==3.7.0",
                "opencv-python==4.8.0.76",
            ],
            solution_requirements=[
                "torch==1.13.0",
                "torchvision==0.14.0",
                "numpy==1.21.6",
                "Pillow==9.5.0",
                "scipy==1.9.0",
                "scikit-learn==1.2.0",
                "matplotlib==3.7.0",
                "opencv-python==4.7.0.72",
            ],
            max_steps=35,
        ),
    ]


def get_scenario(task_id: str) -> Scenario:
    scenarios = {s.task_id: s for s in get_all_scenarios()}
    if task_id not in scenarios:
        raise ValueError(f"Unknown task_id: {task_id}")
    return scenarios[task_id]
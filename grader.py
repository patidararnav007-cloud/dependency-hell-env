import subprocess
import sys
import tempfile
import os
import venv


def create_sandbox() -> str:
    sandbox_dir = tempfile.mkdtemp(prefix="depenv_sandbox_")
    venv.create(sandbox_dir, with_pip=True)
    return sandbox_dir


def get_python_path(sandbox_dir: str) -> str:
    if sys.platform == "win32":
        return os.path.join(sandbox_dir, "Scripts", "python.exe")
    return os.path.join(sandbox_dir, "bin", "python")


def run_pip_install(sandbox_dir: str, requirements: list[str]) -> tuple[bool, list[str]]:
    python = get_python_path(sandbox_dir)
    req_text = "\n".join(requirements)

    req_file = os.path.join(sandbox_dir, "requirements.txt")
    with open(req_file, "w") as f:
        f.write(req_text)

    result = subprocess.run(
        [python, "-m", "pip", "install", "-r", req_file, "--quiet"],
        capture_output=True,
        text=True,
        timeout=120,
    )

    errors = []
    if result.returncode != 0:
        for line in result.stderr.splitlines():
            if any(kw in line.lower() for kw in ["error", "conflict", "incompatible"]):
                errors.append(line.strip())

    return result.returncode == 0, errors


def count_successful_imports(sandbox_dir: str, requirements: list[str]) -> int:
    python = get_python_path(sandbox_dir)
    count = 0

    for req in requirements:
        pkg_name = req.split("==")[0].split(">=")[0].split("<=")[0].strip()
        import_name = normalize_import_name(pkg_name)

        result = subprocess.run(
            [python, "-c", f"import {import_name}"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            count += 1

    return count


def normalize_import_name(pkg_name: str) -> str:
    mapping = {
        "scikit-learn": "sklearn",
        "opencv-python": "cv2",
        "Pillow": "PIL",
        "apache-airflow": "airflow",
        "pytorch": "torch",
    }
    return mapping.get(pkg_name, pkg_name.replace("-", "_").lower())


def cleanup_sandbox(sandbox_dir: str) -> None:
    import shutil
    shutil.rmtree(sandbox_dir, ignore_errors=True)


def score_requirements(requirements: list[str]) -> tuple[float, list[str], int]:
    sandbox_dir = create_sandbox()

    try:
        install_success, errors = run_pip_install(sandbox_dir, requirements)

        if not install_success and not errors:
            errors = ["Install failed with unknown error"]

        successful = count_successful_imports(sandbox_dir, requirements)
        total = len(requirements)

        raw = round(successful / total, 4) if total > 0 else 0.01
        score = max(0.01, min(0.99, raw))

        return score, errors, successful

    finally:
        cleanup_sandbox(sandbox_dir)
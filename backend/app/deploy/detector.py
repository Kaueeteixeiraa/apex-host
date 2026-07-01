import json
from pathlib import Path


def detect_project_type(repo_path: Path) -> dict[str, str | None]:
    package_json = repo_path / "package.json"
    if package_json.exists():
        try:
            data = json.loads(package_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
        scripts = data.get("scripts", {})
        if "next" in deps:
            return {
                "project_type": "nextjs",
                "install_command": "npm install",
                "build_command": scripts.get("build", "npm run build"),
                "start_command": scripts.get("start", "npm run start"),
                "output_directory": ".next",
            }
        if "vite" in deps or "react" in deps:
            return {
                "project_type": "react-vite",
                "install_command": "npm install",
                "build_command": scripts.get("build", "npm run build"),
                "start_command": "npx serve -s dist",
                "output_directory": "dist",
            }
        return {
            "project_type": "node",
            "install_command": "npm install",
            "build_command": scripts.get("build"),
            "start_command": scripts.get("start", "npm run start"),
            "output_directory": None,
        }

    requirements = repo_path / "requirements.txt"
    main_py = repo_path / "main.py"
    app_py = repo_path / "app.py"
    if requirements.exists():
        text = requirements.read_text(encoding="utf-8", errors="ignore").lower()
        if "fastapi" in text:
            return {
                "project_type": "fastapi",
                "install_command": "pip install -r requirements.txt",
                "build_command": None,
                "start_command": "uvicorn main:app --host 0.0.0.0 --port 8000",
                "output_directory": None,
            }
        if "flask" in text or app_py.exists():
            return {
                "project_type": "flask",
                "install_command": "pip install -r requirements.txt",
                "build_command": None,
                "start_command": "gunicorn app:app --bind 0.0.0.0:5000",
                "output_directory": None,
            }
    if main_py.exists() or app_py.exists():
        return {
            "project_type": "python",
            "install_command": None,
            "build_command": None,
            "start_command": "python main.py",
            "output_directory": None,
        }
    if (repo_path / "index.html").exists():
        return {
            "project_type": "static",
            "install_command": None,
            "build_command": None,
            "start_command": None,
            "output_directory": ".",
        }
    return {
        "project_type": "manual",
        "install_command": None,
        "build_command": None,
        "start_command": None,
        "output_directory": None,
    }

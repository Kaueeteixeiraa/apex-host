from typing import Any


PROJECT_TEMPLATES: list[dict[str, Any]] = [
    {
        "id": "static-html",
        "name": "HTML/CSS/JS puro",
        "description": "Site estatico simples com deploy rapido e sem runtime.",
        "stack": "HTML, CSS, JavaScript",
        "install_command": None,
        "build_command": None,
        "start_command": "npx serve -s .",
        "output_directory": ".",
        "internal_port": 3000,
        "project_type": "static",
        "icon": "FileCode2",
        "preview": "Landing estatica com hero neon e secoes responsivas.",
        "tags": ["static", "html", "landing"],
    },
    {
        "id": "react-vite",
        "name": "React + Vite",
        "description": "Frontend moderno com build estatico em dist.",
        "stack": "React, Vite, TypeScript",
        "install_command": "npm install",
        "build_command": "npm run build",
        "start_command": "npx serve -s dist",
        "output_directory": "dist",
        "internal_port": 3000,
        "project_type": "react-vite",
        "icon": "Atom",
        "preview": "Dashboard/app SPA com transicoes suaves.",
        "tags": ["react", "vite", "spa"],
    },
    {
        "id": "nextjs",
        "name": "Next.js",
        "description": "Aplicacao Next com servidor Node.",
        "stack": "Next.js, Node.js",
        "install_command": "npm install",
        "build_command": "npm run build",
        "start_command": "npm run start",
        "output_directory": ".next",
        "internal_port": 3000,
        "project_type": "nextjs",
        "icon": "Triangle",
        "preview": "SSR/SPA com rotas modernas.",
        "tags": ["nextjs", "node", "ssr"],
    },
    {
        "id": "node-express",
        "name": "Node.js/Express",
        "description": "API ou site dinamico com Express.",
        "stack": "Node.js, Express",
        "install_command": "npm install",
        "build_command": None,
        "start_command": "npm start",
        "output_directory": None,
        "internal_port": 3000,
        "project_type": "node",
        "icon": "Server",
        "preview": "API HTTP com health check.",
        "tags": ["node", "express", "api"],
    },
    {
        "id": "python-flask",
        "name": "Python Flask",
        "description": "App Python leve para paginas e APIs simples.",
        "stack": "Python, Flask",
        "install_command": "pip install -r requirements.txt",
        "build_command": None,
        "start_command": "gunicorn app:app --bind 0.0.0.0:5000",
        "output_directory": None,
        "internal_port": 5000,
        "project_type": "flask",
        "icon": "FlaskConical",
        "preview": "Servico Flask com endpoint /health.",
        "tags": ["python", "flask", "api"],
    },
    {
        "id": "python-fastapi",
        "name": "Python FastAPI",
        "description": "API Python com docs automaticos e ASGI.",
        "stack": "Python, FastAPI",
        "install_command": "pip install -r requirements.txt",
        "build_command": None,
        "start_command": "uvicorn app.main:app --host 0.0.0.0 --port 8000",
        "output_directory": None,
        "internal_port": 8000,
        "project_type": "fastapi",
        "icon": "Gauge",
        "preview": "API rapida com OpenAPI.",
        "tags": ["python", "fastapi", "api"],
    },
    {
        "id": "simple-landing",
        "name": "Landing page simples",
        "description": "Pagina de captura institucional com secoes prontas.",
        "stack": "HTML, Tailwind-ready",
        "install_command": None,
        "build_command": None,
        "start_command": "npx serve -s .",
        "output_directory": ".",
        "internal_port": 3000,
        "project_type": "static",
        "icon": "Sparkles",
        "preview": "Hero, beneficios, CTA e FAQ.",
        "tags": ["landing", "marketing", "static"],
    },
    {
        "id": "apex-institutional",
        "name": "Pagina institucional Apex",
        "description": "Template premium para paginas da Apex Technologies.",
        "stack": "React + Vite",
        "install_command": "npm install",
        "build_command": "npm run build",
        "start_command": "npx serve -s dist",
        "output_directory": "dist",
        "internal_port": 3000,
        "project_type": "react-vite",
        "icon": "Gem",
        "preview": "Visual dark premium com azul neon.",
        "tags": ["apex", "brand", "premium"],
    },
    {
        "id": "apex-realms",
        "name": "Apex Realms",
        "description": "Plataforma de RPG de mesa online da Apex",
        "stack": "Python, Flask, Gunicorn",
        "install_command": "pip install -r requirements.txt",
        "build_command": None,
        "start_command": "gunicorn app:app --bind 0.0.0.0:5000",
        "output_directory": None,
        "internal_port": 5000,
        "project_type": "flask",
        "icon": "Dices",
        "preview": "Projeto interno Apex para validar deploy real com login, campanhas e mesas.",
        "tags": ["apex", "interno", "rpg"],
        "template_type": "Projeto interno Apex",
        "category": "RPG / Plataforma interna",
        "github_url": "https://github.com/Kaueeteixeiraa/apex-realms.git",
        "branch": "main",
        "suggested_domain": "realms.{BASE_DOMAIN}",
        "is_internal": True,
    },
]


def detect_framework(files: list[str], package_json: dict[str, Any] | None = None) -> dict[str, Any]:
    normalized = {item.replace("\\", "/").lower().strip("/") for item in files}
    deps = {}
    if package_json:
        deps.update(package_json.get("dependencies") or {})
        deps.update(package_json.get("devDependencies") or {})
    reasons: list[str] = []

    def has_file(name: str) -> bool:
        return name.lower() in normalized

    if has_file("dockerfile"):
        reasons.append("Dockerfile encontrado; respeitar imagem customizada.")
        return _result("Dockerfile", "docker", None, None, None, None, 3000, "container", 0.92, reasons)
    if has_file("next.config.js") or has_file("next.config.mjs") or "next" in deps:
        reasons.append("next.config ou dependencia next detectada.")
        return _result("Next.js", "nextjs", "npm run build", "npm run start", "npm install", ".next", 3000, "node", 0.9, reasons)
    if has_file("vite.config.js") or has_file("vite.config.ts") or "vite" in deps:
        reasons.append("vite.config ou dependencia vite detectada.")
        if "react" in deps:
            reasons.append("dependencia react detectada; servir build estatico em container Nginx.")
        return _result("React + Vite", "react-vite", "npm run build", "npx serve -s dist", "npm install", "dist", 3000, "static", 0.88, reasons)
    if has_file("package.json"):
        reasons.append("package.json encontrado sem framework especifico.")
        return _result("Node.js", "node", None, "npm start", "npm install", None, 3000, "node", 0.7, reasons)
    if has_file("requirements.txt") or has_file("pyproject.toml"):
        python_markers = " ".join(normalized)
        package_text = json_like(package_json)
        if "fastapi" in package_text or has_file("app/main.py") or "fastapi" in python_markers:
            reasons.append("Projeto Python com estrutura comum de FastAPI.")
            return _result("FastAPI", "fastapi", None, "uvicorn app.main:app --host 0.0.0.0 --port 8000", "pip install -r requirements.txt", None, 8000, "python", 0.72, reasons)
        if has_file("app.py") or "flask" in package_text or "flask" in python_markers:
            reasons.append("requirements.txt/pyproject.toml com app.py ou Flask detectado.")
            return _result("Flask", "flask", None, "gunicorn app:app --bind 0.0.0.0:5000", "pip install -r requirements.txt", None, 5000, "python", 0.78, reasons)
        reasons.append("requirements.txt/pyproject.toml detectado.")
        return _result("Python", "python", None, "python app.py", "pip install -r requirements.txt", None, 5000, "python", 0.64, reasons)
    if has_file("index.html"):
        reasons.append("index.html detectado na raiz.")
        return _result("HTML estatico", "static", None, "npx serve -s .", None, ".", 3000, "static", 0.75, reasons)
    reasons.append("Nenhum arquivo conhecido informado; usando configuracao manual.")
    return _result("Manual", "manual", None, None, None, None, 3000, "manual", 0.3, reasons)


def json_like(value: dict[str, Any] | None) -> str:
    if not value:
        return ""
    return " ".join(str(item).lower() for item in value.values())


def _result(
    framework: str,
    project_type: str,
    build_command: str | None,
    start_command: str | None,
    install_command: str | None,
    output_directory: str | None,
    default_port: int,
    runtime: str,
    confidence: float,
    reasons: list[str],
) -> dict[str, Any]:
    return {
        "framework": framework,
        "project_type": project_type,
        "build_command": build_command,
        "start_command": start_command,
        "install_command": install_command,
        "output_directory": output_directory,
        "default_port": default_port,
        "runtime": runtime,
        "confidence": confidence,
        "reasons": reasons,
    }

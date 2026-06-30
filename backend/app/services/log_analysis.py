from app.models import Deploy, LogEntry


ERROR_SIGNALS = {
    "dependency": ["module not found", "cannot find module", "no module named", "dependency", "npm err", "pip error"],
    "build": ["build failed", "compilation failed", "failed to compile", "syntaxerror", "typeerror"],
    "port": ["address already in use", "eaddrinuse", "port"],
    "env": ["environment variable", "env", "secret", "database_url", "keyerror"],
    "docker": ["docker", "container", "image", "daemon"],
    "timeout": ["timeout", "timed out", "deadline"],
    "permission": ["permission denied", "eacces", "forbidden"],
}


def analyze_deploy_logs(deploy: Deploy | None, logs: list[LogEntry]) -> dict:
    lines: list[str] = []
    if deploy:
        for source in [deploy.error, deploy.logs]:
            if source:
                lines.extend(source.splitlines())
    lines.extend(log.message for log in logs)
    compact_lines = [line.strip() for line in lines if line and line.strip()]
    lowered = [line.lower() for line in compact_lines]
    matches: list[str] = []
    for signal, needles in ERROR_SIGNALS.items():
        if any(any(needle in line for needle in needles) for line in lowered):
            matches.append(signal)
    important = [
        line
        for line in compact_lines
        if any(word in line.lower() for word in ["error", "failed", "exception", "timeout", "denied", "not found", "cannot"])
    ][:8]
    if not compact_lines:
        return {
            "summary": "Nao ha logs suficientes para analisar este deploy.",
            "possible_cause": "O deploy ainda nao gerou saida ou os logs foram limpos.",
            "suggested_fix": "Execute um novo deploy dry run e volte a analisar quando houver logs.",
            "severity": "info",
            "important_lines": [],
            "signals": [],
        }
    if "dependency" in matches:
        cause = "Dependencia ausente ou instalacao incompleta."
        fix = "Confira package.json/requirements.txt, rode o install localmente e valide se o comando de build usa o gerenciador correto."
        severity = "high"
    elif "env" in matches:
        cause = "Variavel de ambiente ou segredo obrigatorio parece ausente."
        fix = "Revise as envs do projeto no painel, confirme nomes exatos e rode um deploy dry run antes do deploy real."
        severity = "high"
    elif "port" in matches:
        cause = "A aplicacao tentou subir em uma porta ocupada ou diferente da configurada."
        fix = "Garanta que o app use a porta interna configurada no Apex Host e que leia PORT quando existir."
        severity = "medium"
    elif "timeout" in matches:
        cause = "O build ou health check excedeu o tempo limite."
        fix = "Otimize o build, aumente recursos do plano ou ajuste o endpoint de health check para responder rapidamente."
        severity = "medium"
    elif "docker" in matches:
        cause = "Falha relacionada ao Docker/container."
        fix = "Verifique se Docker esta ativo na VPS, se a imagem foi criada e se a rede do Apex Host existe."
        severity = "high"
    elif "build" in matches:
        cause = "Erro de build ou compilacao."
        fix = "Leia as linhas destacadas, reproduza npm run build/pip localmente e corrija erro de sintaxe/tipo antes de redeploy."
        severity = "high"
    else:
        cause = "O analisador local nao encontrou um padrao conhecido com alta confianca."
        fix = "Filtre por logs de erro, confira o primeiro stack trace e valide comandos de install/build/start."
        severity = "info"
    return {
        "summary": f"Analise local encontrou {len(matches)} sinal(is) relevante(s) em {len(compact_lines)} linha(s).",
        "possible_cause": cause,
        "suggested_fix": fix,
        "severity": severity,
        "important_lines": important,
        "signals": matches,
    }

from typing import Any


INTERNAL_PLANS: list[dict[str, Any]] = [
    {
        "id": "free",
        "name": "Free",
        "description": "Entrada controlada para validar um projeto pequeno.",
        "audience": "Clientes novos",
        "price_label": "Sem pagamento",
        "highlighted": False,
        "limits": {
            "projects": 1,
            "deploys_per_day": 10,
            "ram_mb_per_project": 256,
            "cpu_per_project": "0.25 vCPU",
            "custom_domains": 1,
            "high_availability": False,
            "automatic_backups": False,
            "advanced_logs": False,
            "support": "comunidade",
        },
        "features": ["Deploy dry run", "Subdominio Apex", "Logs basicos", "Fallback manual"],
    },
    {
        "id": "pro",
        "name": "Pro",
        "description": "Para projetos em producao com rollback e dominios reais.",
        "audience": "Devs e pequenos negocios",
        "price_label": "Plano interno",
        "highlighted": True,
        "limits": {
            "projects": 5,
            "deploys_per_day": 50,
            "ram_mb_per_project": 1024,
            "cpu_per_project": "1 vCPU",
            "custom_domains": 5,
            "high_availability": True,
            "automatic_backups": True,
            "advanced_logs": True,
            "support": "prioritario",
        },
        "features": ["Blue/green preparado", "Backups sob demanda", "Alertas", "Analise local de logs"],
    },
    {
        "id": "business",
        "name": "Business",
        "description": "Operacao com mais projetos, suporte e limites maiores.",
        "audience": "Empresas",
        "price_label": "Contrato Apex",
        "highlighted": False,
        "limits": {
            "projects": 20,
            "deploys_per_day": 200,
            "ram_mb_per_project": 4096,
            "cpu_per_project": "2 vCPU",
            "custom_domains": 20,
            "high_availability": True,
            "automatic_backups": True,
            "advanced_logs": True,
            "support": "SLA interno",
        },
        "features": ["Multi-node", "CDN/fallback", "Auditoria ampliada", "Suporte por ticket"],
    },
    {
        "id": "apex_internal",
        "name": "Interno Apex",
        "description": "Plano ilimitado para operacao e testes internos da Apex.",
        "audience": "Equipe Apex",
        "price_label": "Interno",
        "highlighted": False,
        "limits": {
            "projects": None,
            "deploys_per_day": None,
            "ram_mb_per_project": None,
            "cpu_per_project": "custom",
            "custom_domains": None,
            "high_availability": True,
            "automatic_backups": True,
            "advanced_logs": True,
            "support": "interno",
        },
        "features": ["Sem limites padrao", "Admin total", "Testes de VPS", "Recursos experimentais"],
    },
]


def get_plan(plan_id: str) -> dict[str, Any]:
    for plan in INTERNAL_PLANS:
        if plan["id"] == plan_id:
            return plan
    return INTERNAL_PLANS[0]


def limits_for_plan(plan_id: str) -> dict[str, Any]:
    return dict(get_plan(plan_id)["limits"])

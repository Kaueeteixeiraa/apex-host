from typing import Any


INTERNAL_PROFILES: dict[str, dict[str, Any]] = {
    "viewer": {
        "projects": 0,
        "deploys_per_day": 0,
        "custom_domains": 0,
        "can_create_projects": False,
        "can_deploy": False,
        "approval_required": False,
    },
    "dev": {
        "projects": 10,
        "deploys_per_day": 100,
        "custom_domains": 10,
        "can_create_projects": True,
        "can_deploy": True,
        "approval_required": False,
    },
    "admin_internal": {
        "projects": None,
        "deploys_per_day": None,
        "custom_domains": None,
        "can_create_projects": True,
        "can_deploy": True,
        "approval_required": False,
    },
    "pending_approval": {
        "projects": 0,
        "deploys_per_day": 0,
        "custom_domains": 0,
        "can_create_projects": False,
        "can_deploy": False,
        "approval_required": True,
    },
}


def limits_for_profile(profile_id: str) -> dict[str, Any]:
    return dict(INTERNAL_PROFILES.get(profile_id, INTERNAL_PROFILES["viewer"]))

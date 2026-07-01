from sqlalchemy.orm import Session

from app.models import PlatformSetting
from app.services.access_profiles import limits_for_profile


def get_or_create_platform_settings(db: Session) -> PlatformSetting:
    settings = db.get(PlatformSetting, 1)
    if settings:
        legacy_profiles = {"fr" + "ee", "pr" + "o", "busi" + "ness", "pending_admin_review"}
        if settings.default_user_profile in legacy_profiles:
            settings.default_user_profile = "viewer"
            settings.default_user_limits = limits_for_profile("viewer")
            db.commit()
            db.refresh(settings)
        return settings
    settings = PlatformSetting(
        id=1,
        platform_name="Apex Host",
        primary_color="#18b6ff",
        allow_registration=True,
        require_account_approval=True,
        default_user_profile="viewer",
        default_user_limits=limits_for_profile("viewer"),
        smtp_config={"enabled": False, "host": "", "from": ""},
        alert_config={"email": False, "webhook": "", "critical_only": True},
        backup_config={"automatic": False, "retention_days": 7},
        cdn_config={"provider": "", "fallback_enabled": False},
    )
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings

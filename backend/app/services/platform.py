from sqlalchemy.orm import Session

from app.models import PlatformSetting
from app.services.plans import limits_for_plan


def get_or_create_platform_settings(db: Session) -> PlatformSetting:
    settings = db.get(PlatformSetting, 1)
    if settings:
        return settings
    settings = PlatformSetting(
        id=1,
        platform_name="Apex Host",
        primary_color="#18b6ff",
        allow_registration=True,
        require_account_approval=True,
        default_user_plan="free",
        default_user_limits=limits_for_plan("free"),
        smtp_config={"enabled": False, "host": "", "from": ""},
        alert_config={"email": False, "webhook": "", "critical_only": True},
        backup_config={"automatic": False, "retention_days": 7},
        cdn_config={"provider": "", "fallback_enabled": False},
    )
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings

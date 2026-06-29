from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import decrypt_secret, encrypt_secret, mask_secret
from app.db.session import get_db
from app.deps import get_current_user, require_project_access
from app.models import EnvironmentVariable, LogEntry, User
from app.schemas import EnvVarCreate, EnvVarRead, EnvVarUpdate


router = APIRouter(prefix="/projects/{project_id}/env", tags=["environment"])


def _read(item: EnvironmentVariable) -> EnvVarRead:
    value = decrypt_secret(item.value_encrypted)
    return EnvVarRead(
        id=item.id,
        project_id=item.project_id,
        key=item.key,
        is_secret=item.is_secret,
        masked_value=mask_secret(value) if item.is_secret else value,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.get("", response_model=list[EnvVarRead])
def list_env_vars(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[EnvVarRead]:
    require_project_access(project_id, db, user)
    items = db.query(EnvironmentVariable).filter(EnvironmentVariable.project_id == project_id).order_by(EnvironmentVariable.key).all()
    return [_read(item) for item in items]


@router.post("", response_model=EnvVarRead)
def create_env_var(
    project_id: int,
    payload: EnvVarCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EnvVarRead:
    require_project_access(project_id, db, user)
    exists = db.query(EnvironmentVariable).filter(
        EnvironmentVariable.project_id == project_id,
        EnvironmentVariable.key == payload.key,
    ).first()
    if exists:
        raise HTTPException(status_code=409, detail="Environment variable already exists")
    item = EnvironmentVariable(
        project_id=project_id,
        key=payload.key,
        value_encrypted=encrypt_secret(payload.value),
        is_secret=payload.is_secret,
    )
    db.add(item)
    db.add(LogEntry(project_id=project_id, type="system", message=f"Environment variable {payload.key} created"))
    db.commit()
    db.refresh(item)
    return _read(item)


@router.patch("/{env_id}", response_model=EnvVarRead)
def update_env_var(
    project_id: int,
    env_id: int,
    payload: EnvVarUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EnvVarRead:
    require_project_access(project_id, db, user)
    item = db.get(EnvironmentVariable, env_id)
    if item is None or item.project_id != project_id:
        raise HTTPException(status_code=404, detail="Environment variable not found")
    data = payload.model_dump(exclude_unset=True)
    if "value" in data and data["value"] is not None:
        item.value_encrypted = encrypt_secret(data["value"])
    if "is_secret" in data and data["is_secret"] is not None:
        item.is_secret = data["is_secret"]
    db.commit()
    db.refresh(item)
    return _read(item)


@router.delete("/{env_id}")
def delete_env_var(
    project_id: int,
    env_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    require_project_access(project_id, db, user)
    item = db.get(EnvironmentVariable, env_id)
    if item is None or item.project_id != project_id:
        raise HTTPException(status_code=404, detail="Environment variable not found")
    db.delete(item)
    db.add(LogEntry(project_id=project_id, type="system", message=f"Environment variable {item.key} removed"))
    db.commit()
    return {"ok": True}

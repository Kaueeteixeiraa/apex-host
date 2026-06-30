from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user, require_project_access
from app.models import SupportMessage, SupportTicket, User
from app.schemas import SupportMessageCreate, SupportMessageRead, SupportTicketCreate, SupportTicketRead, SupportTicketUpdate
from app.services.audit import record_audit


router = APIRouter(prefix="/support", tags=["support"])


@router.get("/tickets", response_model=list[SupportTicketRead])
def list_tickets(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[SupportTicket]:
    query = db.query(SupportTicket)
    if user.role != "admin":
        query = query.filter(SupportTicket.user_id == user.id)
    return query.order_by(SupportTicket.updated_at.desc()).all()


@router.post("/tickets", response_model=SupportTicketRead)
def create_ticket(
    payload: SupportTicketCreate,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SupportTicket:
    if payload.project_id is not None:
        require_project_access(payload.project_id, db, user)
    ticket = SupportTicket(
        user_id=user.id,
        project_id=payload.project_id,
        subject=payload.subject,
        category=payload.category,
        priority=payload.priority,
        status="open",
    )
    db.add(ticket)
    db.flush()
    db.add(SupportMessage(ticket_id=ticket.id, user_id=user.id, body=payload.body, is_admin_reply=user.role == "admin"))
    record_audit(
        db,
        "support.ticket_created",
        user=user,
        project_id=payload.project_id,
        target_type="support_ticket",
        target_id=ticket.id,
        ip_address=request.client.host if request.client else None,
        details={"category": payload.category, "priority": payload.priority, "user_agent": request.headers.get("user-agent")},
    )
    db.commit()
    db.refresh(ticket)
    return ticket


def _ticket_for_user(ticket_id: int, user: User, db: Session) -> SupportTicket:
    ticket = db.get(SupportTicket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if user.role != "admin" and ticket.user_id != user.id:
        raise HTTPException(status_code=403, detail="Ticket access denied")
    return ticket


@router.get("/tickets/{ticket_id}", response_model=SupportTicketRead)
def get_ticket(ticket_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> SupportTicket:
    return _ticket_for_user(ticket_id, user, db)


@router.patch("/tickets/{ticket_id}", response_model=SupportTicketRead)
def update_ticket(
    ticket_id: int,
    payload: SupportTicketUpdate,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SupportTicket:
    ticket = _ticket_for_user(ticket_id, user, db)
    if user.role != "admin" and payload.status not in {None, "resolved"}:
        raise HTTPException(status_code=403, detail="Only admins can move tickets to reviewing")
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(ticket, key, value)
    record_audit(
        db,
        "support.ticket_updated",
        user=user,
        project_id=ticket.project_id,
        target_type="support_ticket",
        target_id=ticket.id,
        ip_address=request.client.host if request.client else None,
        details={"fields": sorted(data.keys()), "user_agent": request.headers.get("user-agent")},
    )
    db.commit()
    db.refresh(ticket)
    return ticket


@router.get("/tickets/{ticket_id}/messages", response_model=list[SupportMessageRead])
def list_messages(ticket_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[SupportMessage]:
    ticket = _ticket_for_user(ticket_id, user, db)
    return ticket.messages


@router.post("/tickets/{ticket_id}/messages", response_model=SupportMessageRead)
def create_message(
    ticket_id: int,
    payload: SupportMessageCreate,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SupportMessage:
    ticket = _ticket_for_user(ticket_id, user, db)
    message = SupportMessage(ticket_id=ticket.id, user_id=user.id, body=payload.body, is_admin_reply=user.role == "admin")
    ticket.status = "reviewing" if user.role == "admin" else "open"
    db.add(message)
    record_audit(
        db,
        "support.message_created",
        user=user,
        project_id=ticket.project_id,
        target_type="support_ticket",
        target_id=ticket.id,
        ip_address=request.client.host if request.client else None,
        details={"is_admin_reply": user.role == "admin", "user_agent": request.headers.get("user-agent")},
    )
    db.commit()
    db.refresh(message)
    return message

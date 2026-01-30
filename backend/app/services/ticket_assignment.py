"""Ticket Assignment Service"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.ticket import Ticket, TicketStatus
from app.models.user import User
from typing import Optional

def assign_ticket_to_user(db: Session, ticket: Ticket) -> Optional[User]:
    """
    Auto-assign ticket to user in target department with least open tickets.
    Returns assigned user or None if no users in department.
    """
    # Get all active users in target department
    users = db.query(User).filter(
        User.dept_id == ticket.to_dept_id,
        User.is_active == True
    ).all()
    
    if not users:
        return None
    
    # Count open tickets per user
    user_ticket_counts = {}
    for user in users:
        count = db.query(Ticket).filter(
            Ticket.assigned_to_user_id == user.id,
            Ticket.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.WAITING])
        ).count()
        user_ticket_counts[user.id] = count
    
    # Assign to user with minimum open tickets
    if user_ticket_counts:
        min_count = min(user_ticket_counts.values())
        assigned_user_id = min(
            (uid for uid, count in user_ticket_counts.items() if count == min_count),
            key=lambda uid: user_ticket_counts[uid]
        )
        assigned_user = next(u for u in users if u.id == assigned_user_id)
        return assigned_user
    
    # Fallback: assign to first user
    return users[0] if users else None


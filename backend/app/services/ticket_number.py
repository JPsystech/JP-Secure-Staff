"""Ticket Number Generation Service"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.ticket import TicketCounter
import logging

logger = logging.getLogger(__name__)

def generate_ticket_number(db: Session) -> str:
    """
    Generate next ticket number in format TCK-0001, TCK-0002, etc.
    Uses atomic counter to prevent duplicates.
    """
    # Get or create counter
    counter = db.query(TicketCounter).filter(TicketCounter.id == 1).first()
    
    if not counter:
        counter = TicketCounter(id=1, last_number=0)
        db.add(counter)
        db.flush()
    
    # Increment atomically
    counter.last_number += 1
    db.commit()
    db.refresh(counter)
    
    # Format: TCK-0001
    ticket_no = f"TCK-{counter.last_number:04d}"
    
    logger.info(f"Generated ticket number: {ticket_no}")
    return ticket_no


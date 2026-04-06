from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Date
from sqlalchemy.orm import relationship
from src.db.database import Base
import datetime

class Email(Base):
    __tablename__ = "emails"
    id = Column(Integer, primary_key=True, index=True)
    sender = Column(String, index=True)
    subject = Column(String)
    received_time = Column(DateTime)
    body_summary = Column(Text) # the cleaned version
    views = relationship("UnderlyingView", back_populates="email")

class UnderlyingView(Base):
    __tablename__ = "underlying_views"
    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id"))
    underlying = Column(String, index=True) # e.g., "EURUSD"
    sentiment = Column(String) # "bullish", "bearish", "neutral"
    bank = Column(String, index=True) # e.g., "JPMorgan", "Goldman Sachs"
    date = Column(Date, index=True) # derived from email received_time
    rationale = Column(Text)
    levels = Column(String)

    email = relationship("Email", back_populates="views")

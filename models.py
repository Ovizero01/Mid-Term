from database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime
from datetime import datetime, timezone

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    email = Column(String)
    hash_password = Column(String)

class Transaction(Base):
    __tablename__ = 'transaction'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    amount = Column(Float)
    type = Column(String)
    category = Column(String)
    date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    owner_id = Column(Integer, ForeignKey("user.id"))
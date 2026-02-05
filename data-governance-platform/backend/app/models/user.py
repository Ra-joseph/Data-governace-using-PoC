from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """User model representing platform users."""
    
    __tablename__ = "users"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)  # For future auth implementation
    
    # Profile
    full_name = Column(String(255), nullable=False)
    
    # Role & Organization
    role = Column(String(50), nullable=False, default="data_consumer")  # data_owner, data_consumer, data_steward, admin
    team = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    datasets = relationship("Dataset", back_populates="owner")
    subscriptions = relationship("Subscription", foreign_keys="Subscription.consumer_id", back_populates="consumer")
    
    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role}', email='{self.email}')>"

"""
Database model for platform user management.

This module defines the User model which represents all platform users including
data owners, data consumers, data stewards, and administrators. It handles user
authentication, roles, permissions, and relationships to datasets and subscriptions.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """
    User model for platform authentication and authorization.

    This model represents all types of users in the data governance platform,
    including data owners who publish datasets, data consumers who subscribe to
    datasets, data stewards who approve subscriptions, and system administrators.
    It manages user profiles, roles, organizational information, and tracks
    authentication status.

    Attributes:
        id: Primary key identifier
        email: Unique email address for user login and communication
        username: Unique username for display and identification
        hashed_password: Encrypted password hash (for future auth implementation)
        full_name: User's complete name
        role: User role (data_owner, data_consumer, data_steward, admin)
        team: Team or group affiliation
        department: Organizational department
        is_active: Account status flag (active/inactive)
        is_verified: Email verification status
        created_at: Account creation timestamp
        last_login: Most recent login timestamp
        datasets: Relationship to owned Dataset objects (for data owners)
        subscriptions: Relationship to Subscription objects (for consumers)

    Example:
        >>> user = User(
        ...     email="john.doe@example.com",
        ...     username="jdoe",
        ...     full_name="John Doe",
        ...     role="data_owner",
        ...     team="Analytics",
        ...     department="Engineering"
        ... )
        >>> db.add(user)
        >>> db.commit()
    """
    
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
        """
        String representation of the user.

        Returns:
            String containing username, role, and email.
        """
        return f"<User(username='{self.username}', role='{self.role}', email='{self.email}')>"

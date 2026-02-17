"""
Database model for consumer subscription management.

This module defines the Subscription model which represents a data consumer's
subscription to a dataset. It handles the complete subscription lifecycle including
request submission, approval workflow, SLA requirements, access credentials, and
expiration management.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Subscription(Base):
    """
    Data subscription model for managing dataset access requests.

    This model tracks consumer subscriptions to datasets, managing the complete
    lifecycle from initial request through approval, access provisioning, and
    eventual expiration. It captures SLA requirements, quality expectations,
    data filters, and maintains a full audit trail of the approval workflow.

    Attributes:
        id: Primary key identifier
        dataset_id: Foreign key to the subscribed dataset
        contract_id: Foreign key to the associated data contract (set on approval)
        consumer_id: Foreign key to the consumer user (if registered)
        consumer_name: Full name of the data consumer
        consumer_email: Contact email for the consumer
        consumer_team: Team or department of the consumer
        purpose: Business justification for data access
        use_case: Type of use (analytics, ml, reporting, dashboard, api, other)
        sla_freshness: Required data freshness (1h, 6h, 24h, weekly)
        sla_availability: Required availability SLA (99.9%, 99.5%, 99.0%)
        sla_query_performance: Required query performance (<1s, <5s, <30s)
        quality_completeness: Minimum completeness percentage required
        quality_accuracy: Minimum accuracy percentage required
        data_filters: JSON filters for data segmentation (regions, date ranges, etc.)
        status: Workflow status (pending, approved, rejected, active, cancelled)
        approved_by: Foreign key to approving user (data steward)
        approved_at: Timestamp of approval/rejection
        rejection_reason: Explanation if rejected
        access_granted: Boolean flag for active access
        access_credentials: Encrypted credentials for data access
        access_endpoint: Connection string or API endpoint for access
        created_at: Timestamp of subscription creation
        updated_at: Timestamp of last modification
        expires_at: Expiration timestamp for time-limited access
        dataset: Relationship to Dataset model
        contract: Relationship to Contract model
        consumer: Relationship to User model (consumer)
        approver: Relationship to User model (approver)

    Example:
        >>> subscription = Subscription(
        ...     dataset_id=1,
        ...     consumer_name="Jane Smith",
        ...     consumer_email="jane@example.com",
        ...     purpose="Customer analytics for Q1 reporting",
        ...     use_case="analytics",
        ...     status="pending"
        ... )
        >>> db.add(subscription)
        >>> db.commit()
    """
    
    __tablename__ = "subscriptions"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # References
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=True)
    consumer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Consumer Information
    consumer_name = Column(String(255), nullable=False)
    consumer_email = Column(String(255), nullable=False)
    consumer_team = Column(String(255), nullable=True)
    
    # Subscription Details
    purpose = Column(Text, nullable=False)
    use_case = Column(String(100), nullable=False)  # analytics, ml, reporting, etc.
    
    # SLA Requirements
    sla_freshness = Column(String(50), nullable=True)  # 1h, 6h, 24h, weekly
    sla_availability = Column(String(50), nullable=True)  # 99.9%, 99.5%, 99.0%
    sla_query_performance = Column(String(50), nullable=True)  # <1s, <5s, <30s
    
    # Quality Requirements
    quality_completeness = Column(Float, nullable=True)  # Percentage
    quality_accuracy = Column(Float, nullable=True)  # Percentage
    
    # Data Filters
    data_filters = Column(JSON, nullable=True)  # Segments, regions, date ranges
    
    # Approval Workflow
    status = Column(String(50), nullable=False, default="pending")  # pending, approved, rejected, active, cancelled
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Access Information
    access_granted = Column(Boolean, default=False)
    access_credentials = Column(Text, nullable=True)  # Encrypted in production
    access_endpoint = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    dataset = relationship("Dataset", back_populates="subscriptions")
    contract = relationship("Contract", back_populates="subscriptions")
    consumer = relationship("User", foreign_keys=[consumer_id], back_populates="subscriptions")
    approver = relationship("User", foreign_keys=[approved_by])
    
    def __repr__(self):
        """
        String representation of the subscription.

        Returns:
            String containing consumer name, dataset ID, and status.
        """
        return f"<Subscription(consumer='{self.consumer_name}', dataset_id={self.dataset_id}, status='{self.status}')>"

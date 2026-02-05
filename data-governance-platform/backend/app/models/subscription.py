from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Subscription(Base):
    """Subscription model representing a consumer's subscription to a dataset."""
    
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
        return f"<Subscription(consumer='{self.consumer_name}', dataset_id={self.dataset_id}, status='{self.status}')>"

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr
from enum import Enum


class SubscriptionStatus(str, Enum):
    """Subscription workflow status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    CANCELLED = "cancelled"


class UseCase(str, Enum):
    """Data use case types."""
    ANALYTICS = "analytics"
    ML = "ml"
    REPORTING = "reporting"
    DASHBOARD = "dashboard"
    API = "api"
    OTHER = "other"


class SLAFreshness(str, Enum):
    """Data freshness SLA options."""
    REAL_TIME = "real-time"
    ONE_HOUR = "1h"
    SIX_HOURS = "6h"
    TWENTY_FOUR_HOURS = "24h"
    WEEKLY = "weekly"


class SLAAvailability(str, Enum):
    """Data availability SLA options."""
    HIGH = "99.9%"
    MEDIUM = "99.5%"
    STANDARD = "99.0%"


class SLAQueryPerformance(str, Enum):
    """Query performance SLA options."""
    FAST = "<1s"
    MEDIUM = "<5s"
    SLOW = "<30s"


class SubscriptionCreate(BaseModel):
    """Schema for creating a subscription."""
    dataset_id: int
    consumer_name: str
    consumer_email: EmailStr
    consumer_team: Optional[str] = None
    purpose: str
    use_case: UseCase
    sla_freshness: Optional[SLAFreshness] = None
    sla_availability: Optional[SLAAvailability] = None
    sla_query_performance: Optional[SLAQueryPerformance] = None
    quality_completeness: Optional[float] = None
    quality_accuracy: Optional[float] = None
    data_filters: Optional[Dict[str, Any]] = None


class SubscriptionUpdate(BaseModel):
    """Schema for updating a subscription."""
    purpose: Optional[str] = None
    use_case: Optional[UseCase] = None
    sla_freshness: Optional[SLAFreshness] = None
    sla_availability: Optional[SLAAvailability] = None
    sla_query_performance: Optional[SLAQueryPerformance] = None
    quality_completeness: Optional[float] = None
    quality_accuracy: Optional[float] = None
    data_filters: Optional[Dict[str, Any]] = None


class SubscriptionApproval(BaseModel):
    """Schema for approving/rejecting subscription."""
    approved: bool
    rejection_reason: Optional[str] = None
    access_endpoint: Optional[str] = None
    access_credentials: Optional[str] = None


class SubscriptionResponse(BaseModel):
    """Schema for subscription response."""
    id: int
    dataset_id: int
    contract_id: Optional[int]
    consumer_name: str
    consumer_email: str
    consumer_team: Optional[str]
    purpose: str
    use_case: str
    sla_freshness: Optional[str]
    sla_availability: Optional[str]
    sla_query_performance: Optional[str]
    quality_completeness: Optional[float]
    quality_accuracy: Optional[float]
    data_filters: Optional[Dict[str, Any]]
    status: str
    access_granted: bool
    access_endpoint: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    expires_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class SubscriptionListResponse(BaseModel):
    """Schema for listing subscriptions."""
    total: int
    subscriptions: list[SubscriptionResponse]

"""
Pydantic schemas for subscription management and approval workflow.

This module defines request and response schemas for subscription operations
including consumer requests, SLA specifications, approval workflow, and access
credential management. It provides comprehensive data models for the complete
subscription lifecycle from request through approval and cancellation.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr
from enum import Enum


class SubscriptionStatus(str, Enum):
    """
    Subscription workflow status enumeration.

    Tracks subscription progression through approval and lifecycle states.

    Attributes:
        PENDING: Awaiting data steward approval
        APPROVED: Approved by steward, access granted
        REJECTED: Rejected by steward with reason
        ACTIVE: Currently active with valid access
        CANCELLED: Cancelled by consumer or steward, access revoked
    """
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    CANCELLED = "cancelled"


class UseCase(str, Enum):
    """
    Data use case type enumeration.

    Categorizes how consumers intend to use the data.

    Attributes:
        ANALYTICS: Ad-hoc analysis and exploration
        ML: Machine learning model training/inference
        REPORTING: Regular business reporting
        DASHBOARD: Interactive dashboard visualization
        API: API/application integration
        OTHER: Other use cases not listed above
    """
    ANALYTICS = "analytics"
    ML = "ml"
    REPORTING = "reporting"
    DASHBOARD = "dashboard"
    API = "api"
    OTHER = "other"


class SLAFreshness(str, Enum):
    """
    Data freshness SLA enumeration.

    Defines maximum acceptable data age.

    Attributes:
        REAL_TIME: Near real-time streaming data
        ONE_HOUR: Updated within 1 hour
        SIX_HOURS: Updated within 6 hours
        TWENTY_FOUR_HOURS: Daily updates
        WEEKLY: Weekly updates
    """
    REAL_TIME = "real-time"
    ONE_HOUR = "1h"
    SIX_HOURS = "6h"
    TWENTY_FOUR_HOURS = "24h"
    WEEKLY = "weekly"


class SLAAvailability(str, Enum):
    """
    Data availability SLA enumeration.

    Defines expected uptime percentage.

    Attributes:
        HIGH: 99.9% uptime (3.5 min downtime/month)
        MEDIUM: 99.5% uptime (3.6 hours downtime/month)
        STANDARD: 99.0% uptime (7.2 hours downtime/month)
    """
    HIGH = "99.9%"
    MEDIUM = "99.5%"
    STANDARD = "99.0%"


class SLAQueryPerformance(str, Enum):
    """
    Query performance SLA enumeration.

    Defines maximum acceptable query response time.

    Attributes:
        FAST: Sub-second response (<1s)
        MEDIUM: Fast response (<5s)
        SLOW: Acceptable for batch jobs (<30s)
    """
    FAST = "<1s"
    MEDIUM = "<5s"
    SLOW = "<30s"


class SubscriptionCreate(BaseModel):
    """
    Schema for creating a subscription request.

    Request model for consumers to subscribe to datasets with SLA and
    quality requirements.

    Attributes:
        dataset_id: ID of dataset to subscribe to
        consumer_name: Full name of requesting consumer
        consumer_email: Email address for communication
        consumer_team: Optional team or department
        purpose: Business justification for data access
        use_case: Type of intended use (analytics, ML, etc.)
        sla_freshness: Required data freshness
        sla_availability: Required availability percentage
        sla_query_performance: Required query response time
        quality_completeness: Required completeness percentage
        quality_accuracy: Required accuracy percentage
        data_filters: Optional filters for data segmentation
    """
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
    """
    Schema for updating a pending subscription.

    Request model for modifying subscription requests before approval.
    All fields are optional - only provided fields will be updated.

    Attributes:
        purpose: Updated business justification
        use_case: Updated use case type
        sla_freshness: Updated freshness requirement
        sla_availability: Updated availability requirement
        sla_query_performance: Updated performance requirement
        quality_completeness: Updated completeness threshold
        quality_accuracy: Updated accuracy threshold
        data_filters: Updated data filters
    """
    purpose: Optional[str] = None
    use_case: Optional[UseCase] = None
    sla_freshness: Optional[SLAFreshness] = None
    sla_availability: Optional[SLAAvailability] = None
    sla_query_performance: Optional[SLAQueryPerformance] = None
    quality_completeness: Optional[float] = None
    quality_accuracy: Optional[float] = None
    data_filters: Optional[Dict[str, Any]] = None


class SubscriptionApproval(BaseModel):
    """
    Schema for approving or rejecting a subscription.

    Request model for data steward approval decisions.

    Attributes:
        approved: Boolean approval decision
        rejection_reason: Reason for rejection (required if not approved)
        access_endpoint: Connection endpoint/URL (required if approved)
        access_credentials: Credentials for data access (required if approved)
    """
    approved: bool
    rejection_reason: Optional[str] = None
    access_endpoint: Optional[str] = None
    access_credentials: Optional[str] = None


class SubscriptionResponse(BaseModel):
    """
    Schema for subscription response.

    Response model containing complete subscription information including
    status, SLA requirements, and access details.

    Attributes:
        id: Unique subscription identifier
        dataset_id: ID of subscribed dataset
        contract_id: ID of associated contract (set on approval)
        consumer_name: Consumer's full name
        consumer_email: Consumer's email address
        consumer_team: Consumer's team or department
        purpose: Business justification
        use_case: Type of data use
        sla_freshness: Freshness requirement
        sla_availability: Availability requirement
        sla_query_performance: Performance requirement
        quality_completeness: Completeness threshold
        quality_accuracy: Accuracy threshold
        data_filters: Data segmentation filters
        status: Current workflow status
        access_granted: Whether access is currently granted
        access_endpoint: Connection endpoint (if approved)
        created_at: Request creation timestamp
        updated_at: Last modification timestamp
        expires_at: Access expiration timestamp
    """
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
    access_credentials: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime]
    expires_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class SubscriptionListResponse(BaseModel):
    """
    Schema for listing subscriptions with pagination.

    Response model for list endpoints with total count and subscription array.

    Attributes:
        total: Total number of subscriptions matching filters
        subscriptions: List of subscription response objects
    """
    total: int
    subscriptions: list[SubscriptionResponse]

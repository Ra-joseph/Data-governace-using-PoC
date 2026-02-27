"""
API endpoints for subscription management and approval workflow.

This module provides REST API endpoints for managing dataset subscriptions,
including consumer requests, data steward approval/rejection, access credential
provisioning, and subscription lifecycle management. It integrates with the
contract service to update contracts with subscription SLA requirements.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List
from datetime import datetime, timedelta

from app.database import get_db
from app.models.subscription import Subscription
from app.models.dataset import Dataset
from app.models.contract import Contract
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionApproval,
    SubscriptionResponse,
    SubscriptionStatus,
)
from app.services.contract_service import ContractService

router = APIRouter(prefix="/api/v1/subscriptions", tags=["subscriptions"])


@router.post("/", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
def create_subscription(
    subscription_data: SubscriptionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new subscription request for dataset access.

    Data consumers submit subscription requests that enter a pending state
    awaiting approval from data stewards. Requests include business justification,
    use case, SLA requirements, and quality expectations.

    Args:
        subscription_data: SubscriptionCreate request containing:
            - dataset_id: ID of dataset to subscribe to
            - consumer_name: Name of requesting consumer
            - consumer_email: Contact email
            - consumer_team: Optional team or department
            - purpose: Business justification for data access
            - use_case: Type of use (analytics, ml, reporting, etc.)
            - sla_freshness: Optional freshness SLA (e.g. "24h")
            - sla_availability: Optional availability SLA (e.g. "99.9%")
            - sla_query_performance: Optional query performance SLA
            - data_filters: Optional dict with required_fields, access_duration_days
        db: Database session (injected dependency).

    Returns:
        Created subscription in pending status.

    Raises:
        HTTPException 404: If dataset not found.

    Example:
        POST /api/v1/subscriptions/
        {
          "dataset_id": 1,
          "consumer_name": "Jane Smith",
          "consumer_email": "jane@example.com",
          "purpose": "Q1 analytics reporting",
          "use_case": "analytics"
        }
    """
    # Verify dataset exists
    dataset = db.query(Dataset).filter(Dataset.id == subscription_data.dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID {subscription_data.dataset_id} not found"
        )

    # Create subscription
    subscription = Subscription(
        dataset_id=subscription_data.dataset_id,
        consumer_name=subscription_data.consumer_name,
        consumer_email=subscription_data.consumer_email,
        consumer_team=subscription_data.consumer_team or "",
        purpose=subscription_data.purpose,
        use_case=subscription_data.use_case.value,
        status="pending",
        access_granted=False,
    )

    # Build SLA requirements dict from individual SLA fields
    sla_requirements = {}
    if subscription_data.sla_freshness:
        sla_requirements["freshness"] = subscription_data.sla_freshness.value
    if subscription_data.sla_availability:
        sla_requirements["availability"] = subscription_data.sla_availability.value
    if subscription_data.sla_query_performance:
        sla_requirements["query_performance"] = subscription_data.sla_query_performance.value

    # Store SLA requirements and access duration in data_filters
    extra_filters = subscription_data.data_filters or {}
    subscription.data_filters = {
        "sla_requirements": sla_requirements,
        "required_fields": extra_filters.get("required_fields", []),
        "access_duration_days": extra_filters.get("access_duration_days", 365),
    }

    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    return subscription


@router.get("/", response_model=List[SubscriptionResponse])
def list_subscriptions(
    status: Optional[str] = Query(None),
    dataset_id: Optional[int] = Query(None),
    consumer_email: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    List subscriptions with optional filtering.

    Retrieves subscriptions with enhanced dataset information, supporting
    filtering by status, dataset, or consumer.

    Args:
        status: Filter by subscription status (pending, approved, rejected, etc.).
        dataset_id: Filter by specific dataset ID.
        consumer_email: Filter by consumer email address.
        db: Database session (injected dependency).

    Returns:
        List of subscriptions ordered by creation date (newest first).

    Example:
        GET /api/v1/subscriptions/?status=pending
        GET /api/v1/subscriptions/?dataset_id=1&status=approved
    """
    query = db.query(Subscription)

    if status:
        query = query.filter(Subscription.status == status)
    if dataset_id:
        query = query.filter(Subscription.dataset_id == dataset_id)
    if consumer_email:
        query = query.filter(Subscription.consumer_email == consumer_email)

    subscriptions = query.order_by(Subscription.created_at.desc()).all()

    # Enhance with dataset info
    for sub in subscriptions:
        if sub.dataset:
            # Add dataset name to response
            sub.dataset_name = sub.dataset.name

    return subscriptions


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
def get_subscription(subscription_id: int, db: Session = Depends(get_db)):
    """
    Get a specific subscription by ID.

    Retrieves complete subscription details including SLA requirements,
    approval status, and access credentials (if approved).

    Args:
        subscription_id: Unique identifier of the subscription.
        db: Database session (injected dependency).

    Returns:
        Subscription details.

    Raises:
        HTTPException 404: If subscription not found.

    Example:
        GET /api/v1/subscriptions/42
    """
    subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription with ID {subscription_id} not found"
        )

    return subscription


@router.post("/{subscription_id}/approve", response_model=SubscriptionResponse)
def approve_subscription(
    subscription_id: int,
    approval_data: SubscriptionApproval,
    db: Session = Depends(get_db)
):
    """
    Approve or reject a subscription request (data steward action).

    Data stewards review and approve/reject subscription requests. On approval,
    the system grants access, provisions credentials, sets expiration dates, and
    updates the data contract with subscription SLA requirements.

    Workflow on approval:
    1. Updates subscription status to "approved"
    2. Grants access and sets credentials
    3. Sets expiration based on access duration
    4. Creates new contract version with subscription SLA
    5. Links subscription to contract

    Workflow on rejection:
    1. Updates subscription status to "rejected"
    2. Records rejection reason

    Args:
        subscription_id: Unique identifier of the subscription to approve/reject.
        approval_data: SubscriptionApproval containing:
            - approved: True to approve, False to reject
            - access_endpoint: Connection endpoint (required if approved)
            - access_credentials: Credentials string (required if approved)
            - rejection_reason: Rejection reason (required if not approved)
        db: Database session (injected dependency).

    Returns:
        Updated subscription with approval status and credentials.

    Raises:
        HTTPException 404: If subscription not found.
        HTTPException 400: If subscription not in pending status.

    Example:
        POST /api/v1/subscriptions/42/approve
        {
          "approved": true,
          "access_endpoint": "postgresql://analytics-db:5432/dw",
          "access_credentials": "username: jane_analytics, api_key: abc123"
        }
    """
    subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription with ID {subscription_id} not found"
        )

    if subscription.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Subscription is not pending approval (current status: {subscription.status})"
        )

    # Update subscription based on decision
    if approval_data.approved:
        subscription.status = "approved"
        subscription.access_granted = True
        subscription.approved_at = datetime.utcnow()

        # Set access credentials and endpoint
        if approval_data.access_credentials:
            subscription.access_credentials = approval_data.access_credentials
        if approval_data.access_endpoint:
            subscription.access_endpoint = approval_data.access_endpoint

        # Set expiration date from previously stored access_duration_days
        if subscription.data_filters and subscription.data_filters.get("access_duration_days"):
            days = subscription.data_filters["access_duration_days"]
            subscription.expires_at = datetime.utcnow() + timedelta(days=days)

        # Generate new contract version with subscription
        try:
            dataset = subscription.dataset
            if dataset and dataset.contracts:
                # Get latest contract
                latest_contract = sorted(dataset.contracts, key=lambda c: c.created_at, reverse=True)[0]

                # Create new contract version with subscription SLA
                contract_service = ContractService(db)

                # Add SLA requirements to contract
                sla_data = subscription.data_filters.get("sla_requirements", {}) if subscription.data_filters else {}
                updated_contract = contract_service.add_subscription_to_contract(
                    latest_contract.id,
                    subscription.id,
                    {
                        "consumer": subscription.consumer_name,
                        "sla_requirements": sla_data,
                    }
                )

                # Link subscription to new contract
                subscription.contract_id = updated_contract.id

        except Exception as e:
            # Log error but don't fail the approval
            print(f"Warning: Failed to update contract: {str(e)}")

    else:
        subscription.status = "rejected"
        subscription.rejection_reason = approval_data.rejection_reason or ""

    subscription.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(subscription)

    return subscription


@router.put("/{subscription_id}", response_model=SubscriptionResponse)
def update_subscription(
    subscription_id: int,
    update_data: SubscriptionUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a subscription request (before approval).

    Allows consumers to modify pending subscription requests before steward
    review. Only pending subscriptions can be updated.

    Args:
        subscription_id: Unique identifier of the subscription to update.
        update_data: SubscriptionUpdate with optional fields to modify
                     (purpose, use_case, sla_freshness, sla_availability,
                      sla_query_performance, quality_completeness, data_filters).
        db: Database session (injected dependency).

    Returns:
        Updated subscription.

    Raises:
        HTTPException 404: If subscription not found.
        HTTPException 400: If subscription is not in pending status.

    Example:
        PUT /api/v1/subscriptions/42
        {
          "purpose": "Updated business justification",
          "sla_freshness": "6h"
        }
    """
    subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription with ID {subscription_id} not found"
        )

    if subscription.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only update pending subscriptions"
        )

    # Update only the fields explicitly provided in the request
    for field, value in update_data.model_dump(exclude_unset=True).items():
        if hasattr(subscription, field) and value is not None:
            setattr(subscription, field, value)

    subscription.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(subscription)

    return subscription


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_subscription(subscription_id: int, db: Session = Depends(get_db)):
    """
    Cancel a subscription and revoke access.

    Sets subscription status to cancelled and revokes data access. This can
    be called by consumers to cancel their own subscriptions or by stewards
    to revoke access.

    Args:
        subscription_id: Unique identifier of the subscription to cancel.
        db: Database session (injected dependency).

    Returns:
        None (HTTP 204 No Content).

    Raises:
        HTTPException 404: If subscription not found.

    Example:
        DELETE /api/v1/subscriptions/42
    """
    subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription with ID {subscription_id} not found"
        )

    subscription.status = "cancelled"
    subscription.access_granted = False
    subscription.updated_at = datetime.utcnow()

    db.commit()

    return None

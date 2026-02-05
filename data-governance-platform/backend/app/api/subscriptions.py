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
    SubscriptionResponse,
    SubscriptionStatus,
)
from app.services.contract_service import ContractService

router = APIRouter(prefix="/api/v1/subscriptions", tags=["subscriptions"])


@router.post("/", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
def create_subscription(
    subscription_data: dict,
    db: Session = Depends(get_db)
):
    """
    Create a new subscription request.

    Data consumers submit subscription requests which are pending approval by data stewards.
    """
    # Verify dataset exists
    dataset = db.query(Dataset).filter(Dataset.id == subscription_data.get("dataset_id")).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID {subscription_data.get('dataset_id')} not found"
        )

    # Create subscription
    subscription = Subscription(
        dataset_id=subscription_data.get("dataset_id"),
        consumer_name=subscription_data.get("consumer_name"),
        consumer_email=subscription_data.get("consumer_email"),
        consumer_team=subscription_data.get("consumer_organization", ""),
        purpose=subscription_data.get("business_justification", ""),
        use_case=subscription_data.get("use_case", "analytics"),
        status="pending",
        access_granted=False,
    )

    # Store SLA requirements as JSON in data_filters for now
    if subscription_data.get("sla_requirements"):
        subscription.data_filters = {
            "sla_requirements": subscription_data.get("sla_requirements"),
            "required_fields": subscription_data.get("required_fields", []),
            "access_duration_days": subscription_data.get("access_duration_days", 365),
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
    approval_data: dict,
    db: Session = Depends(get_db)
):
    """
    Approve or reject a subscription request.

    When approved:
    1. Updates subscription status
    2. Grants access credentials
    3. Generates new version of data contract with subscription details
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
    if approval_data.get("status") == "approved":
        subscription.status = "approved"
        subscription.access_granted = True
        subscription.approved_at = datetime.utcnow()

        # Set access credentials
        if approval_data.get("access_credentials"):
            creds = approval_data["access_credentials"]
            subscription.access_credentials = f"username: {creds.get('username')}, api_key: {creds.get('api_key')}"
            subscription.access_endpoint = creds.get("connection_string", "")

        # Update data filters with approved fields
        if subscription.data_filters:
            subscription.data_filters["approved_fields"] = approval_data.get("approved_fields", [])
        else:
            subscription.data_filters = {"approved_fields": approval_data.get("approved_fields", [])}

        # Set expiration date
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
                sla_data = subscription.data_filters.get("sla_requirements", {})
                updated_contract = contract_service.add_subscription_to_contract(
                    latest_contract.id,
                    subscription.id,
                    {
                        "consumer": subscription.consumer_name,
                        "sla_requirements": sla_data,
                        "approved_fields": approval_data.get("approved_fields", []),
                    }
                )

                # Link subscription to new contract
                subscription.contract_id = updated_contract.id

        except Exception as e:
            # Log error but don't fail the approval
            print(f"Warning: Failed to update contract: {str(e)}")

    else:
        subscription.status = "rejected"
        subscription.rejection_reason = approval_data.get("reviewer_notes", "")

    subscription.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(subscription)

    return subscription


@router.put("/{subscription_id}", response_model=SubscriptionResponse)
def update_subscription(
    subscription_id: int,
    update_data: dict,
    db: Session = Depends(get_db)
):
    """
    Update a subscription (before approval).
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

    # Update fields
    for field, value in update_data.items():
        if hasattr(subscription, field) and value is not None:
            setattr(subscription, field, value)

    subscription.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(subscription)

    return subscription


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_subscription(subscription_id: int, db: Session = Depends(get_db)):
    """
    Cancel a subscription.
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

"""
Subscription and Payment schemas
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from decimal import Decimal
import uuid


class SubscriptionPlanInfo(BaseModel):
    """Subscription plan information"""
    id: str
    name: str
    price: int  # KRW
    description: str
    features: list[str]


class SubscriptionResponse(BaseModel):
    """User subscription response"""
    id: uuid.UUID
    user_id: uuid.UUID
    plan: str
    status: str
    started_at: datetime
    expires_at: Optional[datetime]
    auto_renew: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentInitRequest(BaseModel):
    """Payment initiation request"""
    plan_id: str = Field(..., description="Subscription plan ID (e.g., 'premium')")
    return_url: str = Field(..., description="Return URL after payment")


class PaymentInitResponse(BaseModel):
    """Payment initiation response"""
    merchant_uid: str
    amount: int
    plan_name: str


class PaymentCompleteRequest(BaseModel):
    """Payment completion request (from frontend after Portone redirect)"""
    merchant_uid: str
    imp_uid: str


class PaymentCompleteResponse(BaseModel):
    """Payment completion response"""
    success: bool
    message: str
    subscription: Optional[SubscriptionResponse]


class PaymentWebhookRequest(BaseModel):
    """Portone webhook request"""
    imp_uid: str
    merchant_uid: str
    status: str


class PaymentResponse(BaseModel):
    """Payment transaction response"""
    id: uuid.UUID
    subscription_id: uuid.UUID
    user_id: uuid.UUID
    amount: Decimal
    currency: str
    status: str
    merchant_uid: str
    imp_uid: Optional[str]
    pay_method: Optional[str]
    card_name: Optional[str]
    paid_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class SubscriptionCancelRequest(BaseModel):
    """Subscription cancellation request"""
    reason: Optional[str] = None

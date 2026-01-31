"""
Subscription and Payment API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.subscription import (
    SubscriptionPlanInfo,
    SubscriptionResponse,
    PaymentInitRequest,
    PaymentInitResponse,
    PaymentCompleteRequest,
    PaymentCompleteResponse,
    PaymentWebhookRequest,
    SubscriptionCancelRequest,
)
from app.schemas.auth import UserResponse
from app.api.v1.deps import get_current_active_user
from app.services.payment_service import PaymentService
from app.core.exceptions import NotFoundError


router = APIRouter()


@router.get("/plans", response_model=list[SubscriptionPlanInfo])
async def get_subscription_plans(
    db: AsyncSession = Depends(get_db),
):
    """
    Get available subscription plans
    
    Public endpoint - no authentication required
    """
    payment_service = PaymentService(db)
    plans = payment_service.get_subscription_plans()
    return plans


@router.get("/me", response_model=SubscriptionResponse)
async def get_my_subscription(
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current user's subscription
    
    Requires: Authentication
    """
    payment_service = PaymentService(db)
    subscription = await payment_service.get_user_subscription(str(current_user.id))
    
    if not subscription:
        # Create free subscription if none exists
        subscription = await payment_service.create_free_subscription(str(current_user.id))
    
    return subscription


@router.post("/payment/init", response_model=PaymentInitResponse)
async def init_payment(
    request: PaymentInitRequest,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Initialize payment process
    
    Creates a pending payment record and returns merchant_uid
    for Portone integration.
    
    Requires: Authentication
    """
    try:
        payment_service = PaymentService(db)
        merchant_uid, amount, plan_name = await payment_service.initiate_payment(
            user_id=str(current_user.id),
            plan_id=request.plan_id,
        )
        
        return PaymentInitResponse(
            merchant_uid=merchant_uid,
            amount=amount,
            plan_name=plan_name,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize payment"
        )


@router.post("/payment/complete", response_model=PaymentCompleteResponse)
async def complete_payment(
    request: PaymentCompleteRequest,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Complete payment after Portone redirect
    
    Verifies payment with Portone and upgrades subscription.
    
    Requires: Authentication
    """
    try:
        payment_service = PaymentService(db)
        subscription = await payment_service.complete_payment(
            merchant_uid=request.merchant_uid,
            imp_uid=request.imp_uid,
        )
        
        return PaymentCompleteResponse(
            success=True,
            message="결제가 완료되었습니다.",
            subscription=SubscriptionResponse.model_validate(subscription),
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        return PaymentCompleteResponse(
            success=False,
            message=f"결제 검증 실패: {str(e)}",
            subscription=None,
        )


@router.post("/payment/webhook")
async def payment_webhook(
    request: PaymentWebhookRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Portone webhook endpoint
    
    Receives payment status updates from Portone.
    No authentication required (verified by Portone signature in production).
    """
    try:
        payment_service = PaymentService(db)
        
        # For now, we just verify the payment
        # In production, add signature verification
        portone_data = payment_service.portone.verify_payment(request.imp_uid)
        
        return {
            "success": True,
            "message": "Webhook processed",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/cancel", response_model=SubscriptionResponse)
async def cancel_subscription(
    request: SubscriptionCancelRequest,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel subscription
    
    User can cancel their subscription. The subscription will remain
    active until the expiration date.
    
    Requires: Authentication
    """
    try:
        payment_service = PaymentService(db)
        subscription = await payment_service.cancel_subscription(
            user_id=str(current_user.id),
            reason=request.reason,
        )
        return subscription
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription"
        )

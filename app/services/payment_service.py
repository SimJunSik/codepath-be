"""
Payment service using Portone (PortOne, formerly iamport)
"""
import uuid
import requests
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from decimal import Decimal

from app.models.subscription import (
    Subscription,
    SubscriptionStatus,
    SubscriptionPlan,
    Payment,
    PaymentStatus,
)
from app.core.config import settings
from app.core.exceptions import NotFoundError


class PortoneService:
    """Portone API integration service"""

    BASE_URL = "https://api.iamport.kr"

    def __init__(self):
        self.api_key = settings.PORTONE_API_KEY
        self.api_secret = settings.PORTONE_API_SECRET
        self.store_id = settings.PORTONE_STORE_ID
        self._access_token: Optional[str] = None

    def _get_access_token(self) -> str:
        """Get Portone access token"""
        if self._access_token:
            return self._access_token

        url = f"{self.BASE_URL}/users/getToken"
        response = requests.post(
            url,
            json={
                "imp_key": self.api_key,
                "imp_secret": self.api_secret,
            },
        )
        data = response.json()

        if data.get("code") != 0:
            raise Exception(f"Failed to get Portone token: {data.get('message')}")

        self._access_token = data["response"]["access_token"]
        return self._access_token

    def verify_payment(self, imp_uid: str) -> dict:
        """Verify payment with Portone"""
        token = self._get_access_token()
        url = f"{self.BASE_URL}/payments/{imp_uid}"

        response = requests.get(
            url,
            headers={"Authorization": token},
        )
        data = response.json()

        if data.get("code") != 0:
            raise Exception(f"Failed to verify payment: {data.get('message')}")

        return data["response"]


class PaymentService:
    """Payment and subscription management service"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.portone = PortoneService()

    def get_subscription_plans(self) -> list[dict]:
        """Get available subscription plans"""
        return [
            {
                "id": "free",
                "name": "무료",
                "price": 0,
                "description": "기본 문제 접근",
                "features": [
                    "입문/쉬움 난이도 문제",
                    "기본 채점 기능",
                ],
            },
            {
                "id": "premium",
                "name": settings.PREMIUM_PLAN_NAME,
                "price": settings.PREMIUM_PLAN_PRICE,
                "description": settings.PREMIUM_PLAN_DESCRIPTION,
                "features": [
                    "모든 난이도 문제 접근",
                    "AI 상세 해설 및 피드백",
                    "무제한 제출",
                    "학습 진도 분석",
                ],
            },
        ]

    async def get_user_subscription(self, user_id: str) -> Optional[Subscription]:
        """Get user's active subscription"""
        result = await self.db.execute(
            select(Subscription)
            .where(Subscription.user_id == user_id)
            .where(Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]))
            .order_by(Subscription.created_at.desc())
        )
        return result.scalar_one_or_none()

    async def create_free_subscription(self, user_id: str) -> Subscription:
        """Create free subscription for new user"""
        subscription = Subscription(
            user_id=user_id,
            plan=SubscriptionPlan.FREE,
            status=SubscriptionStatus.ACTIVE,
            started_at=datetime.utcnow(),
            expires_at=None,  # No expiration for free plan
            auto_renew=False,
        )
        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)
        return subscription

    async def initiate_payment(
        self, user_id: str, plan_id: str
    ) -> tuple[str, int, str]:
        """
        Initiate payment process
        Returns: (merchant_uid, amount, plan_name)
        """
        plans = {p["id"]: p for p in self.get_subscription_plans()}
        if plan_id not in plans:
            raise ValueError(f"Invalid plan: {plan_id}")

        plan = plans[plan_id]
        if plan["price"] == 0:
            raise ValueError("Cannot pay for free plan")

        # Generate unique merchant UID
        merchant_uid = f"ORDER_{user_id[:8]}_{int(datetime.utcnow().timestamp())}"

        # Create pending payment record
        subscription = await self.get_user_subscription(user_id)
        if not subscription:
            subscription = await self.create_free_subscription(user_id)

        payment = Payment(
            subscription_id=subscription.id,
            user_id=user_id,
            amount=Decimal(str(plan["price"])),
            currency="KRW",
            status=PaymentStatus.PENDING,
            merchant_uid=merchant_uid,
        )
        self.db.add(payment)
        await self.db.commit()

        return merchant_uid, plan["price"], plan["name"]

    async def complete_payment(
        self, merchant_uid: str, imp_uid: str
    ) -> Subscription:
        """
        Complete payment after Portone verification
        """
        # Get payment record
        result = await self.db.execute(
            select(Payment).where(Payment.merchant_uid == merchant_uid)
        )
        payment = result.scalar_one_or_none()
        if not payment:
            raise NotFoundError("Payment not found")

        # Verify with Portone
        try:
            portone_data = self.portone.verify_payment(imp_uid)
        except Exception as e:
            payment.status = PaymentStatus.FAILED
            payment.failed_at = datetime.utcnow()
            payment.fail_reason = str(e)
            await self.db.commit()
            raise

        # Check payment status
        if portone_data["status"] != "paid":
            payment.status = PaymentStatus.FAILED
            payment.failed_at = datetime.utcnow()
            payment.fail_reason = f"Payment not completed: {portone_data['status']}"
            await self.db.commit()
            raise Exception("Payment verification failed")

        # Check amount matches
        if int(portone_data["amount"]) != int(payment.amount):
            payment.status = PaymentStatus.FAILED
            payment.failed_at = datetime.utcnow()
            payment.fail_reason = "Amount mismatch"
            await self.db.commit()
            raise Exception("Payment amount mismatch")

        # Update payment
        payment.status = PaymentStatus.PAID
        payment.imp_uid = imp_uid
        payment.pg_tid = portone_data.get("pg_tid")
        payment.pg_provider = portone_data.get("pg_provider")
        payment.pay_method = portone_data.get("pay_method")
        payment.card_name = portone_data.get("card_name")
        payment.card_number = portone_data.get("card_number")
        payment.paid_at = datetime.utcnow()

        # Upgrade subscription to premium
        subscription = await self.db.get(Subscription, payment.subscription_id)
        subscription.plan = SubscriptionPlan.PREMIUM
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.started_at = datetime.utcnow()
        subscription.expires_at = datetime.utcnow() + timedelta(days=30)  # 1 month
        subscription.auto_renew = False  # Manual renewal for now

        await self.db.commit()
        await self.db.refresh(subscription)

        return subscription

    async def cancel_subscription(
        self, user_id: str, reason: Optional[str] = None
    ) -> Subscription:
        """Cancel user subscription"""
        subscription = await self.get_user_subscription(user_id)
        if not subscription:
            raise NotFoundError("No active subscription found")

        if subscription.plan == SubscriptionPlan.FREE:
            raise ValueError("Cannot cancel free subscription")

        subscription.status = SubscriptionStatus.CANCELED
        subscription.canceled_at = datetime.utcnow()
        subscription.auto_renew = False

        await self.db.commit()
        await self.db.refresh(subscription)

        return subscription

"""
Subscription and Payment models
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Enum as SQLEnum, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum

from app.core.database import Base


class SubscriptionStatus(str, enum.Enum):
    """Subscription status enum"""
    ACTIVE = "active"           # 활성 구독
    CANCELED = "canceled"       # 취소됨 (기간 만료 전까지는 사용 가능)
    EXPIRED = "expired"         # 만료됨
    TRIAL = "trial"            # 무료 체험 중


class PaymentStatus(str, enum.Enum):
    """Payment status enum"""
    PENDING = "pending"         # 결제 대기
    PAID = "paid"              # 결제 완료
    FAILED = "failed"          # 결제 실패
    CANCELED = "canceled"      # 결제 취소
    REFUNDED = "refunded"      # 환불


class SubscriptionPlan(str, enum.Enum):
    """Subscription plan types"""
    FREE = "free"
    PREMIUM = "premium"


class Subscription(Base):
    """User subscription model"""
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    plan = Column(SQLEnum(SubscriptionPlan), nullable=False, default=SubscriptionPlan.FREE)
    status = Column(SQLEnum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.ACTIVE)
    
    # 구독 기간
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # None = 무제한 (Free plan)
    canceled_at = Column(DateTime, nullable=True)  # 구독 취소 시점
    
    # 자동 갱신
    auto_renew = Column(Boolean, default=True)
    
    # Portone 관련
    billing_key = Column(String(255), nullable=True)  # 정기결제용 빌링키
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")
    payments = relationship("Payment", back_populates="subscription", cascade="all, delete-orphan")


class Payment(Base):
    """Payment transaction model"""
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 결제 정보
    amount = Column(Numeric(10, 2), nullable=False)  # 결제 금액
    currency = Column(String(3), nullable=False, default="KRW")
    status = Column(SQLEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    
    # Portone 관련
    merchant_uid = Column(String(255), nullable=False, unique=True, index=True)  # 주문번호 (우리측)
    imp_uid = Column(String(255), nullable=True, unique=True, index=True)  # 아임포트 거래 고유번호
    pg_tid = Column(String(255), nullable=True)  # PG사 거래번호
    pg_provider = Column(String(50), nullable=True)  # PG사 (nice, kcp 등)
    pay_method = Column(String(50), nullable=True)  # 결제수단 (card, trans, vbank 등)
    
    # 카드 정보 (선택적)
    card_name = Column(String(100), nullable=True)
    card_number = Column(String(20), nullable=True)  # 마스킹된 카드번호
    
    # 결제 시점
    paid_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    canceled_at = Column(DateTime, nullable=True)
    refunded_at = Column(DateTime, nullable=True)
    
    # 실패/취소 사유
    fail_reason = Column(String(500), nullable=True)
    cancel_reason = Column(String(500), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subscription = relationship("Subscription", back_populates="payments")
    user = relationship("User", back_populates="payments")

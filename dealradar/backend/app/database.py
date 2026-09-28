from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(128), unique=True, index=True, nullable=False)
    fcm_token = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    total_saved_cop = Column(Float, default=0.0)

    alerts = relationship("ProductAlert", back_populates="user", cascade="all, delete-orphan")

class ProductAlert(Base):
    __tablename__ = "product_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_title = Column(String(255), nullable=False)
    query_keyword = Column(String(255), nullable=False)
    category = Column(String(64), default="general")
    target_price_cop = Column(Float, nullable=False)
    current_best_price_cop = Column(Float, nullable=True)
    best_store = Column(String(64), nullable=True)
    product_url = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    last_notified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="alerts")
    price_history = relationship("PriceHistory", back_populates="alert", cascade="all, delete-orphan")

class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("product_alerts.id"), nullable=False)
    store = Column(String(64), nullable=False)
    price_cop = Column(Float, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow)

    alert = relationship("ProductAlert", back_populates="price_history")

class FeaturedDeal(Base):
    __tablename__ = "featured_deals"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    store = Column(String(64), nullable=False)
    category = Column(String(64), default="general")
    current_price_cop = Column(Float, nullable=False)
    original_price_cop = Column(Float, nullable=False)
    discount_percentage = Column(Integer, nullable=False)
    product_url = Column(Text, nullable=False)
    image_url = Column(Text, nullable=True)
    badge = Column(String(32), default="OFERTA DESTACADA")
    updated_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

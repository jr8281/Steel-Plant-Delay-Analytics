from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Shop(Base):
    __tablename__ = "shops"
    id = Column(Integer, primary_key=True)
    shop_code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(80), unique=True, nullable=False)
    delay_events = relationship("DelayEvent", back_populates="shop")


class Equipment(Base):
    __tablename__ = "equipment"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    delay_events = relationship("DelayEvent", back_populates="equipment")


class Agency(Base):
    __tablename__ = "agencies"
    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, nullable=False)
    description = Column(String(200), nullable=True)
    delay_events = relationship("DelayEvent", back_populates="agency")


class DelayEvent(Base):
    __tablename__ = "delay_events"
    id = Column(Integer, primary_key=True)
    delay_date = Column(Date, nullable=False, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=True, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=False, index=True)
    sub_eqpt = Column(String(100), nullable=True)
    from_time = Column(Float, nullable=True)
    upto_time = Column(Float, nullable=True)
    durn = Column(Float, nullable=False)
    eff_durn = Column(Float, nullable=False)
    cum_delay = Column(Float, nullable=False, default=0)
    freq = Column(Integer, nullable=False, default=1)
    descr = Column(String(500), nullable=True)
    material = Column(String(100), nullable=True)
    delay_code = Column(String(30), nullable=True)
    contd = Column(String(5), nullable=True)
    close_dt = Column(Date, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    shop = relationship("Shop", back_populates="delay_events")
    equipment = relationship("Equipment", back_populates="delay_events")
    agency = relationship("Agency", back_populates="delay_events")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="operator")
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True)

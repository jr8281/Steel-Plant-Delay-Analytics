from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)


class DelayEventUpdate(BaseModel):
    delay_date: Optional[date] = None
    shop_code: Optional[str] = Field(default=None, max_length=10)
    equipment_name: Optional[str] = Field(default=None, max_length=100)
    agency_code: Optional[str] = Field(default=None, max_length=10)
    sub_eqpt: Optional[str] = None
    from_time: Optional[float] = None
    upto_time: Optional[float] = None
    durn: Optional[float] = Field(default=None, ge=0)
    eff_durn: Optional[float] = Field(default=None, ge=0)
    cum_delay: Optional[float] = Field(default=None, ge=0)
    freq: Optional[int] = Field(default=None, ge=0)
    descr: Optional[str] = None
    material: Optional[str] = None
    delay_code: Optional[str] = None
    contd: Optional[str] = None
    close_dt: Optional[date] = None


class AssistantQuestion(BaseModel):
    question: str = Field(min_length=2, max_length=1000)


class ChatRequest(BaseModel):
    conversation_id: str
    message: str = Field(min_length=1, max_length=2000)
    filters: Optional[dict] = None

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class GymBase(BaseModel):
    name: str
    email: EmailStr
    address: Optional[str] = None
    description: Optional[str] = None
    gym_type: Optional[str] = Field(default=None, max_length=50)
    monthly_fee_cents: int
    currency: str


class GymCreate(GymBase):
    password: str = Field(min_length=8, max_length=72)


class GymUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    gym_type: Optional[str] = Field(default=None, max_length=50)
    monthly_fee_cents: Optional[int] = None
    currency: Optional[str] = None


class GymOut(GymBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CustomerBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    active: Optional[bool] = True
    date_of_birth: Optional[date] = None
    membership_start: Optional[date] = None
    membership_end: Optional[date] = None
    notes: Optional[str] = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    active: Optional[bool] = None
    date_of_birth: Optional[date] = None
    membership_start: Optional[date] = None
    membership_end: Optional[date] = None
    notes: Optional[str] = None


class CustomerOut(CustomerBase):
    id: int
    gym_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

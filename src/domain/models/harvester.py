from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import date, datetime
import uuid

class HarvesterBase(BaseModel):
    employee_number: Optional[str] = Field(None, max_length=30)
    full_name: str = Field(..., max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=1)
    division_id: Optional[uuid.UUID] = None
    block_id: Optional[uuid.UUID] = None
    hire_date: Optional[date] = None
    is_active: bool = True

class HarvesterCreate(HarvesterBase):
    pass

class HarvesterUpdate(BaseModel):
    employee_number: Optional[str] = Field(None, max_length=30)
    full_name: Optional[str] = Field(None, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=1)
    division_id: Optional[uuid.UUID] = None
    block_id: Optional[uuid.UUID] = None
    hire_date: Optional[date] = None
    is_active: Optional[bool] = None

class HarvesterResponse(HarvesterBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    division_name: Optional[str] = None
    block_code: Optional[str] = None

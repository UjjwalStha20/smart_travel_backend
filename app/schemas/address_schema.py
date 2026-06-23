from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from sqlmodel import Field, Float, Integer


class AddressBase(BaseModel):
    province: str
    district: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    altitude: int = Field(gt=0)


class AddressCreate(AddressBase):
    pass


class AddressRead(AddressBase):
    id: UUID


class AddressUpdate(AddressBase):
    pass

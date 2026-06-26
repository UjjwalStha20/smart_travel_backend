from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field
from sqlmodel import Float, Integer


class AddressBase(BaseModel):
    province: str = Field(min_length=1)
    district: str = Field(min_length=1)
    place: str | None = None
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    altitude: int = Field(gt=0)


class AddressCreate(AddressBase):
    pass


class AddressRead(AddressBase):
    id: UUID


class AddressUpdate(BaseModel):
    province: str | None = Field(default=None, min_length=1)
    district: str | None = Field(default=None, min_length=1)
    place: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    altitude: int | None = Field(default=None, gt=0)

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CategoryBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    default_lifespan_months: int = 36
    default_depreciation_method: str = "STRAIGHT_LINE"


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    default_lifespan_months: Optional[int] = None
    default_depreciation_method: Optional[str] = None


class CategoryResponse(CategoryBase):
    id: str
    created_at: datetime
    updated_at: datetime
    asset_count: Optional[int] = 0

    class Config:
        from_attributes = True

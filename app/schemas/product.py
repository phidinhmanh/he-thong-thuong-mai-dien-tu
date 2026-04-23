from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ProductBase(BaseModel):
    name: str
    slug: Optional[str] = None
    description: Optional[str] = None
    price: float
    compare_price: Optional[float] = None
    image_url: Optional[str] = None
    stock: int = 0
    category_id: Optional[int] = None
    brand: Optional[str] = None
    featured: bool = False

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    compare_price: Optional[float] = None
    image_url: Optional[str] = None
    stock: Optional[int] = None
    category_id: Optional[int] = None
    brand: Optional[str] = None
    featured: Optional[bool] = None

class ProductResponse(ProductBase):
    id: int
    is_active: int
    created_at: datetime

    class Config:
        from_attributes = True

class ProductListResponse(BaseModel):
    items: List[ProductResponse]
    total: int
    page: int
    page_size: int
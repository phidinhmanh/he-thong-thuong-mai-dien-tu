from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class CartItemBase(BaseModel):
    product_id: int
    quantity: int = 1

class CartItemCreate(CartItemBase):
    pass

class CartItemUpdate(BaseModel):
    quantity: int

class CartItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    product_name: str
    product_price: float
    product_image: Optional[str] = None
    subtotal: float

    class Config:
        from_attributes = True

class CartResponse(BaseModel):
    id: int
    items: List[CartItemResponse]
    total_items: int
    total_price: float

    class Config:
        from_attributes = True
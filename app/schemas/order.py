from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class OrderItemBase(BaseModel):
    product_id: int
    quantity: int

class OrderItemCreate(OrderItemBase):
    price: float
    product_name: str

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    price: float
    product_name: str

    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    shipping_address: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None

class OrderUpdate(BaseModel):
    status: str

class OrderResponse(BaseModel):
    id: int
    user_id: int
    status: str
    total: float
    shipping_address: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    items: List[OrderItemResponse] = []
    checkout_url: Optional[str] = None

    class Config:
        from_attributes = True

class OrderListResponse(BaseModel):
    items: List[OrderResponse]
    total: int
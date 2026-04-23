from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class FlashSaleItemBase(BaseModel):
    product_id: int
    sale_price: float
    stock_limit: int

class FlashSaleItemResponse(FlashSaleItemBase):
    id: int
    sold_count: int

    class Config:
        from_attributes = True

class FlashSaleBase(BaseModel):
    name: str
    start_time: datetime
    end_time: datetime
    is_active: bool = True

class FlashSaleCreate(FlashSaleBase):
    items: List[FlashSaleItemBase]

class FlashSaleResponse(FlashSaleBase):
    id: int
    items: List[FlashSaleItemResponse]

    class Config:
        from_attributes = True

class VoucherBase(BaseModel):
    code: str
    discount_type: str
    discount_value: float
    min_order_value: float = 0
    expiry_date: Optional[datetime] = None
    usage_limit: Optional[int] = None
    is_active: bool = True

class VoucherCreate(VoucherBase):
    pass

class VoucherResponse(VoucherBase):
    id: int
    used_count: int

    class Config:
        from_attributes = True

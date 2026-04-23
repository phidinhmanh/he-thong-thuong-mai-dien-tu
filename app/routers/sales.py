from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from typing import List
from app.core.database import get_db
from app.models.models import FlashSale, FlashSaleItem, Voucher, Product
from app.schemas.sales import FlashSaleCreate, FlashSaleResponse, VoucherCreate, VoucherResponse
from app.routers.auth import get_current_admin

router = APIRouter()

@router.get("/flash-sales", response_model=List[FlashSaleResponse])
async def list_flash_sales(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(FlashSale)
        .where(FlashSale.is_active == True)
        .options(selectinload(FlashSale.items))
    )
    return result.scalars().all()

@router.post("/flash-sales", response_model=FlashSaleResponse)
async def create_flash_sale(
    sale: FlashSaleCreate,
    db: AsyncSession = Depends(get_db),
    admin: bool = Depends(get_current_admin)
):
    db_sale = FlashSale(
        name=sale.name,
        start_time=sale.start_time,
        end_time=sale.end_time,
        is_active=sale.is_active
    )
    db.add(db_sale)
    await db.flush()

    for item in sale.items:
        db_item = FlashSaleItem(
            flash_sale_id=db_sale.id,
            product_id=item.product_id,
            sale_price=item.sale_price,
            stock_limit=item.stock_limit
        )
        db.add(db_item)

    await db.commit()
    await db.refresh(db_sale)
    return db_sale

@router.get("/vouchers", response_model=List[VoucherResponse])
async def list_vouchers(
    db: AsyncSession = Depends(get_db),
    admin: bool = Depends(get_current_admin)
):
    result = await db.execute(select(Voucher))
    return result.scalars().all()

@router.post("/vouchers", response_model=VoucherResponse)
async def create_voucher(
    voucher: VoucherCreate,
    db: AsyncSession = Depends(get_db),
    admin: bool = Depends(get_current_admin)
):
    db_voucher = Voucher(**voucher.model_dump())
    db.add(db_voucher)
    await db.commit()
    await db.refresh(db_voucher)
    return db_voucher

@router.get("/vouchers/validate/{code}")
async def validate_voucher(
    code: str,
    total_amount: float,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Voucher).where(
        and_(
            Voucher.code == code,
            Voucher.is_active == True,
            (Voucher.expiry_date == None) | (Voucher.expiry_date > func.now())
        )
    ))
    voucher = result.scalar_one_or_none()

    if not voucher:
        raise HTTPException(status_code=404, detail="Voucher not found or expired")

    if total_amount < voucher.min_order_value:
        raise HTTPException(
            status_code=400,
            detail=f"Order total must be at least {voucher.min_order_value} to use this voucher"
        )

    if voucher.usage_limit and voucher.used_count >= voucher.usage_limit:
        raise HTTPException(status_code=400, detail="Voucher usage limit reached")

    return voucher

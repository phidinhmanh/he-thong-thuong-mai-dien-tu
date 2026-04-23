from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from app.core.database import get_db
from app.models.models import Order, OrderItem, Cart, CartItem, Product, User
from app.schemas.order import OrderCreate, OrderResponse, OrderListResponse
from app.routers.auth import get_current_user

from app.routers.webhooks import create_stripe_checkout

router = APIRouter()

@router.post("/", response_model=OrderResponse)
async def create_order(
    order_data: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # ... (existing logic for cart and total calculation)
    # Get user's cart
    result = await db.execute(select(Cart).where(Cart.user_id == current_user.id))
    cart = result.scalar_one_or_none()

    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Get cart items with product details
    result = await db.execute(
        select(CartItem, Product)
        .join(Product, CartItem.product_id == Product.id)
        .where(CartItem.cart_id == cart.id)
    )
    cart_items = result.all()

    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Calculate total and validate stock
    total = 0
    order_items_data = []

    for cart_item, product in cart_items:
        if product.stock < cart_item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {product.name}"
            )
        item_total = cart_item.quantity * product.price
        total += item_total
        order_items_data.append({
            "product_id": product.id,
            "quantity": cart_item.quantity,
            "price": product.price,
            "product_name": product.name
        })

    # Create order
    order = Order(
        user_id=current_user.id,
        total=total,
        shipping_address=order_data.shipping_address,
        phone=order_data.phone,
        notes=order_data.notes
    )
    db.add(order)
    await db.flush()

    # Create order items and update stock
    for item_data in order_items_data:
        order_item = OrderItem(order_id=order.id, **item_data)
        db.add(order_item)

        # Update product stock
        result = await db.execute(select(Product).where(Product.id == item_data["product_id"]))
        product = result.scalar_one()
        product.stock -= item_data["quantity"]

    # Clear cart
    result = await db.execute(select(CartItem).where(CartItem.cart_id == cart.id))
    items_to_delete = result.scalars().all()
    for item in items_to_delete:
        await db.delete(item)

    await db.commit()

    # Fetch complete order with items
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order.id)
    )
    order = result.scalar_one()

    # Create Stripe Checkout Session
    items_summary = ", ".join([f"{item.product_name} x {item.quantity}" for item in order.items])
    checkout_url = await create_stripe_checkout(order.id, order.total, items_summary)

    # Note: response_model is OrderResponse, we might need to extend it to include checkout_url
    # or return a dict. For now, let's just return the order and handle url in frontend if needed
    # but to be useful, let's add it to the return
    return {**order.__dict__, "checkout_url": checkout_url}

@router.get("/", response_model=List[OrderResponse])
async def list_orders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
    )
    orders = result.scalars().all()
    return orders

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    return order
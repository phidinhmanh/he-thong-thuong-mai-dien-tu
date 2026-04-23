from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.models import Cart, CartItem, Product, User
from app.schemas.cart import CartItemCreate, CartItemUpdate, CartResponse, CartItemResponse
from app.routers.auth import get_current_user

router = APIRouter()

async def get_or_create_cart(user_id: int, db: AsyncSession):
    result = await db.execute(select(Cart).where(Cart.user_id == user_id))
    cart = result.scalar_one_or_none()
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        await db.commit()
        await db.refresh(cart)
    return cart

@router.get("/", response_model=CartResponse)
async def get_cart(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cart = await get_or_create_cart(current_user.id, db)

    # Get cart items with product details
    result = await db.execute(
        select(CartItem, Product)
        .join(Product, CartItem.product_id == Product.id)
        .where(CartItem.cart_id == cart.id)
    )
    items = result.all()

    cart_items = []
    total_price = 0
    total_items = 0

    for cart_item, product in items:
        subtotal = cart_item.quantity * product.price
        total_price += subtotal
        total_items += cart_item.quantity

        cart_items.append(CartItemResponse(
            id=cart_item.id,
            product_id=product.id,
            quantity=cart_item.quantity,
            product_name=product.name,
            product_price=product.price,
            product_image=product.image_url,
            subtotal=subtotal
        ))

    return CartResponse(
        id=cart.id,
        items=cart_items,
        total_items=total_items,
        total_price=total_price
    )

@router.post("/items")
async def add_to_cart(
    item: CartItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check product exists
    result = await db.execute(select(Product).where(Product.id == item.product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product.stock < item.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")

    cart = await get_or_create_cart(current_user.id, db)

    # Check if item already in cart
    result = await db.execute(
        select(CartItem)
        .where(CartItem.cart_id == cart.id, CartItem.product_id == item.product_id)
    )
    existing_item = result.scalar_one_or_none()

    if existing_item:
        existing_item.quantity += item.quantity
        if product.stock < existing_item.quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock")
    else:
        cart_item = CartItem(
            cart_id=cart.id,
            product_id=item.product_id,
            quantity=item.quantity
        )
        db.add(cart_item)

    await db.commit()
    return {"message": "Item added to cart"}

@router.put("/items/{item_id}")
async def update_cart_item(
    item_id: int,
    item_update: CartItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cart = await get_or_create_cart(current_user.id, db)

    result = await db.execute(
        select(CartItem, Product)
        .join(Product, CartItem.product_id == Product.id)
        .where(CartItem.id == item_id, CartItem.cart_id == cart.id)
    )
    cart_item_data = result.first()

    if not cart_item_data:
        raise HTTPException(status_code=404, detail="Cart item not found")

    cart_item, product = cart_item_data

    if item_update.quantity <= 0:
        await db.delete(cart_item)
    else:
        if product.stock < item_update.quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock")
        cart_item.quantity = item_update.quantity

    await db.commit()
    return {"message": "Cart item updated"}

@router.delete("/items/{item_id}")
async def remove_cart_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cart = await get_or_create_cart(current_user.id, db)

    result = await db.execute(
        select(CartItem).where(CartItem.id == item_id, CartItem.cart_id == cart.id)
    )
    cart_item = result.scalar_one_or_none()

    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    await db.delete(cart_item)
    await db.commit()
    return {"message": "Cart item removed"}
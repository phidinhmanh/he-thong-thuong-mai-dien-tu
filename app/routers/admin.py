from fastapi import APIRouter, Depends, HTTPException, Query, Request, File, UploadFile
from app.utils.cloudinary import upload_image
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract, case
from typing import List, Optional
from datetime import datetime, timedelta
import json
from app.core.database import get_db
from app.models.models import Product, Order, User, Category, AuditLog, OrderItem, PriceHistory
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.schemas.order import OrderUpdate, OrderResponse
from app.routers.auth import get_current_admin
from app.models.models import User as UserModel

from app.core.websocket import manager

router = APIRouter()

# ===================== PRODUCTS =====================

async def log_action(db: AsyncSession, user_id: int, action: str, resource_type: str, resource_id: int, details: dict, request: Request):
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=json.dumps(details),
        ip_address=request.client.host
    )
    db.add(audit_log)
    await db.commit()

@router.get("/products")
async def admin_list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin)
):
    result = await db.execute(
        select(Product)
        .order_by(Product.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    products = result.scalars().all()
    return products

@router.post("/products")
async def admin_create_product(
    product: ProductCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin)
):
    slug = product.slug or product.name.lower().replace(" ", "-")
    db_product = Product(**product.model_dump(), slug=slug)
    db.add(db_product)
    await db.flush()

    # Track price history
    price_hist = PriceHistory(product_id=db_product.id, price=db_product.price)
    db.add(price_hist)

    await log_action(db, current_user.id, "CREATE_PRODUCT", "Product", db_product.id, product.model_dump(), request)

    await db.commit()
    await db.refresh(db_product)
    return db_product

@router.put("/products/{product_id}")
async def admin_update_product(
    product_id: int,
    product: ProductUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin)
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    db_product = result.scalar_one_or_none()

    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    old_price = db_product.price
    update_data = product.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_product, key, value)

    # Track price history if price changed
    if "price" in update_data and update_data["price"] != old_price:
        price_hist = PriceHistory(product_id=db_product.id, price=db_product.price)
        db.add(price_hist)

    await log_action(db, current_user.id, "UPDATE_PRODUCT", "Product", product_id, update_data, request)

    await db.commit()
    await db.refresh(db_product)
    return db_product

@router.post("/products/{product_id}/image")
async def admin_upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin)
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    image_url = await upload_image(file.file)
    product.image_url = image_url
    await db.commit()
    return {"image_url": image_url}

@router.get("/analytics/revenue")
async def admin_revenue_analytics(
    days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin)
):
    # Daily revenue for the last X days
    start_date = datetime.now() - timedelta(days=days)

    result = await db.execute(
        select(
            func.date(Order.created_at).label("date"),
            func.sum(Order.total).label("revenue"),
            func.count(Order.id).label("orders")
        )
        .where(Order.created_at >= start_date)
        .group_by(func.date(Order.created_at))
        .order_by("date")
    )
    return result.mappings().all()

@router.get("/analytics/top-products")
async def admin_top_products(
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin)
):
    result = await db.execute(
        select(
            Product.name,
            func.sum(OrderItem.quantity).label("total_sold"),
            func.sum(OrderItem.quantity * OrderItem.price).label("total_revenue")
        )
        .join(OrderItem, Product.id == OrderItem.product_id)
        .group_by(Product.id)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(limit)
    )
    return result.mappings().all()

@router.get("/audit-logs")
async def admin_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin)
):
    result = await db.execute(
        select(AuditLog)
        .order_by(AuditLog.timestamp.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    logs = result.scalars().all()
    return logs

@router.delete("/products/{product_id}")
async def admin_delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    await db.delete(product)
    await db.commit()
    return {"message": "Product deleted"}

# ===================== CATEGORIES =====================

@router.get("/categories")
async def admin_list_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    result = await db.execute(select(Category).order_by(Category.name))
    categories = result.scalars().all()
    return [{"id": c.id, "name": c.name, "slug": c.slug} for c in categories]

@router.post("/categories")
async def admin_create_category(
    category: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    slug = category.slug or category.name.lower().replace(" ", "-")
    db_category = Category(**category.model_dump(), slug=slug)
    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    return {"id": db_category.id, "name": db_category.name, "slug": db_category.slug}

@router.put("/categories/{category_id}")
async def admin_update_category(
    category_id: int,
    category: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    result = await db.execute(select(Category).where(Category.id == category_id))
    db_category = result.scalar_one_or_none()

    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    for key, value in category.model_dump(exclude_unset=True).items():
        setattr(db_category, key, value)

    await db.commit()
    await db.refresh(db_category)
    return {"message": "Category updated"}

# ===================== ORDERS =====================

@router.get("/orders")
async def admin_list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    query = select(Order).order_by(Order.created_at.desc())

    if status:
        query = query.where(Order.status == status)

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    orders = result.scalars().all()

    count_query = select(func.count()).select_from(Order)
    if status:
        count_query = count_query.where(Order.status == status)
    count_result = await db.execute(count_query)
    total = count_result.scalar()

    return {
        "items": [{"id": o.id, "user_id": o.user_id, "status": o.status,
                   "total": o.total, "created_at": o.created_at} for o in orders],
        "total": total, "page": page, "page_size": page_size
    }

@router.get("/orders/{order_id}")
async def admin_get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return {"id": order.id, "user_id": order.user_id, "status": order.status,
            "total": order.total, "shipping_address": order.shipping_address,
            "phone": order.phone, "created_at": order.created_at}

@router.put("/orders/{order_id}/status")
async def admin_update_order_status(
    order_id: int,
    status_update: OrderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = status_update.status
    await db.commit()

    # Notify user via WebSocket
    await manager.send_personal_message(
        {
            "type": "ORDER_STATUS_UPDATE",
            "order_id": order_id,
            "status": order.status,
            "message": f"Đơn hàng #{order_id} của bạn đã chuyển sang trạng thái: {order.status}"
        },
        order.user_id
    )

    return {"message": "Order status updated"}

# ===================== USERS =====================

@router.get("/users")
async def admin_list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    result = await db.execute(
        select(User)
        .order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    users = result.scalars().all()

    count_result = await db.execute(select(func.count()).select_from(User))
    total = count_result.scalar()

    return {
        "items": [{"id": u.id, "email": u.email, "username": u.username,
                   "full_name": u.full_name, "role": u.role, "created_at": u.created_at}
                  for u in users],
        "total": total
    }

@router.get("/stats")
async def admin_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    products_count = await db.execute(select(func.count()).select_from(Product))
    total_products = products_count.scalar()

    orders_count = await db.execute(select(func.count()).select_from(Order))
    total_orders = orders_count.scalar()

    users_count = await db.execute(select(func.count()).select_from(User))
    total_users = users_count.scalar()

    pending_count = await db.execute(
        select(func.count()).select_from(Order).where(Order.status == "pending")
    )
    pending_orders = pending_count.scalar()

    return {
        "total_products": total_products,
        "total_orders": total_orders,
        "total_users": total_users,
        "pending_orders": pending_orders
    }
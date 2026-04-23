from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from app.core.database import get_db
from app.models.models import Product, Category
from app.schemas.product import ProductResponse, ProductCreate, ProductUpdate
from app.schemas.category import CategoryResponse, CategoryCreate, CategoryUpdate
from app.routers.auth import get_current_user, get_current_admin
from app.models.models import User

from app.core.search import fuzzy_search_products

router = APIRouter()

@router.get("/search")
async def search_products(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    products = await fuzzy_search_products(db, q, limit)
    return products

@router.get("/categories", response_model=List[CategoryResponse])
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).order_by(Category.name))
    categories = result.scalars().all()
    return categories

@router.post("/categories")
async def create_category(
    category: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    # Generate slug
    slug = category.slug or category.name.lower().replace(" ", "-")
    db_category = Category(**category.model_dump(), slug=slug)
    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    return db_category

@router.get("/")
async def list_products(
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    query = select(Product).where(Product.is_active == 1)
    count_query = select(func.count()).select_from(Product).where(Product.is_active == 1)

    if category_id:
        query = query.where(Product.category_id == category_id)
        count_query = count_query.where(Product.category_id == category_id)

    if search:
        search_filter = f"%{search}%"
        query = query.where(Product.name.ilike(search_filter))
        count_query = count_query.where(Product.name.ilike(search_filter))

    # Count total
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get paginated results
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    products = result.scalars().all()

    return {
        "items": products,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/{product_id}")
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
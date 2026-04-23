# Seed script - Run after starting backend to create admin user and sample data
import asyncio
from app.core.database import async_session_maker
from app.models.models import User, Product, Category, Voucher, FlashSale, FlashSaleItem, PriceHistory
from datetime import datetime, timedelta
from app.core.security import get_password_hash

async def seed():
    async with async_session_maker() as db:
        admin = User(
            email="admin@amazon.com",
            username="admin",
            full_name="Admin User",
            hashed_password=get_password_hash("admin123"),
            role="admin"
        )
        db.add(admin)

        # Create sample user
        user = User(
            email="user@example.com",
            username="user",
            full_name="Test User",
            hashed_password=get_password_hash("user123"),
            role="customer"
        )
        db.add(user)

        # Create categories
        categories = [
            Category(name="Electronics", slug="electronics", description="Electronic devices"),
            Category(name="Clothing", slug="clothing", description="Fashion and apparel"),
            Category(name="Books", slug="books", description="Books and literature"),
            Category(name="Home & Garden", slug="home-garden", description="Home and garden items"),
        ]
        for cat in categories:
            db.add(cat)

        await db.commit()

        # Create products
        products = [
            Product(name="Laptop Pro 15", slug="laptop-pro-15", price=1299.99, stock=50, image_url="https://picsum.photos/400/400?random=1", category_id=1, brand="TechBrand"),
            Product(name="Wireless Mouse", slug="wireless-mouse", price=29.99, stock=100, image_url="https://picsum.photos/400/400?random=2", category_id=1, brand="TechBrand"),
            Product(name="Smartphone X", slug="smartphone-x", price=899.99, stock=75, image_url="https://picsum.photos/400/400?random=3", category_id=1, brand="PhoneCorp"),
            Product(name="T-Shirt Classic", slug="t-shirt-classic", price=19.99, stock=200, image_url="https://picsum.photos/400/400?random=4", category_id=2, brand="FashionCo"),
            Product(name="Jeans Slim Fit", slug="jeans-slim-fit", price=49.99, stock=150, image_url="https://picsum.photos/400/400?random=5", category_id=2, brand="FashionCo"),
            Product(name="Python Programming", slug="python-programming", price=39.99, stock=80, image_url="https://picsum.photos/400/400?random=6", category_id=3, brand="TechBooks"),
            Product(name="JavaScript Guide", slug="javascript-guide", price=34.99, stock=60, image_url="https://picsum.photos/400/400?random=7", category_id=3, brand="TechBooks"),
            Product(name="Garden Chair", slug="garden-chair", price=89.99, stock=40, image_url="https://picsum.photos/400/400?random=8", category_id=4, brand="GardenCo"),
        ]
        for product in products:
            db.add(product)

        await db.commit()

        # Create vouchers
        vouchers = [
            Voucher(code="WELCOME10", discount_type="percentage", discount_value=10, min_order_value=100, is_active=True),
            Voucher(code="SAVE50", discount_type="fixed", discount_value=50, min_order_value=500, is_active=True),
        ]
        for v in vouchers:
            db.add(v)

        # Create Flash Sale
        sale = FlashSale(
            name="Weekend Mega Sale",
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(days=2),
            is_active=True
        )
        db.add(sale)
        await db.flush()

        sale_item = FlashSaleItem(
            flash_sale_id=sale.id,
            product_id=1,  # Laptop
            sale_price=999.99,
            stock_limit=10
        )
        db.add(sale_item)

        # Create Price History for products
        for p in products:
            # Add some history
            hist1 = PriceHistory(product_id=p.id, price=p.price * 1.1, created_at=datetime.now() - timedelta(days=10))
            hist2 = PriceHistory(product_id=p.id, price=p.price, created_at=datetime.now() - timedelta(days=5))
            db.add(hist1)
            db.add(hist2)

        await db.commit()
        print("Seeded: 1 admin, 1 user, 4 categories, 8 products, 2 vouchers, 1 flash sale")

if __name__ == "__main__":
    asyncio.run(seed())
import pytest
from app.models.models import Order, OrderItem, Product, Category
from datetime import datetime

@pytest.mark.asyncio
async def test_revenue_analytics(admin_client, db_session, admin_user):
    # 1. Setup data
    cat = Category(name="Test", slug="test")
    db_session.add(cat)
    await db_session.commit()
    await db_session.refresh(cat)

    p1 = Product(name="P1", price=100, category_id=cat.id)
    p2 = Product(name="P2", price=200, category_id=cat.id)
    db_session.add_all([p1, p2])
    await db_session.commit()
    await db_session.refresh(p1)
    await db_session.refresh(p2)

    # Order 1
    o1 = Order(user_id=admin_user.id, total=300, status="delivered")
    db_session.add(o1)
    await db_session.flush()
    db_session.add_all([
        OrderItem(order_id=o1.id, product_id=p1.id, quantity=1, price=100, product_name="P1"),
        OrderItem(order_id=o1.id, product_id=p2.id, quantity=1, price=200, product_name="P2")
    ])

    # Order 2 (today)
    o2 = Order(user_id=admin_user.id, total=100, status="confirmed")
    db_session.add(o2)
    await db_session.flush()
    db_session.add(OrderItem(order_id=o2.id, product_id=p1.id, quantity=1, price=100, product_name="P1"))

    await db_session.commit()

    # 2. Test Revenue API
    response = await admin_client.get("/api/admin/analytics/revenue?days=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["revenue"] == 400
    assert data[0]["orders"] == 2

@pytest.mark.asyncio
async def test_top_products_analytics(admin_client, db_session):
    # Data is already there from previous test or we add more
    # Let's check the current results
    response = await admin_client.get("/api/admin/analytics/top-products?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    # P1 should be top since it has 2 units sold (1 in o1, 1 in o2)
    assert data[0]["name"] == "P1"
    assert data[0]["total_sold"] == 2
    assert data[0]["total_revenue"] == 200

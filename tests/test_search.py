import pytest
from app.models.models import Product, Category
from sqlalchemy import select

@pytest.mark.asyncio
async def test_fts_triggers_and_search(client, db_session):
    # 1. Create a category
    cat = Category(name="Electronics", slug="electronics")
    db_session.add(cat)
    await db_session.commit()
    await db_session.refresh(cat)

    # 2. Add products
    p1 = Product(name="Apple iPhone 15 Pro", description="Latest Apple smartphone", price=999.99, category_id=cat.id)
    p2 = Product(name="Samsung Galaxy S23", description="Flagship Android phone", price=899.99, category_id=cat.id)
    db_session.add_all([p1, p2])
    await db_session.commit()

    # 3. Test Search (prefix matching)
    response = await client.get("/api/products/search?q=App")
    assert response.status_code == 200
    results = response.json()
    assert len(results) >= 1
    assert any("iPhone" in p["name"] for p in results)

    response = await client.get("/api/products/search?q=phone")
    assert response.status_code == 200
    results = response.json()
    assert len(results) >= 2

    # 4. Test Trigger on Update
    p1.name = "Apple iPhone 15 Pro Max"
    db_session.add(p1)
    await db_session.commit()

    response = await client.get("/api/products/search?q=Max")
    assert response.status_code == 200
    results = response.json()
    assert any("Max" in p["name"] for p in results)

    # 5. Test Trigger on Delete
    await db_session.delete(p2)
    await db_session.commit()

    response = await client.get("/api/products/search?q=Samsung")
    assert response.status_code == 200
    results = response.json()
    assert not any("Samsung" in p["name"] for p in results)

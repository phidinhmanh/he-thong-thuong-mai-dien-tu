import pytest
from app.models.models import Voucher, Category, Product, FlashSale, FlashSaleItem
from datetime import datetime, timedelta

@pytest.mark.asyncio
async def test_voucher_validation(client, db_session):
    # 1. Create a voucher
    v1 = Voucher(
        code="SAVE10",
        discount_type="percentage",
        discount_value=10,
        min_order_value=100,
        is_active=True
    )
    # Expired voucher
    v2 = Voucher(
        code="EXPIRED",
        discount_type="fixed",
        discount_value=20,
        min_order_value=50,
        expiry_date=datetime.now() - timedelta(days=1),
        is_active=True
    )
    db_session.add_all([v1, v2])
    await db_session.commit()

    # 2. Test Success
    response = await client.get("/api/sales/vouchers/validate/SAVE10?total_amount=150")
    assert response.status_code == 200
    assert response.json()["code"] == "SAVE10"

    # 3. Test Failure - Min Amount
    response = await client.get("/api/sales/vouchers/validate/SAVE10?total_amount=50")
    assert response.status_code == 400
    assert "at least 100" in response.json()["detail"]

    # 4. Test Failure - Expired
    response = await client.get("/api/sales/vouchers/validate/EXPIRED?total_amount=100")
    assert response.status_code == 404

    # 5. Test Failure - Non-existent
    response = await client.get("/api/sales/vouchers/validate/GHOST?total_amount=100")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_flash_sale_listing(client, db_session):
    cat = Category(name="Electronics", slug="elec")
    db_session.add(cat)
    await db_session.commit()
    await db_session.refresh(cat)

    p = Product(name="Sale Phone", price=1000, category_id=cat.id)
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)

    sale = FlashSale(
        name="Mega Sale",
        start_time=datetime.now(),
        end_time=datetime.now() + timedelta(hours=2),
        is_active=True
    )
    db_session.add(sale)
    await db_session.flush()

    item = FlashSaleItem(
        flash_sale_id=sale.id,
        product_id=p.id,
        sale_price=500,
        stock_limit=10
    )
    db_session.add(item)
    await db_session.commit()

    response = await client.get("/api/sales/flash-sales")
    assert response.status_code == 200
    sales = response.json()
    assert len(sales) >= 1
    assert sales[0]["name"] == "Mega Sale"
    assert len(sales[0]["items"]) == 1
    assert sales[0]["items"][0]["sale_price"] == 500

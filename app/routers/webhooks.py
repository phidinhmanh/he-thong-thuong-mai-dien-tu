import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.models import Order, OrderStatus
from app.core.config import settings
from app.core.websocket import manager

stripe.api_key = settings.STRIPE_SECRET_KEY

router = APIRouter()

@router.post("/stripe-webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None)
):
    """
    Handle Stripe webhooks for payment success.
    """
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        order_id = int(session['metadata']['order_id'])

        # Update order status in a new session (webhooks are async/background)
        from app.core.database import async_session_maker
        async with async_session_maker() as db:
            result = await db.execute(select(Order).where(Order.id == order_id))
            order = result.scalar_one_or_none()
            if order:
                order.status = OrderStatus.CONFIRMED.value
                await db.commit()

                # Notify user via WebSocket
                await manager.send_personal_message(
                    {
                        "type": "PAYMENT_SUCCESS",
                        "order_id": order_id,
                        "message": f"Thanh toán thành công cho đơn hàng #{order_id}!"
                    },
                    order.user_id
                )

    return {"status": "success"}

async def create_stripe_checkout(order_id: int, total: float, items_summary: str):
    """
    Helper to create a Stripe checkout session.
    """
    if not settings.STRIPE_SECRET_KEY:
        # Fallback for dev
        return "https://checkout.stripe.com/pay/fake_session"

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': f"Order #{order_id}",
                    'description': items_summary,
                },
                'unit_amount': int(total * 100),
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url='http://localhost:5173/order/success?id=' + str(order_id),
        cancel_url='http://localhost:5173/order/cancel?id=' + str(order_id),
        metadata={
            'order_id': str(order_id)
        }
    )
    return session.url

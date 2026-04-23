from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine
from app.models import Base
from app.routers import auth as auth_router, products as products_router
from app.routers import cart as cart_router, orders as orders_router, admin as admin_router, sales as sales_router, webhooks as webhooks_router

from app.core.search import setup_fts

from app.core.websocket import manager
from app.core.security import decode_access_token
from fastapi import WebSocket, WebSocketDisconnect

app = FastAPI(
    title="Amazon Clone API",
    description="API for simplified Amazon-like e-commerce",
    version="1.0.0",
)

@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=1008)
        return

    user_id = payload.get("user_id")
    await manager.connect(websocket, user_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router.router, prefix="/api/auth", tags=["auth"])
app.include_router(products_router.router, prefix="/api/products", tags=["products"])
app.include_router(cart_router.router, prefix="/api/cart", tags=["cart"])
app.include_router(orders_router.router, prefix="/api/orders", tags=["orders"])
app.include_router(admin_router.router, prefix="/api/admin", tags=["admin"])
app.include_router(sales_router.router, prefix="/api/sales", tags=["sales"])
app.include_router(webhooks_router.router, prefix="/api/webhooks", tags=["webhooks"])

@app.on_event("startup")
async def startup():
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Setup FTS search
    from app.core.database import async_session_maker
    async with async_session_maker() as db:
        await setup_fts(db)

@app.get("/")
async def root():
    return {"message": "Amazon Clone API", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
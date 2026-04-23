# Advanced E-commerce Backend


## 🚀 Feature

- **Fuzzy Search (SQLite FTS5)**: Tìm kiếm sản phẩm thông minh, hỗ trợ sửa lỗi gõ sai và tìm kiếm theo tiền tố dựa trên engine Full-Text Search tích hợp sâu vào Database.
- **Real-time WebSockets**: Hệ thống thông báo đơn hàng và cập nhật Flash Sale theo thời gian thực (Bi-directional communication).
- **Hệ thống Flash Sale & Voucher**: Logic khuyến mãi phức tạp với giới hạn thời gian, số lượng (stock limit) và điều kiện áp dụng voucher (min order value).
- **Admin Analytics & Audit Logs**: Hệ thống thống kê doanh thu (Aggregation) và ghi lại lịch sử hoạt động của quản trị viên để đảm bảo an toàn hệ thống.
- **Tích hợp Thanh toán & Media**: Kết nối thực tế với **Stripe** (Thanh toán) và **Cloudinary** (Quản lý hình ảnh).
- **Testing Suite**: Hệ thống kiểm thử tự động (Unit & Integration Tests) với 100% pass rate cho các logic cốt lõi.

## 🛠 Công nghệ sử dụng

- **Framework**: FastAPI (Asynchronous)
- **Database**: SQLite (SQLAlchemy 2.0 Asyncio + aiosqlite)
- **Security**: JWT Authentication, Password Hashing (Bcrypt)
- **Validation**: Pydantic v2 (Strict validation)
- **Testing**: Pytest, Pytest-asyncio, HTTPX

## 📋 Hướng dẫn chạy cục bộ (Local Development)

### 1. Cài đặt môi trường
Yêu cầu Python 3.10+ và đã cài `uv`.

```bash
# Clone dự án và truy cập thư mục backend
cd backend

# Tạo môi trường và cài đặt thư viện
uv sync
```

Nếu chưa có `uv`, cài nhanh bằng:

```bash
pip install uv
```

### 2. Cấu hình biến môi trường
Tạo file `.env` tại thư mục gốc của backend:

```env
SECRET_KEY=your_very_secret_key_here
DATABASE_URL=sqlite+aiosqlite:///./amazon_clone.db

# (Tùy chọn) Media & Payment
CLOUDINARY_CLOUD_NAME=your_name
CLOUDINARY_API_KEY=your_key
CLOUDINARY_API_SECRET=your_secret
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### 3. Khởi tạo Database & Seed Data
```bash
uv run python seed.py
```
*Mặc định sẽ tạo:*
- Admin: `admin@test.com` / `admin123`
- User: `user@test.com` / `password123`

### 4. Chạy Server
```bash
uv run python main.py
```
Truy cập Swagger UI tại: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## 🧪 Kiểm thử (Testing)
Dự án đi kèm bộ test diện rộng để đảm bảo chất lượng:
```bash
uv run pytest
```

---

## ☁️ Hướng dẫn triển khai lên Vercel (Deployment)

Vercel hỗ trợ tốt FastAPI thông qua Serverless Functions. Tuy nhiên, lưu ý rằng **SQLite không phù hợp để lưu trữ lâu dài trên Vercel** (do hệ thống file của Vercel là read-only). Để chạy thực tế, bạn nên đổi sang PostgreSQL (Neon.tech hoặc Supabase).

### Bước 1: Chuẩn bị file `vercel.json`
Tạo file `vercel.json` ở thư mục gốc backend:
```json
{
  "version": 2,
  "builds": [
    {
      "src": "main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "main.py"
    }
  ]
}
```

### Bước 2: Cập nhật `main.py` cho Vercel
Đảm bảo biến `app` được khởi tạo đúng và không chạy `uvicorn.run()` khi ở môi trường production của Vercel.

### Bước 3: Đẩy mã nguồn lên GitHub
Tạo repo mới trên GitHub và push code lên.

### Bước 4: Import vào Vercel
1. Truy cập [Vercel Dashboard](https://vercel.com/dashboard).
2. Chọn "Add New" -> "Project" -> Import từ GitHub.
3. Trong phần **Environment Variables**, thêm các biến từ file `.env`.
4. Nhấn **Deploy**.

**Lưu ý quan trọng cho Vercel:**
- SQLite sẽ bị reset mỗi khi serverless function restart. Bạn nên dùng `DATABASE_URL` trỏ tới một DB bên ngoài (PostgreSQL).
- Cập nhật `BACKEND_CORS_ORIGINS` trong `.env` để cho phép domain frontend của bạn.

---
**Author**: phimanh
**Project**: Amazon Clone Pro - UET Advanced Coding Assignment

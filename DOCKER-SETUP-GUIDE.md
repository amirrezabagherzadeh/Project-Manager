# راهنمای انتقال پروژه به لپ‌تاپ دیگر (Docker)

این پوشه شامل کد کامل پروژه + تصاویر (Images) ساخته‌شدهٔ Docker است؛
می‌توانید پروژه را روی هر ماشینی که Docker دارد فوراً اجرا کنید یا توسعه را ادامه دهید.

## پیش‌نیازها روی لپ‌تاپ مقصد
- Docker Desktop (Windows/macOS) یا Docker Engine (Linux)
- برای توسعه‌ی محلی خارج از Docker: uv، Python 3.12، Node.js 20.9+، pnpm 10.30.1

## روش ۱ — اجرای فوری بدون Build (پیشنهادی)
1. از این Zip خارج شوید (Extract).
2. تصاویر را Load کنید:
   docker load -i docker-images/backend.tar
   docker load -i docker-images/frontend.tar
3. سرویس‌ها را بالا بیاورید (اینجا از Image موجود استفاده می‌شود، Build مجدد نمی‌شود):
   docker compose up -d
   (در صورت تمایل ابتدا Schema را بسازید:
    docker compose run --rm backend uv run --no-dev alembic upgrade head)
4. برنامه را باز کنید:
   - Frontend: http://localhost:3000
   - Backend Health: http://localhost:8000/health
   - Swagger: http://localhost:8000/docs

## روش ۲ — توسعه / Build مجدد از سورس
بعد از Load کردن تصاویر یا بدون آن، از سورس بسازید:
   docker compose up --build -d

اگر بخواهید بدون Docker توسعه دهید، دستورالعمل‌های کامل در README.md هست.

## پاکسازی
   docker compose down
   (برای حذف کامل Volume داده:
    docker compose down -v)

## نکات
- نام تصاویر: projectmanagerapp-backend:latest و projectmanagerapp-frontend:latest
- دادهٔ Backend در Volume به نام backend-data ذخیره می‌شود و پایدار است.
- فایل‌های .env واقعی در سورس نیستند؛ از روی .env.example بسازید.

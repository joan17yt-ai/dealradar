import urllib.parse
from typing import List, Optional
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.database import get_db, init_db, User, ProductAlert, PriceHistory, FeaturedDeal
from app.scrapers.manager import scraper_manager
from app.services.tracker import check_alerts_job
from app.services.notifications import init_firebase

scheduler = AsyncIOScheduler()

def seed_initial_deals(db: Session):
    # Limpiar y regenerar con URLs 100% funcionales (sin errores 404)
    db.query(FeaturedDeal).delete()
    deals = [
        FeaturedDeal(
            title="iPhone 15 128GB Negro",
            store="Mercado Libre",
            category="Celulares",
            current_price_cop=3499000.0,
            original_price_cop=4299000.0,
            discount_percentage=18,
            product_url="https://listado.mercadolibre.com.co/iphone-15",
            image_url="https://http2.mlstatic.com/D_NQ_NP_893049-MLA71782867320_092023-O.webp",
            badge="MÍNIMO HISTÓRICO"
        ),
        FeaturedDeal(
            title="Portátil ASUS Vivobook 15 Core i5 16GB 512GB SSD",
            store="Alkosto",
            category="Computadores",
            current_price_cop=2199000.0,
            original_price_cop=2899000.0,
            discount_percentage=24,
            # URL de búsqueda directa garantizada que nunca da 404
            product_url="https://www.alkosto.com/search?text=asus+vivobook+15+i5",
            image_url="https://alkosto.vtexassets.com/arquivos/ids/1449339-1200-auto",
            badge="OFERTA FLASH"
        ),
        FeaturedDeal(
            title="Nevera No Frost Haceb 311 Litros Titanio",
            store="Éxito",
            category="Neveras",
            current_price_cop=1649900.0,
            original_price_cop=2299900.0,
            discount_percentage=28,
            # URL de búsqueda directa en Éxito que nunca da 404
            product_url="https://www.exito.com/nevera-haceb-311?_q=nevera-haceb-311&map=ft",
            image_url="https://exitocol.vtexassets.com/arquivos/ids/20141753/Nevera-No-Frost-311-L-Titanio-HACEB-3103233_a.jpg",
            badge="MEJOR PRECIO"
        ),
        FeaturedDeal(
            title="Parlante Bluetooth JBL Flip 6 Resistente al Agua",
            store="Amazon",
            category="Parlantes",
            current_price_cop=439000.0,
            original_price_cop=599000.0,
            discount_percentage=26,
            product_url="https://www.amazon.com/s?k=jbl+flip+6",
            image_url="https://m.media-amazon.com/images/I/71u9s2a4+bL._AC_SL1500_.jpg",
            badge="GANGA DEL DÍA"
        ),
        FeaturedDeal(
            title="Samsung Galaxy S24 Ultra 256GB Titanium Gray",
            store="Mercado Libre",
            category="Celulares",
            current_price_cop=4799000.0,
            original_price_cop=5699000.0,
            discount_percentage=15,
            product_url="https://listado.mercadolibre.com.co/samsung-s24-ultra",
            image_url="https://http2.mlstatic.com/D_NQ_NP_977348-MLA74075193952_012024-O.webp",
            badge="PRECIO BAJO"
        ),
        FeaturedDeal(
            title="Impresora Multifuncional Epson EcoTank L3250 WiFi",
            store="Mercado Libre",
            category="Computadores",
            current_price_cop=789000.0,
            original_price_cop=999000.0,
            discount_percentage=21,
            product_url="https://listado.mercadolibre.com.co/impresora-epson-ecotank-l3250",
            image_url="https://http2.mlstatic.com/D_NQ_NP_753198-MLA48446261358_122021-O.webp",
            badge="OFERTA POPULAR"
        )
    ]
    db.add_all(deals)
    db.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    init_firebase()
    from app.database import SessionLocal
    db = SessionLocal()
    seed_initial_deals(db)
    db.close()

    scheduler.add_job(check_alerts_job, "interval", minutes=settings.TRACKING_INTERVAL_MINUTES)
    scheduler.start()
    print(f"[DealRadar] Scheduler started (interval: {settings.TRACKING_INTERVAL_MINUTES} min)")
    yield
    scheduler.shutdown()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DeviceRegisterRequest(BaseModel):
    device_id: Optional[str] = None
    deviceId: Optional[str] = None
    fcm_token: Optional[str] = None

class CreateAlertRequest(BaseModel):
    device_id: str
    product_title: str
    query_keyword: str
    category: Optional[str] = "general"
    target_price_cop: float
    current_best_price_cop: Optional[float] = None
    best_store: Optional[str] = None
    product_url: Optional[str] = None
    image_url: Optional[str] = None

@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.PROJECT_NAME, "version": settings.VERSION}

@app.post("/api/user/register")
def register_device(req: DeviceRegisterRequest, db: Session = Depends(get_db)):
    final_id = req.device_id or req.deviceId or "anonymous_device"
    user = db.query(User).filter(User.device_id == final_id).first()
    if not user:
        user = User(device_id=final_id, fcm_token=req.fcm_token)
        db.add(user)
    else:
        if req.fcm_token:
            user.fcm_token = req.fcm_token
    db.commit()
    db.refresh(user)
    return {"status": "success", "user_id": user.id, "device_id": user.device_id, "saved_cop": user.total_saved_cop}

@app.get("/api/search")
async def search_stores(q: str = Query(..., description="Término de búsqueda del producto")):
    products = await scraper_manager.search_all_stores(q, limit_per_store=4)
    return {
        "query": q,
        "total_results": len(products),
        "results": [
            {
                "title": p.title,
                "price_cop": p.price_cop,
                "original_price_cop": p.original_price_cop,
                "discount_percentage": p.discount_percentage,
                "store": p.store,
                "product_url": p.product_url,
                "image_url": p.image_url,
                "is_available": p.is_available
            } for p in products
        ]
    }

@app.get("/api/deals/feed")
def get_featured_deals(category: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(FeaturedDeal)
    if category and category.lower() != "todos":
        query = query.filter(FeaturedDeal.category.ilike(f"%{category}%"))
    deals = query.order_by(FeaturedDeal.discount_percentage.desc()).all()
    return {
        "deals": [
            {
                "id": d.id,
                "title": d.title,
                "store": d.store,
                "category": d.category,
                "current_price_cop": d.current_price_cop,
                "original_price_cop": d.original_price_cop,
                "discount_percentage": d.discount_percentage,
                "product_url": d.product_url,
                "image_url": d.image_url,
                "badge": d.badge
            } for d in deals
        ]
    }

@app.post("/api/alerts")
def create_alert(req: CreateAlertRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.device_id == req.device_id).first()
    if not user:
        user = User(device_id=req.device_id)
        db.add(user)
        db.commit()
        db.refresh(user)

    alert = ProductAlert(
        user_id=user.id,
        product_title=req.product_title,
        query_keyword=req.query_keyword,
        category=req.category or "general",
        target_price_cop=req.target_price_cop,
        current_best_price_cop=req.current_best_price_cop,
        best_store=req.best_store,
        product_url=req.product_url,
        image_url=req.image_url,
        is_active=True
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return {"status": "created", "alert_id": alert.id, "product": alert.product_title}

@app.get("/api/alerts")
def list_user_alerts(device_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.device_id == device_id).first()
    if not user:
        return {"alerts": []}
    alerts = db.query(ProductAlert).filter(ProductAlert.user_id == user.id).all()
    return {
        "alerts": [
            {
                "id": a.id,
                "product_title": a.product_title,
                "query_keyword": a.query_keyword,
                "category": a.category,
                "target_price_cop": a.target_price_cop,
                "current_best_price_cop": a.current_best_price_cop,
                "best_store": a.best_store,
                "product_url": a.product_url,
                "image_url": a.image_url,
                "is_active": a.is_active,
                "created_at": a.created_at.isoformat() if a.created_at else None
            } for a in alerts
        ]
    }

@app.delete("/api/alerts/{alert_id}")
def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(ProductAlert).filter(ProductAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    db.delete(alert)
    db.commit()
    return {"status": "deleted", "alert_id": alert_id}

@app.get("/api/user/savings")
def get_user_savings(device_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.device_id == device_id).first()
    if not user:
        return {"total_saved_cop": 0.0, "alerts_count": 0, "rank": "Explorador Novato"}
    count = db.query(ProductAlert).filter(ProductAlert.user_id == user.id).count()
    return {"total_saved_cop": user.total_saved_cop, "alerts_count": count, "rank": "Cazador Activo"}

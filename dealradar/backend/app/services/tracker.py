from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal, ProductAlert, PriceHistory, User
from app.scrapers.manager import scraper_manager
from app.services.notifications import send_deal_push_notification

async def check_alerts_job():
    print("[Tracker Job] Running price monitoring check...")
    db: Session = SessionLocal()
    try:
        active_alerts = db.query(ProductAlert).filter(ProductAlert.is_active == True).all()
        for alert in active_alerts:
            user = db.query(User).filter(User.id == alert.user_id).first()
            if not user:
                continue

            products = await scraper_manager.search_all_stores(alert.query_keyword, limit_per_store=3)
            if not products:
                continue

            best_match = products[0] # Ya ordenados por precio ascendente
            
            # Registrar historial
            history_entry = PriceHistory(
                alert_id=alert.id,
                store=best_match.store,
                price_cop=best_match.price_cop,
                recorded_at=datetime.utcnow()
            )
            db.add(history_entry)

            # Actualizar precio actual
            alert.current_best_price_cop = best_match.price_cop
            alert.best_store = best_match.store
            alert.product_url = best_match.product_url
            if best_match.image_url:
                alert.image_url = best_match.image_url

            # Evaluar si cumple con la condición de alerta
            if best_match.price_cop <= alert.target_price_cop:
                # Comprobar si no se ha notificado recientemente (o si el precio bajó aún más)
                discount_amount = alert.target_price_cop - best_match.price_cop
                title = f"¡Alerta de Oferta! {alert.product_title}"
                body = f"Bajó a ${best_match.price_cop:,.0f} COP en {best_match.store}. ¡Ahorras ${discount_amount:,.0f} COP!"
                
                payload = {
                    "alert_id": str(alert.id),
                    "product_url": best_match.product_url or "",
                    "store": best_match.store,
                    "price_cop": str(best_match.price_cop)
                }

                if user.fcm_token:
                    sent = send_deal_push_notification(user.fcm_token, title, body, payload)
                    if sent:
                        alert.last_notified_at = datetime.utcnow()
                        user.total_saved_cop += max(0.0, discount_amount)

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[Tracker Job Error] {e}")
    finally:
        db.close()

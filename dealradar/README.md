# 📡 DealRadar — Alerta de Ofertas y Rastreador de Precios en Colombia

**DealRadar** es una plataforma completa (App Android en Kotlin/Jetpack Compose + Backend en Python/FastAPI) diseñada para rastrear precios y notificar al instante cuando un producto baja de precio en las principales tiendas de Colombia (**Mercado Libre, Alkosto, Éxito, Amazon**, etc.).

---

## 🚀 Características Principales

1. **Radar de Gangas (Feed Dinámico)**:
   - Detección automática de caídas de precio drásticas en las últimas 24 horas en Colombia.
   - Filtros por categorías clave: **Celulares, Computadores, Neveras, Parlantes y Audio**.
   - Semáforo de precio: Mínimo histórico, oferta flash y precio real verificado.

2. **Buscador Multitienda en Tiempo Real**:
   - Compara en paralelo el mismo producto en distintas tiendas para ver cuál tiene el precio más bajo en pesos colombianos ($ COP).

3. **Alertas Hiperpersonalizadas por Umbral**:
   - El usuario define exactamente cuánto está dispuesto a pagar.
   - El servidor monitorea los catálogos periódicamente sin consumir batería ni datos del celular.
   - Notificación push inmediata vía **Firebase Cloud Messaging (FCM)** al tocar el umbral.

4. **Gamificación y Dashboard de Ahorro**:
   - Medidor de dinero total ahorrado en COP.
   - Rangos de usuario: *Explorador Novato*, *Buscador de Gangas*, *Cazador Experto*, *Cazador Legendario*.

5. **Monetización Integrada**:
   - Compatible con enlaces de afiliado de Amazon Associates y Mercado Libre Afiliados para generar comisiones automáticas cuando los usuarios compran desde la alerta.

---

## 📁 Estructura del Proyecto

```text
dealradar/
├── android/                           # Código nativo Android (Jetpack Compose + Material 3)
│   ├── app/
│   │   ├── src/main/
│   │   │   ├── java/com/dealradar/app/
│   │   │   │   ├── MainActivity.kt    # Navegación y ciclo de vida
│   │   │   │   ├── data/api/          # Cliente Retrofit
│   │   │   │   ├── data/model/        # Modelos de datos
│   │   │   │   ├── service/           # Receptor de notificaciones FCM
│   │   │   │   └── ui/screens/        # Pantallas (Feed, Buscar, Alertas, Ahorro)
│   │   │   └── AndroidManifest.xml
│   │   └── build.gradle.kts
│   ├── build.gradle.kts
│   └── settings.gradle.kts
├── backend/                           # Servidor y Workers de Monitoreo
│   ├── app/
│   │   ├── main.py                    # API REST con FastAPI
│   │   ├── database.py                # Modelos SQLAlchemy (SQLite/PostgreSQL)
│   │   ├── scrapers/                  # Extractores de Mercado Libre, Alkosto, Éxito, Amazon
│   │   └── services/                  # Planificador de chequeos y notificaciones push
│   ├── Dockerfile
│   └── requirements.txt
└── .github/workflows/
    ├── build-android.yml              # CI/CD: Compila el APK automáticamente en GitHub
    └── backend-test.yml               # CI/CD: Pruebas del backend
```

---

## 🛠️ Guía Paso a Paso para Joan

### Paso 1: Crear tu Repositorio en GitHub y Subir el Código

1. Entra a tu cuenta en [GitHub](https://github.com/) y haz clic en **New repository**.
2. Nómbralo: `dealradar` (puedes dejarlo público o privado).
3. En tu computador o terminal, descomprime la carpeta del proyecto y ejecuta:
   ```bash
   cd dealradar
   git init
   git add .
   git commit -m "feat: Initial commit DealRadar Android & Backend"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/dealradar.git
   git push -u origin main
   ```

---

### Paso 2: Configurar Firebase (Para Notificaciones Push Gratuitas)

1. Ve a la consola de [Firebase](https://console.firebase.google.com/) y crea un proyecto llamado **DealRadar**.
2. Agrega una aplicación **Android**:
   - Nombre de paquete: `com.dealradar.app`
3. Descarga el archivo `google-services.json` y colócalo dentro de la carpeta:
   `android/app/google-services.json`
4. En Firebase Console, ve a **Configuración del proyecto > Cuentas de servicio**, genera una nueva clave privada en formato JSON y guárdala como `firebase_service_account.json` dentro de `backend/`.

---

### Paso 3: Desplegar el Backend Gratis en Render

1. Crea una cuenta gratuita en [Render](https://render.com/).
2. Haz clic en **New > Web Service** y conecta tu repositorio de GitHub `dealradar`.
3. Configuración del servicio:
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Copia la URL que te genera Render (ej. `https://dealradar-xxx.onrender.com/`).
5. En el archivo `android/app/src/main/java/com/dealradar/app/data/api/DealRadarApi.kt`, coloca esa URL en `var baseUrl`.

---

### Paso 4: Obtener tu APK Listo para Instalar en el Celular

Gracias al flujo de trabajo configurado en `.github/workflows/build-android.yml`:
1. Cada vez que hagas `git push` a tu repositorio en GitHub, se activará la pestaña **Actions**.
2. GitHub compilará el proyecto en la nube y generará el archivo `DealRadar-Debug-APK`.
3. Solo debes entrar a **Actions > Última ejecución > Artifacts**, descargar el archivo `.apk` y pasarlo a tu celular para instalarlo.

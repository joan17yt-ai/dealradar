import urllib.parse
from typing import List, Optional
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.database import get_db, init_db, User, ProductAlert, PriceHistory, FeaturedDeal
from app.scrapers.manager import scraper_manager
from app.services.tracker import check_alerts_job
from app.services.notifications import init_firebase

scheduler = AsyncIOScheduler()

HTML_PAGE = """<!DOCTYPE html>
<html lang="es" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>DealRadar Colombia — Alertas de Ofertas y Comparador de Precios</title>
    <meta name="description" content="Rastreador de precios en tiempo real para Mercado Libre, Alkosto, Éxito y Amazon en Colombia.">
    <meta name="theme-color" content="#0F141C">
    
    <!-- Tailwind CSS CDN & Lucide Icons -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        darkBg: '#0B0F17',
                        darkSurface: '#131B26',
                        darkCard: '#1A2332',
                        radarGreen: '#00E676',
                        radarBlue: '#00B0FF',
                        discountRed: '#FF3B30',
                        starGold: '#FFD60A'
                    }
                }
            }
        }
    </script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
        body { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #0B0F17; color: #FFFFFF; }
        .glass-panel { background: rgba(19, 27, 38, 0.85); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); }
        .pulse-beacon { animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: .5; transform: scale(1.15); } }
        /* Hide scrollbars */
        .no-scrollbar::-webkit-scrollbar { display: none; }
        .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
    </style>
</head>
<body class="min-h-screen pb-20">

    <!-- Barra Superior / Header -->
    <header class="sticky top-0 z-50 glass-panel border-b border-gray-800/80 px-4 py-3">
        <div class="max-w-4xl mx-auto flex items-center justify-between">
            <div class="flex items-center space-x-2.5">
                <div class="relative flex items-center justify-center w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30">
                    <span class="w-2.5 h-2.5 rounded-full bg-radarGreen pulse-beacon"></span>
                </div>
                <div>
                    <h1 class="text-lg font-black tracking-tight flex items-center gap-1.5">
                        DEAL<span class="text-radarGreen">RADAR</span>
                        <span class="text-[10px] font-bold uppercase bg-emerald-500/20 text-radarGreen px-1.5 py-0.5 rounded">Colombia</span>
                    </h1>
                </div>
            </div>

            <div class="flex items-center space-x-2">
                <button onclick="switchTab('savings')" class="flex items-center space-x-1 px-3 py-1.5 rounded-full bg-darkCard border border-gray-700/60 text-xs font-semibold text-gray-300 hover:text-white hover:border-radarGreen transition">
                    <i data-lucide="award" class="w-3.5 h-3.5 text-starGold"></i>
                    <span id="headerSavingsCounter">$0 Ahorro</span>
                </button>
            </div>
        </div>
    </header>

    <!-- Contenedor Principal de Vistas -->
    <main class="max-w-4xl mx-auto px-4 pt-4">

        <!-- ================= VISTA 1: RADAR DE GANGAS (FEED) ================= -->
        <section id="view-feed" class="space-y-4">
            <!-- Banner Hero -->
            <div class="relative overflow-hidden rounded-2xl p-5 border border-emerald-500/20 bg-gradient-to-r from-emerald-950/40 via-darkCard to-blue-950/30">
                <div class="relative z-10 space-y-1">
                    <span class="inline-flex items-center gap-1 px-2 py-0.5 text-[11px] font-bold rounded-full bg-emerald-500/20 text-radarGreen">
                        <i data-lucide="flame" class="w-3 h-3"></i> Ofertón del Día
                    </span>
                    <h2 class="text-xl font-extrabold text-white">Monitoreo de Precios en Vivo</h2>
                    <p class="text-xs text-gray-400">Rastreamos Mercado Libre, Alkosto, Éxito y Amazon para avisarte de gangas reales.</p>
                </div>
                <div class="absolute -right-6 -bottom-6 w-32 h-32 rounded-full bg-radarGreen/10 blur-2xl pointer-events-none"></div>
            </div>

            <!-- Selector de Categorías -->
            <div class="flex space-x-2 overflow-x-auto no-scrollbar py-1 text-xs">
                <button onclick="filterCategory('Todos')" class="cat-pill active-pill whitespace-nowrap px-4 py-2 rounded-xl font-semibold bg-radarGreen text-darkBg transition">Todos</button>
                <button onclick="filterCategory('Celulares')" class="cat-pill whitespace-nowrap px-4 py-2 rounded-xl font-medium bg-darkCard text-gray-300 hover:text-white border border-gray-800 transition">Celulares</button>
                <button onclick="filterCategory('Computadores')" class="cat-pill whitespace-nowrap px-4 py-2 rounded-xl font-medium bg-darkCard text-gray-300 hover:text-white border border-gray-800 transition">Computadores</button>
                <button onclick="filterCategory('Neveras')" class="cat-pill whitespace-nowrap px-4 py-2 rounded-xl font-medium bg-darkCard text-gray-300 hover:text-white border border-gray-800 transition">Neveras</button>
                <button onclick="filterCategory('Parlantes')" class="cat-pill whitespace-nowrap px-4 py-2 rounded-xl font-medium bg-darkCard text-gray-300 hover:text-white border border-gray-800 transition">Parlantes & Audio</button>
            </div>

            <!-- Lista de Ofertas Destacadas -->
            <div id="feedList" class="space-y-3">
                <div class="text-center py-10 text-gray-500 text-sm">Cargando las mejores gangas de Colombia...</div>
            </div>
        </section>

        <!-- ================= VISTA 2: BUSCADOR MULTITIENDA ================= -->
        <section id="view-search" class="space-y-4 hidden">
            <div class="space-y-1">
                <h2 class="text-lg font-bold text-white flex items-center gap-2">
                    <i data-lucide="search" class="w-5 h-5 text-radarGreen"></i> Buscador Multitienda
                </h2>
                <p class="text-xs text-gray-400">Escribe cualquier producto (ej. <span class="text-emerald-400 font-medium">impresoras, iPhone 14, televisor</span>) para comparar precios en Colombia.</p>
            </div>

            <!-- Formulario de búsqueda -->
            <form onsubmit="handleSearch(event)" class="relative">
                <input id="searchInput" type="text" placeholder="¿Qué producto buscas?" 
                    class="w-full pl-11 pr-24 py-3.5 rounded-xl bg-darkSurface border border-gray-700/70 text-sm text-white focus:outline-none focus:border-radarGreen transition shadow-inner">
                <i data-lucide="search" class="w-5 h-5 absolute left-3.5 top-3.5 text-gray-400"></i>
                <button type="submit" class="absolute right-2 top-2 px-4 py-1.5 rounded-lg bg-radarGreen text-darkBg font-bold text-xs hover:bg-emerald-400 transition shadow">
                    Buscar
                </button>
            </form>

            <!-- Loading de búsqueda -->
            <div id="searchLoading" class="hidden text-center py-10 space-y-2">
                <div class="inline-block w-8 h-8 border-3 border-radarGreen border-t-transparent rounded-full animate-spin"></div>
                <p class="text-xs text-gray-400">Consultando catálogos de Mercado Libre, Alkosto, Éxito y Amazon...</p>
            </div>

            <!-- Resultados de Búsqueda -->
            <div id="searchResults" class="space-y-3"></div>
        </section>

        <!-- ================= VISTA 3: MIS ALERTAS ACTIVAS ================= -->
        <section id="view-alerts" class="space-y-4 hidden">
            <div class="flex items-center justify-between">
                <div>
                    <h2 class="text-lg font-bold text-white flex items-center gap-2">
                        <i data-lucide="bell-ring" class="w-5 h-5 text-radarGreen"></i> Mis Alertas Vigiladas
                    </h2>
                    <p class="text-xs text-gray-400" id="alertsCountText">0 productos bajo vigilancia</p>
                </div>
                <button onclick="switchTab('search')" class="px-3 py-1.5 rounded-lg bg-emerald-500/20 text-radarGreen text-xs font-semibold hover:bg-emerald-500/30 transition">
                    + Nueva Alerta
                </button>
            </div>

            <div id="userAlertsList" class="space-y-3">
                <div class="text-center py-12 text-gray-500 text-sm">No tienes alertas creadas aún. Busca un producto para vigilarlo.</div>
            </div>
        </section>

        <!-- ================= VISTA 4: DASHBOARD DE AHORRO ================= -->
        <section id="view-savings" class="space-y-4 hidden">
            <div class="rounded-2xl p-6 border border-emerald-500/20 bg-darkSurface text-center space-y-3">
                <div class="inline-flex p-3 rounded-full bg-emerald-500/10 text-radarGreen">
                    <i data-lucide="piggy-bank" class="w-8 h-8"></i>
                </div>
                <div>
                    <span class="text-xs text-gray-400 uppercase tracking-wider font-semibold">Tu Ahorro Potencial Acumulado</span>
                    <h2 id="totalSavedDisplay" class="text-3xl font-black text-white mt-0.5">$0 COP</h2>
                </div>
                <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-darkCard border border-gray-700 text-xs font-semibold text-starGold">
                    <i data-lucide="shield-check" class="w-4 h-4"></i> Rango: <span id="userRankText">Cazador Activo</span>
                </div>
            </div>

            <div class="space-y-2">
                <h3 class="text-xs font-bold uppercase tracking-wider text-gray-400 px-1">Consejos para comprar en Colombia</h3>
                <div class="p-3.5 rounded-xl bg-darkCard border border-gray-800/80 text-xs text-gray-300 space-y-1">
                    <p class="font-bold text-white flex items-center gap-1.5">
                        <i data-lucide="check-circle" class="w-3.5 h-3.5 text-radarGreen"></i> Envíos gratis de Amazon a Colombia
                    </p>
                    <p class="text-gray-400">Recuerda que pedidos calificados de más de $35 USD en Amazon cuentan con envío gratuito directo hasta tu puerta en Colombia.</p>
                </div>
                <div class="p-3.5 rounded-xl bg-darkCard border border-gray-800/80 text-xs text-gray-300 space-y-1">
                    <p class="font-bold text-white flex items-center gap-1.5">
                        <i data-lucide="check-circle" class="w-3.5 h-3.5 text-radarGreen"></i> Días sin IVA y CyberLunes
                    </p>
                    <p class="text-gray-400">Verifica siempre el precio base semanas antes; con DealRadar evitas promociones con descuentos inflados artificialmente.</p>
                </div>
            </div>
        </section>

    </main>

    <!-- Modal para Configurar Alerta -->
    <div id="alertModal" class="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm hidden flex items-center justify-center p-4">
        <div class="glass-panel w-full max-w-sm rounded-2xl p-5 border border-gray-700 space-y-4">
            <div class="flex items-center justify-between">
                <h3 class="text-sm font-bold text-white flex items-center gap-1.5">
                    <i data-lucide="bell-plus" class="w-4 h-4 text-radarGreen"></i> Activar Alerta de Precio
                </h3>
                <button onclick="closeAlertModal()" class="text-gray-400 hover:text-white">
                    <i data-lucide="x" class="w-4 h-4"></i>
                </button>
            </div>
            <div>
                <p id="modalProductTitle" class="text-xs text-gray-300 font-semibold line-clamp-2"></p>
                <p id="modalCurrentPrice" class="text-xs text-radarGreen font-bold mt-1"></p>
            </div>
            <div class="space-y-1.5">
                <label class="text-xs text-gray-400 font-medium">¿A qué precio deseas que te avisemos? (COP):</label>
                <input id="modalTargetPrice" type="number" class="w-full px-3 py-2 rounded-lg bg-darkBg border border-gray-700 text-sm text-white focus:outline-none focus:border-radarGreen">
            </div>
            <div class="flex justify-end gap-2 pt-2">
                <button onclick="closeAlertModal()" class="px-3.5 py-1.5 rounded-lg text-xs font-semibold text-gray-400 hover:text-white">Cancelar</button>
                <button onclick="submitNewAlert()" class="px-4 py-1.5 rounded-lg bg-radarGreen text-darkBg text-xs font-bold hover:bg-emerald-400 transition shadow">Guardar Alerta</button>
            </div>
        </div>
    </div>

    <!-- Barra de Navegación Inferior Móvil (Estilo App Nativa) -->
    <nav class="fixed bottom-0 left-0 right-0 z-40 glass-panel border-t border-gray-800/80 px-2 py-2">
        <div class="max-w-md mx-auto grid grid-cols-4 gap-1 text-center">
            <button onclick="switchTab('feed')" id="nav-feed" class="nav-btn flex flex-col items-center py-1 text-radarGreen">
                <i data-lucide="radar" class="w-5 h-5"></i>
                <span class="text-[10px] font-semibold mt-0.5">Radar</span>
            </button>
            <button onclick="switchTab('search')" id="nav-search" class="nav-btn flex flex-col items-center py-1 text-gray-400 hover:text-gray-200">
                <i data-lucide="search" class="w-5 h-5"></i>
                <span class="text-[10px] font-semibold mt-0.5">Buscar</span>
            </button>
            <button onclick="switchTab('alerts')" id="nav-alerts" class="nav-btn flex flex-col items-center py-1 text-gray-400 hover:text-gray-200">
                <i data-lucide="bell" class="w-5 h-5"></i>
                <span class="text-[10px] font-semibold mt-0.5">Mis Alertas</span>
            </button>
            <button onclick="switchTab('savings')" id="nav-savings" class="nav-btn flex flex-col items-center py-1 text-gray-400 hover:text-gray-200">
                <i data-lucide="trophy" class="w-5 h-5"></i>
                <span class="text-[10px] font-semibold mt-0.5">Mi Ahorro</span>
            </button>
        </div>
    </nav>

    <!-- Lógica de la Aplicación en JavaScript -->
    <script>
        // Manejador de ID único de dispositivo en LocalStorage
        let deviceId = localStorage.getItem('dealradar_device_id');
        if (!deviceId) {
            deviceId = 'web_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('dealradar_device_id', deviceId);
        }

        const copFormatter = new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            maximumFractionDigits: 0
        });

        let currentActiveItem = null;

        // Inicializar iconos
        function refreshIcons() {
            lucide.createIcons();
        }

        // Navegación entre vistas
        function switchTab(tabName) {
            ['feed', 'search', 'alerts', 'savings'].forEach(tab => {
                document.getElementById(`view-${tab}`).classList.add('hidden');
                const nav = document.getElementById(`nav-${tab}`);
                nav.classList.remove('text-radarGreen');
                nav.classList.add('text-gray-400');
            });

            document.getElementById(`view-${tabName}`).classList.remove('hidden');
            const activeNav = document.getElementById(`nav-${tabName}`);
            activeNav.classList.remove('text-gray-400');
            activeNav.classList.add('text-radarGreen');

            if (tabName === 'alerts') loadUserAlerts();
            if (tabName === 'savings') loadUserSavings();
            refreshIcons();
        }

        // Cargar ofertas destacadas
        async function loadFeedDeals(category = null) {
            const feedList = document.getElementById('feedList');
            feedList.innerHTML = `<div class="text-center py-10 text-gray-500 text-xs">Actualizando gangas en vivo...</div>`;
            try {
                const url = category && category !== 'Todos' ? `/api/deals/feed?category=${encodeURIComponent(category)}` : '/api/deals/feed';
                const res = await fetch(url);
                const data = await res.json();
                renderFeed(data.deals || []);
            } catch (err) {
                feedList.innerHTML = `<div class="text-center py-8 text-red-400 text-xs">Error cargando ofertas. Revisa tu conexión.</div>`;
            }
        }

        function filterCategory(cat) {
            document.querySelectorAll('.cat-pill').forEach(pill => {
                pill.classList.remove('bg-radarGreen', 'text-darkBg', 'font-semibold');
                pill.classList.add('bg-darkCard', 'text-gray-300', 'font-medium');
                if (pill.innerText.trim() === cat) {
                    pill.classList.remove('bg-darkCard', 'text-gray-300', 'font-medium');
                    pill.classList.add('bg-radarGreen', 'text-darkBg', 'font-semibold');
                }
            });
            loadFeedDeals(cat);
        }

        function getStoreBadgeColor(store) {
            switch(store) {
                case 'Mercado Libre': return 'bg-amber-400/20 text-amber-300 border-amber-500/30';
                case 'Alkosto': return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
                case 'Éxito': return 'bg-yellow-400/20 text-yellow-300 border-yellow-500/30';
                case 'Amazon': return 'bg-sky-500/20 text-sky-400 border-sky-500/30';
                default: return 'bg-gray-700 text-gray-300 border-gray-600';
            }
        }

        function renderFeed(deals) {
            const feedList = document.getElementById('feedList');
            if (!deals.length) {
                feedList.innerHTML = `<div class="text-center py-8 text-gray-500 text-xs">No hay ofertas en esta categoría ahora.</div>`;
                return;
            }

            feedList.innerHTML = deals.map(deal => `
                <div class="glass-panel rounded-2xl p-4 transition hover:border-gray-700 space-y-3">
                    <div class="flex items-center justify-between">
                        <span class="text-[11px] font-bold px-2 py-0.5 rounded-md border ${getStoreBadgeColor(deal.store)}">
                            ${deal.store}
                        </span>
                        <span class="text-[11px] font-black px-2 py-0.5 rounded-md bg-discountRed/90 text-white">
                            -${deal.discount_percentage}% OFF
                        </span>
                    </div>

                    <div class="flex gap-3.5 items-center">
                        ${deal.image_url ? `
                            <img src="${deal.image_url}" alt="${deal.title}" class="w-18 h-18 w-20 h-20 object-contain rounded-xl bg-white p-1.5 flex-shrink-0">
                        ` : ''}
                        <div class="min-w-0 flex-1">
                            <h3 class="text-sm font-semibold text-white line-clamp-2">${deal.title}</h3>
                            <div class="mt-1 flex items-baseline gap-2">
                                <span class="text-base font-extrabold text-radarGreen">${copFormatter.format(deal.current_price_cop)}</span>
                                ${deal.original_price_cop > deal.current_price_cop ? `
                                    <span class="text-xs text-gray-500 line-through">${copFormatter.format(deal.original_price_cop)}</span>
                                ` : ''}
                            </div>
                        </div>
                    </div>

                    <div class="grid grid-cols-2 gap-2 pt-1">
                        <button onclick='openAlertModal(${JSON.stringify(deal)})' class="flex items-center justify-center gap-1.5 py-2 rounded-xl bg-darkCard border border-gray-700/80 text-xs font-semibold text-gray-300 hover:text-white hover:border-radarGreen transition">
                            <i data-lucide="bell" class="w-3.5 h-3.5 text-radarGreen"></i> Vigilar
                        </button>
                        <a href="${deal.product_url}" target="_blank" rel="noopener noreferrer" class="flex items-center justify-center gap-1.5 py-2 rounded-xl bg-radarGreen text-darkBg text-xs font-bold hover:bg-emerald-400 transition shadow">
                            <i data-lucide="external-link" class="w-3.5 h-3.5"></i> Ver Oferta
                        </a>
                    </div>
                </div>
            `).join('');
            refreshIcons();
        }

        // Búsqueda Multitienda
        async function handleSearch(e) {
            e.preventDefault();
            const query = document.getElementById('searchInput').value.trim();
            if (!query) return;

            const loading = document.getElementById('searchLoading');
            const results = document.getElementById('searchResults');
            loading.classList.remove('hidden');
            results.innerHTML = '';

            try {
                const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
                const data = await res.json();
                renderSearchResults(data.results || [], query);
            } catch (err) {
                results.innerHTML = `<div class="text-center py-6 text-red-400 text-xs">Error al buscar. Intenta de nuevo.</div>`;
            } finally {
                loading.classList.add('hidden');
            }
        }

        function renderSearchResults(items, query) {
            const container = document.getElementById('searchResults');
            if (!items.length) {
                container.innerHTML = `<div class="text-center py-8 text-gray-400 text-xs">No se encontraron productos para "${query}".</div>`;
                return;
            }

            container.innerHTML = items.map(item => `
                <div class="glass-panel rounded-xl p-3.5 flex items-center justify-between gap-3">
                    ${item.image_url ? `
                        <img src="${item.image_url}" alt="${item.title}" class="w-14 h-14 object-contain rounded-lg bg-white p-1 flex-shrink-0">
                    ` : ''}
                    <div class="min-w-0 flex-1">
                        <span class="text-[10px] font-bold text-radarGreen uppercase">${item.store}</span>
                        <h4 class="text-xs font-medium text-white line-clamp-1">${item.title}</h4>
                        <p class="text-xs font-bold text-white mt-0.5">
                            ${item.price_cop > 0 ? copFormatter.format(item.price_cop) : 'Ver en Tienda'}
                        </p>
                    </div>
                    <div class="flex items-center gap-1.5 flex-shrink-0">
                        <button onclick='openAlertModal(${JSON.stringify(item)})' class="p-2 rounded-lg bg-darkCard border border-gray-700 text-gray-300 hover:text-radarGreen transition" title="Crear Alerta">
                            <i data-lucide="bell-plus" class="w-4 h-4"></i>
                        </button>
                        <a href="${item.product_url}" target="_blank" rel="noopener noreferrer" class="p-2 rounded-lg bg-radarGreen text-darkBg font-bold transition hover:bg-emerald-400" title="Ver Oferta">
                            <i data-lucide="external-link" class="w-4 h-4"></i>
                        </a>
                    </div>
                </div>
            `).join('');
            refreshIcons();
        }

        // Modal de Alertas
        function openAlertModal(item) {
            currentActiveItem = item;
            document.getElementById('modalProductTitle').innerText = item.title;
            const currentPrice = item.price_cop || item.current_price_cop || 0;
            document.getElementById('modalCurrentPrice').innerText = currentPrice > 0 ? `Precio actual: ${copFormatter.format(currentPrice)} en ${item.store}` : `Tienda: ${item.store}`;
            document.getElementById('modalTargetPrice').value = currentPrice > 0 ? Math.round(currentPrice * 0.90) : 500000;
            document.getElementById('alertModal').classList.remove('hidden');
            refreshIcons();
        }

        function closeAlertModal() {
            document.getElementById('alertModal').classList.add('hidden');
            currentActiveItem = null;
        }

        async function submitNewAlert() {
            if (!currentActiveItem) return;
            const targetPrice = parseFloat(document.getElementById('modalTargetPrice').value);
            if (!targetPrice || targetPrice <= 0) return alert('Por favor ingresa un precio válido en pesos colombianos.');

            try {
                const res = await fetch('/api/alerts', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        device_id: deviceId,
                        product_title: currentActiveItem.title,
                        query_keyword: currentActiveItem.title.substring(0, 50),
                        target_price_cop: targetPrice,
                        current_best_price_cop: currentActiveItem.price_cop || currentActiveItem.current_price_cop || targetPrice,
                        best_store: currentActiveItem.store,
                        product_url: currentActiveItem.product_url,
                        image_url: currentActiveItem.image_url
                    })
                });
                if (res.ok) {
                    alert('¡Alerta activada con éxito! Te avisaremos cuando el precio baje.');
                    closeAlertModal();
                    loadUserAlerts();
                }
            } catch (err) {
                alert('No se pudo guardar la alerta.');
            }
        }

        async function loadUserAlerts() {
            const container = document.getElementById('userAlertsList');
            try {
                const res = await fetch(`/api/alerts?device_id=${encodeURIComponent(deviceId)}`);
                const data = await res.json();
                const alerts = data.alerts || [];
                document.getElementById('alertsCountText').innerText = `${alerts.length} producto${alerts.length === 1 ? '' : 's'} bajo vigilancia`;
                
                if (!alerts.length) {
                    container.innerHTML = `<div class="text-center py-12 text-gray-500 text-xs">No tienes alertas activas. Crea una desde el Buscador o el Radar.</div>`;
                    return;
                }

                container.innerHTML = alerts.map(a => `
                    <div class="glass-panel rounded-xl p-3.5 space-y-2">
                        <div class="flex items-center justify-between">
                            <span class="text-[10px] font-bold text-radarGreen uppercase">VIGILANDO EN ${a.best_store || 'COLOMBIA'}</span>
                            <button onclick="deleteAlert(${a.id})" class="text-red-400 hover:text-red-300 text-xs">
                                <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                            </button>
                        </div>
                        <h4 class="text-xs font-semibold text-white line-clamp-1">${a.product_title}</h4>
                        <div class="flex justify-between text-xs pt-1 border-t border-gray-800">
                            <span class="text-gray-400">Objetivo: <strong class="text-radarGreen">${copFormatter.format(a.target_price_cop)}</strong></span>
                            <a href="${a.product_url}" target="_blank" class="text-sky-400 hover:underline flex items-center gap-1">Ver en tienda <i data-lucide="external-link" class="w-3 h-3"></i></a>
                        </div>
                    </div>
                `).join('');
                refreshIcons();
            } catch (err) {
                container.innerHTML = `<div class="text-center py-6 text-red-400 text-xs">Error cargando alertas.</div>`;
            }
        }

        async function deleteAlert(id) {
            if (!confirm('¿Deseas eliminar esta alerta de precio?')) return;
            try {
                await fetch(`/api/alerts/${id}`, { method: 'DELETE' });
                loadUserAlerts();
            } catch (err) {
                alert('Error al borrar alerta');
            }
        }

        async function loadUserSavings() {
            try {
                const res = await fetch(`/api/user/savings?device_id=${encodeURIComponent(deviceId)}`);
                const data = await res.json();
                document.getElementById('totalSavedDisplay').innerText = copFormatter.format(data.total_saved_cop || 0);
                document.getElementById('headerSavingsCounter').innerText = `${copFormatter.format(data.total_saved_cop || 0)} Ahorro`;
                document.getElementById('userRankText').innerText = data.rank || 'Cazador Activo';
            } catch (err) {}
        }

        // Carga inicial
        loadFeedDeals();
        loadUserSavings();
        refreshIcons();
    </script>
</body>
</html>
"""

def seed_initial_deals(db: Session):
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
            product_url="https://www.exito.com/s?q=nevera+haceb+311",
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

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    return HTMLResponse(content=HTML_PAGE)

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

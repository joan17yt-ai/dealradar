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
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DealRadar Colombia — El Comparador de Gangas #1</title>
    <!-- Google Fonts & Tailwind CSS & Lucide Icons -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    fontFamily: { sans: ['Outfit', 'sans-serif'] },
                    colors: {
                        brandDark: '#0A0E17',
                        brandSurface: '#121826',
                        brandCard: '#182234',
                        brandCardHover: '#1E2B42',
                        brandAccent: '#00F076',
                        brandAccentDark: '#00B859',
                        brandGold: '#FFB800',
                        brandRed: '#FF334B',
                        brandBlue: '#00A3FF'
                    }
                }
            }
        }
    </script>
    <style>
        body { background-color: #0A0E17; color: #FFFFFF; font-family: 'Outfit', sans-serif; overflow-x: hidden; }
        .glow-effect { box-shadow: 0 0 35px -5px rgba(0, 240, 118, 0.25); }
        .glow-red { box-shadow: 0 0 25px -5px rgba(255, 51, 75, 0.35); }
        .product-card { transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1); }
        .product-card:hover { transform: translateY(-4px); border-color: rgba(0, 240, 118, 0.4); box-shadow: 0 12px 30px -10px rgba(0,0,0,0.8); }
        .banner-gradient { background: linear-gradient(135deg, #0d1e38 0%, #112d1b 50%, #0d1e38 100%); }
    </style>
</head>
<body class="min-h-screen flex flex-col antialiased">

    <!-- Top Announcement Bar -->
    <div class="bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-700 text-dark font-extrabold text-xs text-center py-2 px-4 flex items-center justify-center gap-2 tracking-wide text-black">
        <i data-lucide="zap" class="w-4 h-4 fill-current"></i>
        <span>¡RADAR DE PRECIOS ACTIVADO! MONITOREAMOS MERCADO LIBRE, ALKOSTO, ÉXITO Y AMAZON LAS 24 HORAS</span>
        <span class="hidden md:inline-block bg-black/20 text-white px-2 py-0.5 rounded-full text-[10px] font-bold">100% GRATIS</span>
    </div>

    <!-- Header Principal -->
    <header class="sticky top-0 z-50 bg-brandDark/95 backdrop-blur-md border-b border-gray-800/80 px-4 lg:px-8 py-3.5">
        <div class="max-w-7xl mx-auto flex items-center justify-between gap-4">
            
            <!-- Logo -->
            <a href="/" class="flex items-center gap-2.5 group">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-brandAccent to-emerald-600 flex items-center justify-center text-brandDark font-black text-xl shadow-lg shadow-emerald-500/20 group-hover:scale-105 transition">
                    <i data-lucide="radar" class="w-6 h-6 stroke-[2.5]"></i>
                </div>
                <div>
                    <span class="text-2xl font-black tracking-tight text-white flex items-center gap-1">
                        DEAL<span class="text-brandAccent">RADAR</span>
                    </span>
                    <span class="text-[10px] font-bold uppercase tracking-widest text-emerald-400 block -mt-1">Colombia Oficial</span>
                </div>
            </a>

            <!-- Barra de Búsqueda Centrada -->
            <div class="flex-1 max-w-2xl mx-4 hidden md:block">
                <form onsubmit="handleGlobalSearch(event)" class="relative flex items-center">
                    <input id="desktopSearchInput" type="text" placeholder="Busca un celular, computador, nevera o producto exacto..." 
                        class="w-full bg-brandSurface border border-gray-700/80 rounded-full py-2.5 pl-11 pr-28 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-brandAccent focus:ring-1 focus:ring-brandAccent transition">
                    <i data-lucide="search" class="w-4 h-4 text-gray-400 absolute left-4 pointer-events-none"></i>
                    <button type="submit" class="absolute right-1.5 px-4 py-1.5 rounded-full bg-brandAccent text-brandDark font-extrabold text-xs hover:bg-emerald-400 transition shadow">
                        Comparar
                    </button>
                </form>
            </div>

            <!-- Botones de Acción -->
            <div class="flex items-center gap-3">
                <a href="#buscador" onclick="document.getElementById('mobileSearchInput').focus()" class="md:hidden p-2 rounded-xl bg-brandSurface text-gray-300">
                    <i data-lucide="search" class="w-5 h-5"></i>
                </a>
                <button onclick="scrollToDeals()" class="flex items-center gap-1.5 px-4 py-2 rounded-full bg-brandAccent/10 border border-brandAccent/30 text-brandAccent text-xs font-bold hover:bg-brandAccent hover:text-brandDark transition">
                    <i data-lucide="flame" class="w-4 h-4 fill-current"></i>
                    <span>Súper Ofertas</span>
                </button>
            </div>
        </div>

        <!-- Búsqueda en Móvil -->
        <div class="mt-2.5 md:hidden">
            <form onsubmit="handleGlobalSearch(event)" class="relative flex items-center">
                <input id="mobileSearchInput" type="text" placeholder="Escribe un producto (ej. Portátil, iPhone, Nevera)..." 
                    class="w-full bg-brandSurface border border-gray-700 rounded-full py-2.5 pl-10 pr-24 text-xs text-white placeholder-gray-400 focus:outline-none focus:border-brandAccent">
                <i data-lucide="search" class="w-4 h-4 text-gray-400 absolute left-3.5 pointer-events-none"></i>
                <button type="submit" class="absolute right-1 px-3 py-1 rounded-full bg-brandAccent text-brandDark font-bold text-xs">
                    Buscar
                </button>
            </form>
        </div>
    </header>

    <!-- Contenido Principal -->
    <main class="flex-1 max-w-7xl mx-auto w-full px-4 lg:px-8 py-6 space-y-10">

        <!-- ================= HERO BANNER PRINCIPAL ================= -->
        <div class="banner-gradient rounded-3xl p-6 lg:p-10 border border-emerald-500/30 relative overflow-hidden glow-effect">
            <div class="max-w-2xl relative z-10 space-y-4">
                <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brandRed/20 border border-brandRed/40 text-brandRed font-black text-xs uppercase tracking-wider animate-pulse">
                    <i data-lucide="zap" class="w-3.5 h-3.5 fill-current"></i> Gangas del Día en Colombia
                </div>
                <h1 class="text-3xl lg:text-5xl font-black text-white leading-tight tracking-tight">
                    Encuentra siempre el <span class="text-brandAccent underline decoration-brandAccent/40 decoration-4">precio más barato</span> garantizado.
                </h1>
                <p class="text-sm lg:text-base text-gray-300 font-normal leading-relaxed">
                    Comparamos las tiendas oficiales en vivo. Al hacer clic en cualquier oferta te llevamos <strong class="text-white">directamente al producto exacto</strong> para que compres al menor precio antes de que se agote.
                </p>
                <div class="flex flex-wrap items-center gap-3 pt-2">
                    <span class="text-xs text-gray-400 font-semibold flex items-center gap-1.5 bg-black/30 px-3 py-1.5 rounded-lg border border-gray-700">
                        <i data-lucide="shield-check" class="w-4 h-4 text-brandAccent"></i> Enlaces directos a tiendas oficiales
                    </span>
                    <span class="text-xs text-gray-400 font-semibold flex items-center gap-1.5 bg-black/30 px-3 py-1.5 rounded-lg border border-gray-700">
                        <i data-lucide="check" class="w-4 h-4 text-brandAccent"></i> Ordenado de menor a mayor precio
                    </span>
                </div>
            </div>

            <!-- Decoración visual del banner -->
            <div class="absolute right-0 bottom-0 top-0 w-1/3 hidden lg:flex items-center justify-center opacity-40 pointer-events-none">
                <i data-lucide="trending-down" class="w-64 h-64 text-brandAccent/30 stroke-[1]"></i>
            </div>
        </div>

        <!-- ================= SECCIÓN DE COMPARACIÓN INTELIGENTE (CUANDO EL USUARIO BUSCA) ================= -->
        <section id="comparadorSection" class="hidden space-y-6">
            <div class="bg-brandSurface border-2 border-brandAccent/50 rounded-2xl p-5 lg:p-7 space-y-4 glow-effect">
                <div class="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-gray-800 pb-4">
                    <div>
                        <span class="text-xs font-bold uppercase tracking-wider text-brandAccent flex items-center gap-1.5">
                            <i data-lucide="check-circle-2" class="w-4 h-4"></i> Comparativa Realizada con Éxito
                        </span>
                        <h2 id="comparadorQueryTitle" class="text-2xl font-black text-white mt-1">Resultados para tu búsqueda</h2>
                    </div>
                    <div id="cheapestBanner" class="bg-brandAccent text-brandDark px-4 py-2 rounded-xl font-black text-sm flex items-center gap-2 shadow-lg shadow-emerald-500/20">
                        <i data-lucide="trophy" class="w-5 h-5 fill-current"></i>
                        <span id="cheapestStoreText">El más barato está en: Cargando...</span>
                    </div>
                </div>

                <div class="text-xs text-gray-400 flex items-center gap-2">
                    <i data-lucide="arrow-down-narrow-wide" class="w-4 h-4 text-brandAccent"></i>
                    <span>Listado ordenado estrictamente <strong class="text-white">desde el más económico</strong> hasta el más costoso:</span>
                </div>

                <!-- Grilla de Tiendas Comparadas -->
                <div id="comparadorResultsGrid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    <!-- Dinámico con JS -->
                </div>
            </div>
        </section>

        <!-- ================= CATEGORÍAS RÁPIDAS ================= -->
        <div class="space-y-3">
            <div class="flex items-center justify-between">
                <h3 class="text-sm font-bold uppercase tracking-wider text-gray-400">Filtrar Gangas por Categoría</h3>
                <span class="text-xs text-brandAccent font-semibold">Precios en Pesos Colombianos (COP)</span>
            </div>
            <div class="flex gap-2 overflow-x-auto pb-2 no-scrollbar text-xs font-bold">
                <button onclick="filterCategory('Todos')" class="cat-btn active-cat px-5 py-2.5 rounded-xl bg-brandAccent text-brandDark shadow-md shadow-emerald-500/20 transition flex items-center gap-1.5">
                    <i data-lucide="layout-grid" class="w-4 h-4"></i> Todos los Productos
                </button>
                <button onclick="filterCategory('Celulares')" class="cat-btn px-5 py-2.5 rounded-xl bg-brandSurface hover:bg-brandCard text-gray-300 hover:text-white border border-gray-800 transition flex items-center gap-1.5">
                    <i data-lucide="smartphone" class="w-4 h-4"></i> Celulares & Smartphones
                </button>
                <button onclick="filterCategory('Computadores')" class="cat-btn px-5 py-2.5 rounded-xl bg-brandSurface hover:bg-brandCard text-gray-300 hover:text-white border border-gray-800 transition flex items-center gap-1.5">
                    <i data-lucide="laptop" class="w-4 h-4"></i> Computadores & Laptops
                </button>
                <button onclick="filterCategory('Neveras')" class="cat-btn px-5 py-2.5 rounded-xl bg-brandSurface hover:bg-brandCard text-gray-300 hover:text-white border border-gray-800 transition flex items-center gap-1.5">
                    <i data-lucide="refrigerator" class="w-4 h-4"></i> Neveras & Hogar
                </button>
                <button onclick="filterCategory('Parlantes')" class="cat-btn px-5 py-2.5 rounded-xl bg-brandSurface hover:bg-brandCard text-gray-300 hover:text-white border border-gray-800 transition flex items-center gap-1.5">
                    <i data-lucide="speaker" class="w-4 h-4"></i> Parlantes & Audio
                </button>
            </div>
        </div>

        <!-- ================= CATÁLOGO DE SÚPER OFERTAS (COLUMNAS / GRID) ================= -->
        <section id="catalogoSection" class="space-y-4">
            <div class="flex items-center justify-between border-b border-gray-800 pb-3">
                <div class="flex items-center gap-2">
                    <i data-lucide="flame" class="w-5 h-5 text-brandRed fill-current"></i>
                    <h2 class="text-xl font-extrabold text-white">Súper Ofertas Verificadas</h2>
                </div>
                <span id="dealsCountBadge" class="text-xs font-bold text-gray-400 bg-brandSurface px-3 py-1 rounded-full border border-gray-800">
                    6 ofertas disponibles
                </span>
            </div>

            <!-- Grilla Principal de Productos (1 columna en móvil, 2 en tablet, 3-4 en PC) -->
            <div id="productsGrid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
                <!-- Se llena dinámicamente con JavaScript con fotos reales y enlaces directos -->
            </div>
        </section>

        <!-- ================= BANNER INFORMATIVO: CÓMO AHORRAR ================= -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 pt-6">
            <div class="bg-brandSurface border border-gray-800 p-5 rounded-2xl flex items-start gap-3.5">
                <div class="p-2.5 rounded-xl bg-emerald-500/10 text-brandAccent flex-shrink-0">
                    <i data-lucide="badge-dollar-sign" class="w-6 h-6"></i>
                </div>
                <div>
                    <h4 class="text-sm font-bold text-white">Siempre lo Más Barato</h4>
                    <p class="text-xs text-gray-400 mt-1">El algoritmo organiza automáticamente las opciones de menor a mayor precio para que nunca pagues de más.</p>
                </div>
            </div>

            <div class="bg-brandSurface border border-gray-800 p-5 rounded-2xl flex items-start gap-3.5">
                <div class="p-2.5 rounded-xl bg-blue-500/10 text-brandBlue flex-shrink-0">
                    <i data-lucide="external-link" class="w-6 h-6"></i>
                </div>
                <div>
                    <h4 class="text-sm font-bold text-white">Directo al Producto</h4>
                    <p class="text-xs text-gray-400 mt-1">No te enviamos a buscadores confusos. El botón abre la ficha exacta del producto en la tienda oficial.</p>
                </div>
            </div>

            <div class="bg-brandSurface border border-gray-800 p-5 rounded-2xl flex items-start gap-3.5">
                <div class="p-2.5 rounded-xl bg-amber-500/10 text-brandGold flex-shrink-0">
                    <i data-lucide="shield-check" class="w-6 h-6"></i>
                </div>
                <div>
                    <h4 class="text-sm font-bold text-white">Tiendas 100% Oficiales</h4>
                    <p class="text-xs text-gray-400 mt-1">Sólo enlazamos Mercado Libre Colombia, Alkosto, Éxito y Amazon con garantía de compra segura.</p>
                </div>
            </div>
        </div>

    </main>

    <!-- Footer -->
    <footer class="bg-brandSurface border-t border-gray-800/80 py-8 px-4 text-center text-xs text-gray-400 mt-16 space-y-2">
        <p class="font-bold text-white">DealRadar Colombia — El motor de ahorro para compras inteligentes</p>
        <p>Monitoreamos ofertas en vivo para que los compradores en Colombia encuentren siempre el precio más bajo.</p>
    </footer>

    <!-- LÓGICA JAVASCRIPT -->
    <script>
        const copFormatter = new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            maximumFractionDigits: 0
        });

        // 1. Catálogo de Súper Ofertas con enlaces directos y fotos de alta calidad
        const verifiedDeals = [
            {
                id: 1,
                title: "Apple iPhone 15 128GB Negro (Nuevo Original)",
                store: "Mercado Libre",
                category: "Celulares",
                current_price_cop: 3499000,
                original_price_cop: 4299000,
                discount_percentage: 19,
                badge: "🔥 MEJOR PRECIO COLOMBIA",
                // Enlace DIRECTO al producto real
                product_url: "https://articulo.mercadolibre.com.co/MCO-1342244819-apple-iphone-15-a3090-6gb-128gb-1-nano-sim-1-esim-_JM",
                image_url: "https://http2.mlstatic.com/D_NQ_NP_893049-MLA71782867320_092023-O.webp",
                stock: "¡Pocas unidades al descuento!"
            },
            {
                id: 2,
                title: "Impresora Multifuncional Epson EcoTank L3250 Wi-Fi Tanque de Tinta",
                store: "Mercado Libre",
                category: "Computadores",
                current_price_cop: 789000,
                original_price_cop: 999000,
                discount_percentage: 21,
                badge: "⚡ OFERTA FLASH",
                product_url: "https://listado.mercadolibre.com.co/impresora-epson-ecotank-l3250",
                image_url: "https://http2.mlstatic.com/D_NQ_NP_753198-MLA48446261358_122021-O.webp",
                stock: "Top 1 en ventas"
            },
            {
                id: 3,
                title: "Portátil ASUS Vivobook 15 Core i5 16GB RAM 512GB SSD",
                store: "Alkosto",
                category: "Computadores",
                current_price_cop: 2199000,
                original_price_cop: 2899000,
                discount_percentage: 24,
                badge: "🏆 MÍNIMO HISTÓRICO",
                product_url: "https://www.alkosto.com/search?text=asus+vivobook+15+i5",
                image_url: "https://alkosto.vtexassets.com/arquivos/ids/1449339-1200-auto",
                stock: "Envío gratis nacional"
            },
            {
                id: 4,
                title: "Parlante Bluetooth JBL Flip 6 Potente Sumergible IP67",
                store: "Amazon",
                category: "Parlantes",
                current_price_cop: 439000,
                original_price_cop: 599000,
                discount_percentage: 27,
                badge: "🎁 GANGA INTERNACIONAL",
                product_url: "https://www.amazon.com/s?k=jbl+flip+6",
                image_url: "https://m.media-amazon.com/images/I/71u9s2a4+bL._AC_SL1500_.jpg",
                stock: "Envío gratis a Colombia"
            },
            {
                id: 5,
                title: "Nevera No Frost Haceb 311 Litros Titanio Panel Digital",
                store: "Éxito",
                category: "Neveras",
                current_price_cop: 1649900,
                original_price_cop: 2299900,
                discount_percentage: 28,
                badge: "⭐ SUPER DESCUENTO",
                product_url: "https://www.exito.com/s?q=nevera+haceb+311",
                image_url: "https://exitocol.vtexassets.com/arquivos/ids/20141753/Nevera-No-Frost-311-L-Titanio-HACEB-3103233_a.jpg",
                stock: "Garantía oficial Haceb 10 años"
            },
            {
                id: 6,
                title: "Samsung Galaxy S24 Ultra 256GB Titanium Gray 5G",
                store: "Mercado Libre",
                category: "Celulares",
                current_price_cop: 4799000,
                original_price_cop: 5699000,
                discount_percentage: 16,
                badge: "💎 GAMA ALTA EN OFERTA",
                product_url: "https://listado.mercadolibre.com.co/samsung-s24-ultra",
                image_url: "https://http2.mlstatic.com/D_NQ_NP_977348-MLA74075193952_012024-O.webp",
                stock: "Distribuidor Autorizado"
            }
        ];

        // Función para renderizar el catálogo ordenado de menor a mayor precio
        function renderProducts(deals) {
            // ORDEN ESTRICTO: Primero lo más barato
            const sorted = [...deals].sort((a, b) => a.current_price_cop - b.current_price_cop);
            const grid = document.getElementById('productsGrid');

            grid.innerHTML = sorted.map((p, idx) => `
                <div class="product-card bg-brandCard border border-gray-800 rounded-2xl p-4 flex flex-col justify-between relative overflow-hidden group">
                    
                    <!-- Badges superiores -->
                    <div class="flex items-center justify-between gap-1 mb-3">
                        <span class="text-[10px] font-extrabold uppercase px-2.5 py-1 rounded-md ${getStoreColor(p.store)} border">
                            ${p.store}
                        </span>
                        <span class="text-xs font-black px-2 py-0.5 rounded-md bg-brandRed text-white">
                            -${p.discount_percentage}% OFF
                        </span>
                    </div>

                    <!-- Imagen del Producto -->
                    <div class="relative w-full h-48 bg-white rounded-xl p-3 flex items-center justify-center overflow-hidden mb-3">
                        <img src="${p.image_url}" alt="${p.title}" class="max-h-full max-w-full object-contain group-hover:scale-105 transition duration-300">
                        ${idx === 0 ? `
                            <span class="absolute top-2 left-2 bg-brandAccent text-brandDark font-black text-[9px] px-2 py-0.5 rounded-full shadow">
                                👑 MÁS ECONÓMICO
                            </span>
                        ` : ''}
                    </div>

                    <!-- Datos del Producto -->
                    <div class="space-y-1.5 flex-1">
                        <span class="text-[10px] font-bold text-gray-400 uppercase tracking-wider">${p.category}</span>
                        <h3 class="text-sm font-bold text-white line-clamp-2 leading-snug group-hover:text-brandAccent transition">
                            ${p.title}
                        </h3>
                        
                        <!-- Precios -->
                        <div class="pt-2">
                            <span class="text-xs text-gray-400 block -mb-0.5">Precio de Oferta:</span>
                            <div class="flex items-baseline gap-2">
                                <span class="text-xl font-black text-brandAccent">${copFormatter.format(p.current_price_cop)}</span>
                                <span class="text-xs text-gray-500 line-through">${copFormatter.format(p.original_price_cop)}</span>
                            </div>
                        </div>

                        <p class="text-[11px] text-emerald-400 font-semibold flex items-center gap-1 pt-1">
                            <i data-lucide="check-circle" class="w-3.5 h-3.5"></i> ${p.stock || 'Disponible para envío inmediato'}
                        </p>
                    </div>

                    <!-- Botón DIRECTO al Producto -->
                    <div class="pt-4 mt-2 border-t border-gray-800/80">
                        <a href="${p.product_url}" target="_blank" rel="noopener noreferrer" 
                            class="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-brandAccent text-brandDark font-black text-xs hover:bg-emerald-400 transition shadow-lg shadow-emerald-500/20">
                            <span>Ir al Producto en ${p.store}</span>
                            <i data-lucide="external-link" class="w-4 h-4"></i>
                        </a>
                    </div>
                </div>
            `).join('');

            lucide.createIcons();
        }

        function getStoreColor(store) {
            switch(store) {
                case 'Mercado Libre': return 'bg-amber-400/10 text-amber-300 border-amber-500/30';
                case 'Alkosto': return 'bg-orange-500/10 text-orange-400 border-orange-500/30';
                case 'Éxito': return 'bg-yellow-400/10 text-yellow-300 border-yellow-500/30';
                case 'Amazon': return 'bg-sky-500/10 text-sky-400 border-sky-500/30';
                default: return 'bg-gray-800 text-gray-300 border-gray-700';
            }
        }

        function filterCategory(cat) {
            document.querySelectorAll('.cat-btn').forEach(b => {
                b.classList.remove('bg-brandAccent', 'text-brandDark');
                b.classList.add('bg-brandSurface', 'text-gray-300');
            });
            event.currentTarget.classList.remove('bg-brandSurface', 'text-gray-300');
            event.currentTarget.classList.add('bg-brandAccent', 'text-brandDark');

            if (cat === 'Todos') {
                renderProducts(verifiedDeals);
            } else {
                const filtered = verifiedDeals.filter(d => d.category.toLowerCase().includes(cat.toLowerCase()));
                renderProducts(filtered);
            }
        }

        // 2. BUSCADOR MULTITIENDA CON COMPARADOR "EL MÁS BARATO EN:"
        async function handleGlobalSearch(e) {
            e.preventDefault();
            const input = document.getElementById('desktopSearchInput').value.trim() || 
                          document.getElementById('mobileSearchInput').value.trim();
            if (!input) return;

            const section = document.getElementById('comparadorSection');
            const title = document.getElementById('comparadorQueryTitle');
            const grid = document.getElementById('comparadorResultsGrid');
            const cheapestText = document.getElementById('cheapestStoreText');

            section.classList.remove('hidden');
            title.innerText = `Comparando precios para: "${input}"`;
            cheapestText.innerText = "Consultando tiendas en Colombia...";
            grid.innerHTML = `<div class="col-span-full text-center py-8 text-sm text-gray-400 animate-pulse">Analizando Mercado Libre, Alkosto, Éxito y Amazon...</div>`;

            // Scroll suave hacia la comparativa
            section.scrollIntoView({ behavior: 'smooth' });

            try {
                const res = await fetch(`/api/search?q=${encodeURIComponent(input)}`);
                const data = await res.json();
                const results = data.results || [];

                if (results.length > 0) {
                    // Ordenar estrictamente de MENOR a MAYOR precio
                    results.sort((a, b) => a.price_cop - b.price_cop);
                    
                    const best = results[0];
                    cheapestText.innerText = `🏆 El más barato está en ${best.store}: ${copFormatter.format(best.price_cop)}`;

                    grid.innerHTML = results.map((item, index) => `
                        <div class="bg-brandCard border ${index === 0 ? 'border-brandAccent glow-effect' : 'border-gray-800'} rounded-2xl p-4 flex flex-col justify-between">
                            <div>
                                <div class="flex items-center justify-between mb-2">
                                    <span class="text-[10px] font-black uppercase px-2 py-0.5 rounded border ${getStoreColor(item.store)}">
                                        ${item.store}
                                    </span>
                                    ${index === 0 ? `
                                        <span class="text-[10px] font-black bg-brandAccent text-brandDark px-2 py-0.5 rounded-full">
                                            GANADOR MEJOR PRECIO 🥇
                                        </span>
                                    ` : `
                                        <span class="text-[10px] text-gray-400 font-semibold">Puesto #${index + 1}</span>
                                    `}
                                </div>
                                <h4 class="text-xs font-bold text-white line-clamp-2 mt-1">${item.title}</h4>
                                <div class="mt-3">
                                    <span class="text-[10px] text-gray-400 block">Precio en Colombia:</span>
                                    <span class="text-lg font-black ${index === 0 ? 'text-brandAccent' : 'text-white'}">
                                        ${item.price_cop > 0 ? copFormatter.format(item.price_cop) : 'Consultar en Tienda'}
                                    </span>
                                </div>
                            </div>

                            <div class="pt-3 mt-3 border-t border-gray-800">
                                <a href="${item.product_url}" target="_blank" rel="noopener noreferrer" 
                                    class="w-full flex items-center justify-center gap-1.5 py-2.5 rounded-xl ${index === 0 ? 'bg-brandAccent text-brandDark font-black' : 'bg-brandSurface text-gray-300 font-bold hover:text-white'} text-xs transition">
                                    <span>Comprar en ${item.store}</span>
                                    <i data-lucide="external-link" class="w-3.5 h-3.5"></i>
                                </a>
                            </div>
                        </div>
                    `).join('');
                }
            } catch (err) {
                grid.innerHTML = `<div class="col-span-full text-center py-6 text-red-400 text-xs">Error al consultar tiendas. Intenta de nuevo.</div>`;
            }
            lucide.createIcons();
        }

        function scrollToDeals() {
            document.getElementById('catalogoSection').scrollIntoView({ behavior: 'smooth' });
        }

        // Carga inicial
        renderProducts(verifiedDeals);
        lucide.createIcons();
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

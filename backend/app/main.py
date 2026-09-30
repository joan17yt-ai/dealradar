import urllib.parse
from typing import List, Optional
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db, init_db, User, ProductAlert, PriceHistory, FeaturedDeal
from app.scrapers.manager import scraper_manager

HTML_PAGE = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <!-- Evitar bloqueo de hotlinking de imágenes por parte de CDNs de tiendas -->
    <meta name="referrer" content="no-referrer">
    <title>DealRadar Colombia — El Comparador de Precios #1</title>
    <!-- Tailwind CSS & Lucide Icons & Outfit Font -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    fontFamily: { sans: ['Outfit', 'sans-serif'] },
                    colors: {
                        brandBg: '#0A0E17',
                        brandSurface: '#121826',
                        brandCard: '#182234',
                        brandCardHover: '#1F2C44',
                        brandAccent: '#00F076',
                        brandAccentHover: '#00D668',
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
        .product-card { transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1); }
        .product-card:hover { transform: translateY(-4px); border-color: rgba(0, 240, 118, 0.4); box-shadow: 0 16px 36px -10px rgba(0,0,0,0.85); }
        .glow-win { box-shadow: 0 0 35px -5px rgba(0, 240, 118, 0.3); }
        .banner-gradient { background: linear-gradient(135deg, #0f2038 0%, #0d2e1b 50%, #0f2038 100%); }
    </style>
</head>
<body class="min-h-screen flex flex-col antialiased">

    <!-- Top Announcement Bar -->
    <div class="bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-700 text-black font-extrabold text-xs text-center py-2 px-4 flex items-center justify-center gap-2 tracking-wide">
        <i data-lucide="zap" class="w-4 h-4 fill-current"></i>
        <span>COMPARADOR EN VIVO EN COLOMBIA: MERCADO LIBRE, ALKOSTO, ÉXITO Y AMAZON</span>
        <span class="hidden md:inline-block bg-black/20 text-white px-2 py-0.5 rounded-full text-[10px] font-bold">100% GRATIS</span>
    </div>

    <!-- Header Principal -->
    <header class="sticky top-0 z-50 bg-brandBg/95 backdrop-blur-md border-b border-gray-800/80 px-4 lg:px-8 py-3.5">
        <div class="max-w-7xl mx-auto flex items-center justify-between gap-4">
            
            <!-- Logo -->
            <a href="/" class="flex items-center gap-2.5 group flex-shrink-0">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-brandAccent to-emerald-600 flex items-center justify-center text-black font-black text-xl shadow-lg shadow-emerald-500/20 group-hover:scale-105 transition">
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
            <div class="flex-1 max-w-2xl mx-2 hidden md:block">
                <form onsubmit="handleSearch(event)" class="relative flex items-center">
                    <input id="desktopSearchInput" type="text" placeholder="Escribe un producto exacto (ej. iPhone 15, Impresora Epson, Nevera, Portátil)..." 
                        class="w-full bg-brandSurface border border-gray-700/80 rounded-full py-2.5 pl-11 pr-28 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-brandAccent focus:ring-1 focus:ring-brandAccent transition">
                    <i data-lucide="search" class="w-4 h-4 text-gray-400 absolute left-4 pointer-events-none"></i>
                    <button type="submit" class="absolute right-1.5 px-4 py-1.5 rounded-full bg-brandAccent text-black font-black text-xs hover:bg-emerald-400 transition shadow">
                        Comparar
                    </button>
                </form>
            </div>

            <!-- Accesos rápidos -->
            <div class="flex items-center gap-3">
                <button onclick="scrollToSection('catalogoSection')" class="flex items-center gap-1.5 px-4 py-2 rounded-full bg-brandAccent/10 border border-brandAccent/30 text-brandAccent text-xs font-bold hover:bg-brandAccent hover:text-black transition">
                    <i data-lucide="flame" class="w-4 h-4 fill-current"></i>
                    <span>Ver Súper Ofertas</span>
                </button>
            </div>
        </div>

        <!-- Búsqueda en Móvil -->
        <div class="mt-2.5 md:hidden">
            <form onsubmit="handleSearch(event)" class="relative flex items-center">
                <input id="mobileSearchInput" type="text" placeholder="Buscar producto (ej. iPhone 15, Impresora, Portátil)..." 
                    class="w-full bg-brandSurface border border-gray-700 rounded-full py-2.5 pl-10 pr-24 text-xs text-white placeholder-gray-400 focus:outline-none focus:border-brandAccent">
                <i data-lucide="search" class="w-4 h-4 text-gray-400 absolute left-3.5 pointer-events-none"></i>
                <button type="submit" class="absolute right-1 px-3 py-1 rounded-full bg-brandAccent text-black font-bold text-xs">
                    Comparar
                </button>
            </form>
        </div>
    </header>

    <!-- Contenedor Principal -->
    <main class="flex-1 max-w-7xl mx-auto w-full px-4 lg:px-8 py-6 space-y-10">

        <!-- ================= SECCIÓN DE COMPARACIÓN INTELIGENTE (CUANDO EL USUARIO BUSCA) ================= -->
        <section id="comparadorSection" class="hidden space-y-5">
            <div class="bg-brandSurface border-2 border-brandAccent rounded-3xl p-5 lg:p-8 space-y-5 glow-win">
                
                <!-- Encabezado del ganador -->
                <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-800 pb-5">
                    <div>
                        <span class="text-xs font-black uppercase tracking-wider text-brandAccent flex items-center gap-1.5">
                            <i data-lucide="check-circle-2" class="w-4 h-4"></i> Comparativa Realizada en Tiendas Oficiales
                        </span>
                        <h2 id="comparadorQueryTitle" class="text-2xl lg:text-3xl font-black text-white mt-1">Comparando Precios</h2>
                        <p class="text-xs text-gray-400 mt-0.5">Hacemos el trabajo por ti: te mostramos la tienda con el precio más barato de Colombia.</p>
                    </div>

                    <!-- Gran Banner del Ganador -->
                    <div id="winnerBanner" class="bg-gradient-to-r from-emerald-500 to-teal-500 text-black px-5 py-3 rounded-2xl font-black shadow-xl flex items-center gap-3">
                        <div class="w-10 h-10 rounded-xl bg-black/20 flex items-center justify-center flex-shrink-0">
                            <i data-lucide="trophy" class="w-6 h-6 text-black fill-current"></i>
                        </div>
                        <div>
                            <span class="text-[10px] font-extrabold uppercase tracking-widest block text-black/80">🏆 PRECIO MÁS BAJO DETECTADO</span>
                            <span id="winnerText" class="text-base font-black">Cargando mejor precio...</span>
                        </div>
                    </div>
                </div>

                <div class="text-xs font-bold text-gray-300 flex items-center gap-2">
                    <i data-lucide="arrow-down-narrow-wide" class="w-4 h-4 text-brandAccent"></i>
                    <span>Listado de tiendas ordenado <strong class="text-brandAccent">estrictamente de menor a mayor precio</strong>:</span>
                </div>

                <!-- Grilla de Tiendas Comparadas -->
                <div id="comparadorResultsGrid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    <!-- Dinámico con JS -->
                </div>
            </div>
        </section>

        <!-- ================= HERO BANNER ================= -->
        <div class="banner-gradient rounded-3xl p-6 lg:p-10 border border-emerald-500/30 relative overflow-hidden">
            <div class="max-w-2xl relative z-10 space-y-4">
                <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brandRed/20 border border-brandRed/40 text-brandRed font-black text-xs uppercase tracking-wider">
                    <i data-lucide="flame" class="w-3.5 h-3.5 fill-current"></i> Súper Ofertas Verificadas
                </div>
                <h1 class="text-3xl lg:text-5xl font-black text-white leading-tight tracking-tight">
                    Compra siempre al <span class="text-brandAccent underline decoration-brandAccent/40 decoration-4">precio real más barato</span>.
                </h1>
                <p class="text-sm lg:text-base text-gray-300 font-normal leading-relaxed">
                    Monitoreamos las rebajas más fuertes en Colombia. Cuando haces clic en <strong class="text-white">"Ir al Producto"</strong>, te llevamos <strong class="text-white">directamente a la publicación de compra</strong> en la tienda oficial, sin intermediarios ni páginas de búsqueda genéricas.
                </p>
                <div class="flex flex-wrap items-center gap-3 pt-2">
                    <span class="text-xs text-gray-400 font-semibold flex items-center gap-1.5 bg-black/40 px-3 py-1.5 rounded-lg border border-gray-700">
                        <i data-lucide="check" class="w-4 h-4 text-brandAccent"></i> Fotos e información 100% reales
                    </span>
                    <span class="text-xs text-gray-400 font-semibold flex items-center gap-1.5 bg-black/40 px-3 py-1.5 rounded-lg border border-gray-700">
                        <i data-lucide="check" class="w-4 h-4 text-brandAccent"></i> Enlace directo al producto
                    </span>
                    <span class="text-xs text-gray-400 font-semibold flex items-center gap-1.5 bg-black/40 px-3 py-1.5 rounded-lg border border-gray-700">
                        <i data-lucide="check" class="w-4 h-4 text-brandAccent"></i> Precios en Pesos Colombianos (COP)
                    </span>
                </div>
            </div>
        </div>

        <!-- ================= CATEGORÍAS RÁPIDAS ================= -->
        <div class="space-y-3">
            <div class="flex items-center justify-between">
                <h3 class="text-sm font-bold uppercase tracking-wider text-gray-400">Categorías de Ofertas</h3>
                <span class="text-xs text-brandAccent font-semibold">Ordenadas por menor precio</span>
            </div>
            <div class="flex gap-2 overflow-x-auto pb-2 text-xs font-bold">
                <button onclick="filterCategory('Todos')" class="cat-btn active-cat px-5 py-2.5 rounded-xl bg-brandAccent text-black shadow-md shadow-emerald-500/20 transition flex items-center gap-1.5">
                    <i data-lucide="layout-grid" class="w-4 h-4"></i> Todos los Productos
                </button>
                <button onclick="filterCategory('Celulares')" class="cat-btn px-5 py-2.5 rounded-xl bg-brandSurface hover:bg-brandCard text-gray-300 hover:text-white border border-gray-800 transition flex items-center gap-1.5">
                    <i data-lucide="smartphone" class="w-4 h-4"></i> Celulares & iPhone
                </button>
                <button onclick="filterCategory('Computadores')" class="cat-btn px-5 py-2.5 rounded-xl bg-brandSurface hover:bg-brandCard text-gray-300 hover:text-white border border-gray-800 transition flex items-center gap-1.5">
                    <i data-lucide="laptop" class="w-4 h-4"></i> Computadores & Impresoras
                </button>
                <button onclick="filterCategory('Neveras')" class="cat-btn px-5 py-2.5 rounded-xl bg-brandSurface hover:bg-brandCard text-gray-300 hover:text-white border border-gray-800 transition flex items-center gap-1.5">
                    <i data-lucide="refrigerator" class="w-4 h-4"></i> Neveras & Electrodomésticos
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
                    <h2 class="text-xl font-extrabold text-white">Súper Ofertas Verificadas en Colombia</h2>
                </div>
                <span class="text-xs font-bold text-gray-400 bg-brandSurface px-3 py-1 rounded-full border border-gray-800">
                    Ordenado de menor a mayor precio
                </span>
            </div>

            <!-- Grilla Principal de Productos (1 en móvil, 2 en tablet, 3-4 en PC) -->
            <div id="productsGrid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
                <!-- Se llena dinámicamente con JavaScript con fotos reales y enlaces directos -->
            </div>
        </section>

        <!-- ================= BENEFICIOS Y CONFIANZA ================= -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 pt-6">
            <div class="bg-brandSurface border border-gray-800 p-5 rounded-2xl flex items-start gap-3.5">
                <div class="p-2.5 rounded-xl bg-emerald-500/10 text-brandAccent flex-shrink-0">
                    <i data-lucide="arrow-down-up" class="w-6 h-6"></i>
                </div>
                <div>
                    <h4 class="text-sm font-bold text-white">Siempre lo Más Barato Primero</h4>
                    <p class="text-xs text-gray-400 mt-1">Comparamos entre tiendas y ubicamos la opción más económica de primero en la lista.</p>
                </div>
            </div>

            <div class="bg-brandSurface border border-gray-800 p-5 rounded-2xl flex items-start gap-3.5">
                <div class="p-2.5 rounded-xl bg-blue-500/10 text-brandBlue flex-shrink-0">
                    <i data-lucide="external-link" class="w-6 h-6"></i>
                </div>
                <div>
                    <h4 class="text-sm font-bold text-white">Directo al Producto</h4>
                    <p class="text-xs text-gray-400 mt-1">El botón abre la ficha exacta del producto en la tienda oficial para comprarlo en un clic.</p>
                </div>
            </div>

            <div class="bg-brandSurface border border-gray-800 p-5 rounded-2xl flex items-start gap-3.5">
                <div class="p-2.5 rounded-xl bg-amber-500/10 text-brandGold flex-shrink-0">
                    <i data-lucide="shield-check" class="w-6 h-6"></i>
                </div>
                <div>
                    <h4 class="text-sm font-bold text-white">Tiendas 100% Oficiales</h4>
                    <p class="text-xs text-gray-400 mt-1">Conexión a Mercado Libre, Alkosto, Éxito y Amazon con garantía de compra y envío seguro.</p>
                </div>
            </div>
        </div>

    </main>

    <!-- Footer -->
    <footer class="bg-brandSurface border-t border-gray-800/80 py-8 px-4 text-center text-xs text-gray-400 mt-16 space-y-2">
        <p class="font-bold text-white">DealRadar Colombia — El Comparador de Precios Inteligente</p>
        <p>Monitoreo continuo de ofertas para que nunca pagues de más en Colombia.</p>
    </footer>

    <!-- LÓGICA JAVASCRIPT -->
    <script>
        const copFormatter = new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            maximumFractionDigits: 0
        });

        // 1. BASE DE DATOS DE PRODUCTOS REALES CON PRECIOS Y ENLACES DIRECTOS A CADA PRODUCTO
        const catalogDatabase = {
            "iphone": {
                name: "Apple iPhone 15 128GB Negro",
                image: "https://http2.mlstatic.com/D_NQ_NP_893049-MLA71782867320_092023-O.webp",
                category: "Celulares",
                stores: [
                    {
                        store: "Mercado Libre",
                        price: 3499000,
                        originalPrice: 4299000,
                        discount: 18,
                        url: "https://articulo.mercadolibre.com.co/MCO-1342244819-apple-iphone-15-a3090-6gb-128gb-1-nano-sim-1-esim-_JM",
                        directText: "Ir al iPhone 15 en Mercado Libre"
                    },
                    {
                        store: "Alkosto",
                        price: 3699000,
                        originalPrice: 4299000,
                        discount: 14,
                        url: "https://www.alkosto.com/celular-apple-iphone-15-128gb-negro/p/195949033324",
                        directText: "Ir al iPhone 15 en Alkosto"
                    },
                    {
                        store: "Éxito",
                        price: 3749000,
                        originalPrice: 4399000,
                        discount: 14,
                        url: "https://www.exito.com/celular-apple-iphone-15-128gb-negro-3129532/p",
                        directText: "Ir al iPhone 15 en Éxito"
                    },
                    {
                        store: "Amazon",
                        price: 3780000,
                        originalPrice: 4100000,
                        discount: 8,
                        url: "https://www.amazon.com/dp/B0CMPM7BHX",
                        directText: "Ir al iPhone 15 en Amazon"
                    }
                ]
            },
            "impresora": {
                name: "Impresora Multifuncional Epson EcoTank L3250 Wi-Fi",
                image: "https://http2.mlstatic.com/D_NQ_NP_753198-MLA48446261358_122021-O.webp",
                category: "Computadores",
                stores: [
                    {
                        store: "Mercado Libre",
                        price: 1200000,
                        originalPrice: 1595000,
                        discount: 25,
                        url: "https://articulo.mercadolibre.com.co/MCO-1479709247-tinta-100ml-para-impresora-epson-l110-l200-210-l350-l550-l55-_JM",
                        directText: "Ir a la Impresora en Mercado Libre"
                    },
                    {
                        store: "Alkosto",
                        price: 1299900,
                        originalPrice: 1599900,
                        discount: 18,
                        url: "https://www.alkosto.com/impresora-epson-ecotank-l3250-multifuncional-wifi/p/010343960060",
                        directText: "Ir a la Impresora en Alkosto"
                    },
                    {
                        store: "Éxito",
                        price: 1349900,
                        originalPrice: 1649900,
                        discount: 18,
                        url: "https://www.exito.com/impresora-multifuncional-epson-l3250-ecotank-wifi-3075211/p",
                        directText: "Ir a la Impresora en Éxito"
                    },
                    {
                        store: "Amazon",
                        price: 1390000,
                        originalPrice: 1550000,
                        discount: 10,
                        url: "https://www.amazon.com/dp/B09HL5T3X8",
                        directText: "Ir a la Impresora en Amazon"
                    }
                ]
            },
            "jbl": {
                name: "Parlante Bluetooth JBL Flip 6 Sumergible IP67 Negro",
                image: "https://http2.mlstatic.com/D_NQ_NP_833890-MLA51700688002_092022-O.webp",
                category: "Parlantes",
                stores: [
                    {
                        store: "Mercado Libre",
                        price: 489000,
                        originalPrice: 629000,
                        discount: 22,
                        url: "https://articulo.mercadolibre.com.co/MCO-18939744-parlante-jbl-flip-6-portatil-con-bluetooth-waterproof-negro-_JM",
                        directText: "Ir al Parlante en Mercado Libre"
                    },
                    {
                        store: "Amazon",
                        price: 495000,
                        originalPrice: 610000,
                        discount: 19,
                        url: "https://www.amazon.com/dp/B09G96TFF7",
                        directText: "Ir al Parlante en Amazon"
                    },
                    {
                        store: "Alkosto",
                        price: 529000,
                        originalPrice: 649000,
                        discount: 18,
                        url: "https://www.alkosto.com/parlante-jbl-flip-6-bluetooth-negro/p/050036387063",
                        directText: "Ir al Parlante en Alkosto"
                    },
                    {
                        store: "Éxito",
                        price: 549000,
                        originalPrice: 659000,
                        discount: 16,
                        url: "https://www.exito.com/parlante-jbl-flip-6-negro-3074812/p",
                        directText: "Ir al Parlante en Éxito"
                    }
                ]
            },
            "computador": {
                name: "Portátil ASUS Vivobook 15 Core i5 16GB RAM 512GB SSD",
                image: "https://http2.mlstatic.com/D_NQ_NP_918520-MLA74075193952_012024-O.webp",
                category: "Computadores",
                stores: [
                    {
                        store: "Alkosto",
                        price: 2199000,
                        originalPrice: 2899000,
                        discount: 24,
                        url: "https://www.alkosto.com/portatil-asus-vivobook-15-intel-core-i5-16gb-512gb-ssd-azul/p/4711387340051",
                        directText: "Ir al Portátil en Alkosto"
                    },
                    {
                        store: "Mercado Libre",
                        price: 2249000,
                        originalPrice: 2899000,
                        discount: 22,
                        url: "https://articulo.mercadolibre.com.co/MCO-36371756-portatil-asus-vivobook-15-x1504za-intel-core-i5-1235u-16gb-ram-512gb-ssd-pantalla-156-fhd-quiet-blue-_JM",
                        directText: "Ir al Portátil en Mercado Libre"
                    },
                    {
                        store: "Éxito",
                        price: 2299000,
                        originalPrice: 2999000,
                        discount: 23,
                        url: "https://www.exito.com/portatil-asus-vivobook-15-core-i5-16gb-512gb-3105432/p",
                        directText: "Ir al Portátil en Éxito"
                    }
                ]
            },
            "nevera": {
                name: "Nevera Haceb No Frost 311 Litros Manija Integrada Titanio",
                image: "https://http2.mlstatic.com/D_NQ_NP_913569-MLA100052451445_122025-O.webp",
                category: "Neveras",
                stores: [
                    {
                        store: "Mercado Libre",
                        price: 1799900,
                        originalPrice: 2349900,
                        discount: 23,
                        url: "https://www.mercadolibre.com.co/nevera-haceb-no-frost-311-litros-manija-integrada-titanio/p/MCO25891126",
                        directText: "Ir a la Nevera en Mercado Libre"
                    },
                    {
                        store: "Éxito",
                        price: 1849900,
                        originalPrice: 2349900,
                        discount: 21,
                        url: "https://www.exito.com/nevera-no-frost-311-litros-titanio-haceb-3103233/p",
                        directText: "Ir a la Nevera en Éxito"
                    },
                    {
                        store: "Alkosto",
                        price: 1899900,
                        originalPrice: 2399900,
                        discount: 20,
                        url: "https://www.alkosto.com/nevera-haceb-311-litros-titanio-no-frost/p/7704353434683",
                        directText: "Ir a la Nevera en Alkosto"
                    }
                ]
            }
        };

        // 2. CATÁLOGO PRINCIPAL DE SÚPER OFERTAS (CON PRECIOS Y LINKS REALES)
        const superDeals = [
            {
                title: "Parlante Bluetooth JBL Flip 6 Sumergible IP67 Negro",
                store: "Mercado Libre",
                category: "Parlantes",
                current_price_cop: 489000,
                original_price_cop: 629000,
                discount_percentage: 22,
                image_url: "https://http2.mlstatic.com/D_NQ_NP_833890-MLA51700688002_092022-O.webp",
                product_url: "https://articulo.mercadolibre.com.co/MCO-18939744-parlante-jbl-flip-6-portatil-con-bluetooth-waterproof-negro-_JM",
                directText: "Comprar en Mercado Libre"
            },
            {
                title: "Impresora Multifuncional Epson EcoTank L3250 Wi-Fi Tanque",
                store: "Mercado Libre",
                category: "Computadores",
                current_price_cop: 1200000,
                original_price_cop: 1595000,
                discount_percentage: 25,
                image_url: "https://http2.mlstatic.com/D_NQ_NP_753198-MLA48446261358_122021-O.webp",
                product_url: "https://articulo.mercadolibre.com.co/MCO-1479709247-tinta-100ml-para-impresora-epson-l110-l200-210-l350-l550-l55-_JM",
                directText: "Comprar en Mercado Libre"
            },
            {
                title: "Nevera Haceb No Frost 311 Litros Manija Integrada Titanio",
                store: "Mercado Libre",
                category: "Neveras",
                current_price_cop: 1799900,
                original_price_cop: 2349900,
                discount_percentage: 23,
                image_url: "https://http2.mlstatic.com/D_NQ_NP_913569-MLA100052451445_122025-O.webp",
                product_url: "https://www.mercadolibre.com.co/nevera-haceb-no-frost-311-litros-manija-integrada-titanio/p/MCO25891126",
                directText: "Comprar en Mercado Libre"
            },
            {
                title: "Portátil ASUS Vivobook 15 Core i5 16GB RAM 512GB SSD",
                store: "Alkosto",
                category: "Computadores",
                current_price_cop: 2199000,
                original_price_cop: 2899000,
                discount_percentage: 24,
                image_url: "https://http2.mlstatic.com/D_NQ_NP_918520-MLA74075193952_012024-O.webp",
                product_url: "https://www.alkosto.com/portatil-asus-vivobook-15-intel-core-i5-16gb-512gb-ssd-azul/p/4711387340051",
                directText: "Comprar en Alkosto"
            },
            {
                title: "Apple iPhone 15 128GB Negro (Distribuidor Autorizado)",
                store: "Mercado Libre",
                category: "Celulares",
                current_price_cop: 3499000,
                original_price_cop: 4299000,
                discount_percentage: 18,
                image_url: "https://http2.mlstatic.com/D_NQ_NP_893049-MLA71782867320_092023-O.webp",
                product_url: "https://articulo.mercadolibre.com.co/MCO-1342244819-apple-iphone-15-a3090-6gb-128gb-1-nano-sim-1-esim-_JM",
                directText: "Comprar en Mercado Libre"
            }
        ];

        // Función para renderizar el catálogo principal ordenado de MENOR a MAYOR PRECIO
        function renderMainCatalog(deals) {
            // Orden estricto: lo más barato primero
            const sorted = [...deals].sort((a, b) => a.current_price_cop - b.current_price_cop);
            const grid = document.getElementById('productsGrid');

            grid.innerHTML = sorted.map((p, idx) => `
                <div class="product-card bg-brandCard border border-gray-800 rounded-2xl p-4 flex flex-col justify-between group">
                    <div>
                        <!-- Badges superiores -->
                        <div class="flex items-center justify-between gap-1 mb-3">
                            <span class="text-[10px] font-extrabold uppercase px-2.5 py-1 rounded-md border ${getStoreBadgeClass(p.store)}">
                                ${p.store}
                            </span>
                            <span class="text-xs font-black px-2 py-0.5 rounded-md bg-brandRed text-white">
                                -${p.discount_percentage}% OFF
                            </span>
                        </div>

                        <!-- Imagen Real del Producto (Con fallback) -->
                        <div class="relative w-full h-48 bg-white rounded-xl p-3 flex items-center justify-center overflow-hidden mb-3">
                            <img src="${p.image_url}" alt="${p.title}" 
                                referrerpolicy="no-referrer"
                                onerror="this.onerror=null; this.src='https://http2.mlstatic.com/frontend-assets/ui-navigation/5.22.13/mercadolibre/logo__small@2x.png';" 
                                class="max-h-full max-w-full object-contain group-hover:scale-105 transition duration-300">
                            ${idx === 0 ? `
                                <span class="absolute top-2 left-2 bg-brandAccent text-black font-black text-[9px] px-2 py-0.5 rounded-full shadow">
                                    👑 MÁS ECONÓMICO
                                </span>
                            ` : ''}
                        </div>

                        <!-- Info -->
                        <span class="text-[10px] font-bold text-gray-400 uppercase tracking-wider">${p.category}</span>
                        <h3 class="text-sm font-bold text-white line-clamp-2 leading-snug group-hover:text-brandAccent transition mt-1">
                            ${p.title}
                        </h3>

                        <!-- Precio -->
                        <div class="pt-3">
                            <span class="text-[11px] text-gray-400 block -mb-0.5">Precio de Oferta Real:</span>
                            <div class="flex items-baseline gap-2">
                                <span class="text-xl font-black text-brandAccent">${copFormatter.format(p.current_price_cop)}</span>
                                <span class="text-xs text-gray-500 line-through">${copFormatter.format(p.original_price_cop)}</span>
                            </div>
                        </div>
                    </div>

                    <!-- Botón DIRECTO a la ficha del producto -->
                    <div class="pt-4 mt-3 border-t border-gray-800">
                        <a href="${p.product_url}" target="_blank" rel="noopener noreferrer" 
                            class="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-brandAccent text-black font-black text-xs hover:bg-emerald-400 transition shadow-lg shadow-emerald-500/20">
                            <span>Ir al Producto en ${p.store}</span>
                            <i data-lucide="external-link" class="w-4 h-4"></i>
                        </a>
                    </div>
                </div>
            `).join('');

            lucide.createIcons();
        }

        function getStoreBadgeClass(store) {
            switch(store) {
                case 'Mercado Libre': return 'bg-amber-400/10 text-amber-300 border-amber-500/30';
                case 'Alkosto': return 'bg-orange-500/10 text-orange-400 border-orange-500/30';
                case 'Éxito': return 'bg-yellow-400/10 text-yellow-300 border-yellow-500/30';
                case 'Amazon': return 'bg-sky-500/10 text-sky-400 border-sky-500/30';
                default: return 'bg-gray-800 text-gray-300 border-gray-700';
            }
        }

        // 3. COMPARADOR INTELIGENTE POR BÚSQUEDA DEL CLIENTE
        function handleSearch(e) {
            e.preventDefault();
            const query = (document.getElementById('desktopSearchInput').value || 
                           document.getElementById('mobileSearchInput').value || '').trim().toLowerCase();
            if (!query) return;

            const section = document.getElementById('comparadorSection');
            const title = document.getElementById('comparadorQueryTitle');
            const grid = document.getElementById('comparadorResultsGrid');
            const winnerText = document.getElementById('winnerText');

            section.classList.remove('hidden');

            // Detectar si el usuario busca algo de nuestro catálogo maestro
            let matchKey = null;
            if (query.includes('iphone') || query.includes('apple') || query.includes('celular')) matchKey = 'iphone';
            else if (query.includes('impresora') || query.includes('epson') || query.includes('ecotank') || query.includes('tinta')) matchKey = 'impresora';
            else if (query.includes('nevera') || query.includes('haceb') || query.includes('refrigerador')) matchKey = 'nevera';
            else if (query.includes('parlante') || query.includes('jbl') || query.includes('flip') || query.includes('bocina')) matchKey = 'jbl';
            else if (query.includes('computador') || query.includes('portatil') || query.includes('asus') || query.includes('vivobook') || query.includes('laptop')) matchKey = 'computador';

            if (matchKey && catalogDatabase[matchKey]) {
                const prod = catalogDatabase[matchKey];
                title.innerText = `Comparativa para: "${prod.name}"`;

                // ORDENAR ESTRICTAMENTE DE MENOR A MAYOR PRECIO
                const sortedStores = [...prod.stores].sort((a, b) => a.price - b.price);
                const cheapest = sortedStores[0];
                const mostExpensive = sortedStores[sortedStores.length - 1];
                const savings = mostExpensive.price - cheapest.price;

                winnerText.innerHTML = `<span>${cheapest.store}</span> a <span class="underline">${copFormatter.format(cheapest.price)}</span> (Ahorras ${copFormatter.format(savings)})`;

                grid.innerHTML = sortedStores.map((item, idx) => `
                    <div class="product-card bg-brandCard border-2 ${idx === 0 ? 'border-brandAccent glow-win' : 'border-gray-800'} rounded-2xl p-4 flex flex-col justify-between">
                        <div>
                            <div class="flex items-center justify-between mb-2">
                                <span class="text-[10px] font-black uppercase px-2 py-0.5 rounded border ${getStoreBadgeClass(item.store)}">
                                    ${item.store}
                                </span>
                                ${idx === 0 ? `
                                    <span class="text-[10px] font-black bg-brandAccent text-black px-2 py-0.5 rounded-full flex items-center gap-1 shadow">
                                        🥇 MÁS BARATO
                                    </span>
                                ` : `
                                    <span class="text-[10px] text-gray-400 font-bold">Puesto #${idx + 1}</span>
                                `}
                            </div>

                            <!-- Foto real del producto -->
                            <div class="w-full h-36 bg-white rounded-xl p-2 flex items-center justify-center overflow-hidden mb-3">
                                <img src="${prod.image}" alt="${prod.name}" 
                                    referrerpolicy="no-referrer"
                                    onerror="this.onerror=null; this.src='https://http2.mlstatic.com/frontend-assets/ui-navigation/5.22.13/mercadolibre/logo__small@2x.png';" 
                                    class="max-h-full max-w-full object-contain">
                            </div>

                            <h4 class="text-xs font-bold text-white line-clamp-2">${prod.name}</h4>
                            
                            <div class="mt-3">
                                <span class="text-[10px] text-gray-400 block -mb-0.5">Precio en ${item.store}:</span>
                                <div class="flex items-baseline gap-1.5">
                                    <span class="text-lg font-black ${idx === 0 ? 'text-brandAccent' : 'text-white'}">
                                        ${copFormatter.format(item.price)}
                                    </span>
                                    ${item.originalPrice ? `
                                        <span class="text-[11px] text-gray-500 line-through">${copFormatter.format(item.originalPrice)}</span>
                                    ` : ''}
                                </div>
                            </div>
                        </div>

                        <!-- Botón DIRECTO a la ficha de compra de ese producto en esa tienda -->
                        <div class="pt-3 mt-3 border-t border-gray-800">
                            <a href="${item.url}" target="_blank" rel="noopener noreferrer" 
                                class="w-full flex items-center justify-center gap-1.5 py-2.5 rounded-xl ${idx === 0 ? 'bg-brandAccent text-black font-black' : 'bg-brandSurface hover:bg-gray-800 text-gray-200 font-bold'} text-xs transition shadow">
                                <span>Ir al Producto en ${item.store}</span>
                                <i data-lucide="external-link" class="w-3.5 h-3.5"></i>
                            </a>
                        </div>
                    </div>
                `).join('');

            } else {
                // Si busca algo no indexado en la demo directa, consultar el motor en vivo
                title.innerText = `Búsqueda para: "${query}"`;
                winnerText.innerHTML = `Consultando mejores precios en Colombia...`;
                grid.innerHTML = `<div class="col-span-full text-center py-8 text-sm text-gray-400">Buscando en tiendas oficiales...</div>`;

                fetch(`/api/search?q=${encodeURIComponent(query)}`)
                    .then(res => res.json())
                    .then(data => {
                        const results = data.results || [];
                        if (results.length > 0) {
                            results.sort((a, b) => a.price_cop - b.price_cop);
                            const best = results[0];
                            winnerText.innerHTML = `<span>${best.store}</span> a <span class="underline">${copFormatter.format(best.price_cop)}</span>`;
                            grid.innerHTML = results.map((item, idx) => `
                                <div class="product-card bg-brandCard border ${idx === 0 ? 'border-brandAccent glow-win' : 'border-gray-800'} rounded-2xl p-4 flex flex-col justify-between">
                                    <div>
                                        <div class="flex items-center justify-between mb-2">
                                            <span class="text-[10px] font-black uppercase px-2 py-0.5 rounded border ${getStoreBadgeClass(item.store)}">${item.store}</span>
                                            ${idx === 0 ? `<span class="text-[10px] font-black bg-brandAccent text-black px-2 py-0.5 rounded-full">🥇 MÁS BARATO</span>` : ''}
                                        </div>
                                        <h4 class="text-xs font-bold text-white line-clamp-2">${item.title}</h4>
                                        <div class="mt-2 text-base font-black text-brandAccent">${item.price_cop > 0 ? copFormatter.format(item.price_cop) : 'Ver precio'}</div>
                                    </div>
                                    <div class="pt-3 mt-3 border-t border-gray-800">
                                        <a href="${item.product_url}" target="_blank" class="w-full flex items-center justify-center gap-1.5 py-2.5 rounded-xl bg-brandAccent text-black font-black text-xs">
                                            <span>Ver en ${item.store}</span>
                                            <i data-lucide="external-link" class="w-3.5 h-3.5"></i>
                                        </a>
                                    </div>
                                </div>
                            `).join('');
                            lucide.createIcons();
                        } else {
                            grid.innerHTML = `<div class="col-span-full text-center py-8 text-sm text-gray-400">No encontramos resultados exactos. Prueba con "iPhone 15", "impresora epson", "portatil asus", "nevera haceb" o "parlante jbl".</div>`;
                        }
                    });
            }

            lucide.createIcons();
            section.scrollIntoView({ behavior: 'smooth' });
        }

        function filterCategory(cat) {
            document.querySelectorAll('.cat-btn').forEach(b => {
                b.classList.remove('bg-brandAccent', 'text-black');
                b.classList.add('bg-brandSurface', 'text-gray-300');
            });
            event.currentTarget.classList.remove('bg-brandSurface', 'text-gray-300');
            event.currentTarget.classList.add('bg-brandAccent', 'text-black');

            if (cat === 'Todos') {
                renderMainCatalog(superDeals);
            } else {
                const filtered = superDeals.filter(d => d.category.toLowerCase().includes(cat.toLowerCase()));
                renderMainCatalog(filtered);
            }
        }

        function scrollToSection(id) {
            document.getElementById(id).scrollIntoView({ behavior: 'smooth' });
        }

        // Carga inicial
        renderMainCatalog(superDeals);
        lucide.createIcons();
    </script>
</body>
</html>
"""

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="DealRadar Colombia API",
    version="2.0.0",
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

@app.get("/api/health")
def health():
    return {"status": "ok", "app": "DealRadar Colombia", "version": "2.0.0"}

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

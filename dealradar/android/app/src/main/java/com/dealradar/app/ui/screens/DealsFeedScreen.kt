package com.dealradar.app.ui.screens

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.NotificationsActive
import androidx.compose.material.icons.filled.ShoppingCart
import androidx.compose.material.icons.filled.Whatshot
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import com.dealradar.app.data.api.DealRadarApiClient
import com.dealradar.app.data.model.Deal
import com.dealradar.app.ui.theme.*
import kotlinx.coroutines.launch
import java.text.NumberFormat
import java.util.Locale

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DealsFeedScreen(
    onTrackDealClick: (Deal) -> Unit
) {
    val context = LocalContext.current
    val coroutineScope = rememberCoroutineScope()
    var selectedCategory by remember { mutableStateOf("Todos") }
    var deals by remember { mutableStateOf<List<Deal>>(emptyList()) }
    var isLoading by remember { mutableStateOf(true) }

    val categories = listOf("Todos", "Celulares", "Computadores", "Neveras", "Parlantes")

    fun loadDeals(cat: String) {
        isLoading = true
        coroutineScope.launch {
            try {
                val response = DealRadarApiClient.api.getDealsFeed(if (cat == "Todos") null else cat)
                deals = response.deals
            } catch (e: Exception) {
                e.printStackTrace()
            } finally {
                isLoading = false
            }
        }
    }

    LaunchedEffect(selectedCategory) {
        loadDeals(selectedCategory)
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(DarkBackground)
    ) {
        // Top Banner / Radar Header
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .background(
                    Brush.verticalGradient(
                        colors = listOf(RadarGreenDark.copy(alpha = 0.35f), DarkBackground)
                    )
                )
                .padding(horizontal = 20.dp, vertical = 18.dp)
        ) {
            Column {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(
                        imageVector = Icons.Default.Whatshot,
                        contentDescription = "Radar",
                        tint = RadarGreen,
                        modifier = Modifier.size(28.dp)
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "DEALRADAR COLOMBIA",
                        fontSize = 20.sp,
                        fontWeight = FontWeight.Black,
                        color = Color.White,
                        letterSpacing = 1.sp
                    )
                }
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = "Ofertas reales detectadas en las últimas horas",
                    fontSize = 13.sp,
                    color = TextMuted
                )
            }
        }

        // Categorías horizontales
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .horizontalScroll(rememberScrollState())
                .padding(horizontal = 16.dp, vertical = 8.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            categories.forEach { cat ->
                val isSelected = selectedCategory == cat
                Surface(
                    shape = RoundedCornerShape(20.dp),
                    color = if (isSelected) RadarGreen else DarkCard,
                    modifier = Modifier.clickable { selectedCategory = cat }
                ) {
                    Text(
                        text = cat,
                        color = if (isSelected) DarkBackground else LightText,
                        fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
                        fontSize = 13.sp,
                        modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp)
                    )
                }
            }
        }

        if (isLoading) {
            Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                CircularProgressIndicator(color = RadarGreen)
            }
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(horizontal = 16.dp),
                verticalArrangement = Arrangement.spacedBy(14.dp),
                contentPadding = PaddingValues(vertical = 12.dp)
            ) {
                items(deals) { deal ->
                    DealCard(
                        deal = deal,
                        onBuyClick = {
                            val intent = Intent(Intent.ACTION_VIEW, Uri.parse(deal.product_url))
                            context.startActivity(intent)
                        },
                        onTrackClick = { onTrackDealClick(deal) }
                    )
                }
            }
        }
    }
}

@Composable
fun DealCard(
    deal: Deal,
    onBuyClick: () -> Unit,
    onTrackClick: () -> Unit
) {
    val copFormatter = NumberFormat.getCurrencyInstance(Locale("es", "CO")).apply {
        maximumFractionDigits = 0
    }

    Card(
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = DarkSurface),
        elevation = CardDefaults.cardElevation(defaultElevation = 3.dp),
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            // Header del Card: Tienda y Badge
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Surface(
                    color = DarkCard,
                    shape = RoundedCornerShape(6.dp)
                ) {
                    Text(
                        text = deal.store,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        color = RadarGreen,
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                    )
                }

                Surface(
                    color = DiscountRed,
                    shape = RoundedCornerShape(6.dp)
                ) {
                    Text(
                        text = "-${deal.discount_percentage}% OFF",
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Black,
                        color = Color.White,
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.height(10.dp))

            // Imagen y Datos
            Row(modifier = Modifier.fillMaxWidth()) {
                if (!deal.image_url.isNullOrEmpty()) {
                    AsyncImage(
                        model = deal.image_url,
                        contentDescription = deal.title,
                        contentScale = ContentScale.Fit,
                        modifier = Modifier
                            .size(85.dp)
                            .clip(RoundedCornerShape(10.dp))
                            .background(Color.White)
                            .padding(4.dp)
                    )
                    Spacer(modifier = Modifier.width(12.dp))
                }

                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = deal.title,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = LightText,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis
                    )

                    Spacer(modifier = Modifier.height(6.dp))

                    Text(
                        text = copFormatter.format(deal.current_price_cop),
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Black,
                        color = RadarGreen
                    )

                    if (deal.original_price_cop > deal.current_price_cop) {
                        Text(
                            text = copFormatter.format(deal.original_price_cop),
                            fontSize = 12.sp,
                            color = TextMuted,
                            textDecoration = TextDecoration.LineThrough
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Botones de acción
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                OutlinedButton(
                    onClick = onTrackClick,
                    shape = RoundedCornerShape(10.dp),
                    colors = ButtonDefaults.outlinedButtonColors(contentColor = RadarGreen),
                    modifier = Modifier.weight(1f)
                ) {
                    Icon(imageVector = Icons.Default.NotificationsActive, contentDescription = null, modifier = Modifier.size(16.dp))
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(text = "Vigilar", fontSize = 12.sp)
                }

                Button(
                    onClick = onBuyClick,
                    shape = RoundedCornerShape(10.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = RadarGreen, contentColor = DarkBackground),
                    modifier = Modifier.weight(1f)
                ) {
                    Icon(imageVector = Icons.Default.ShoppingCart, contentDescription = null, modifier = Modifier.size(16.dp))
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(text = "Ver Oferta", fontSize = 12.sp, fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}

package com.dealradar.app.ui.screens

import android.content.Context
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.EmojiEvents
import androidx.compose.material.icons.filled.Lightbulb
import androidx.compose.material.icons.filled.Savings
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.dealradar.app.data.api.DealRadarApiClient
import com.dealradar.app.data.model.UserSavingsResponse
import com.dealradar.app.ui.theme.*
import kotlinx.coroutines.launch
import java.text.NumberFormat
import java.util.Locale

@Composable
fun SavingsScreen() {
    val context = LocalContext.current
    val coroutineScope = rememberCoroutineScope()
    val prefs = context.getSharedPreferences("dealradar_prefs", Context.MODE_PRIVATE)
    val deviceId = prefs.getString("device_id", "demo_device_1") ?: "demo_device_1"

    var savingsData by remember { mutableStateOf<UserSavingsResponse?>(null) }
    var isLoading by remember { mutableStateOf(true) }

    val copFormatter = NumberFormat.getCurrencyInstance(Locale("es", "CO")).apply {
        maximumFractionDigits = 0
    }

    LaunchedEffect(Unit) {
        coroutineScope.launch {
            try {
                savingsData = DealRadarApiClient.api.getUserSavings(deviceId)
            } catch (e: Exception) {
                e.printStackTrace()
            } finally {
                isLoading = false
            }
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(DarkBackground)
            .padding(16.dp)
            .verticalScroll(rememberScrollState())
    ) {
        Text(
            text = "TU RADAR DE AHORRO",
            fontSize = 18.sp,
            fontWeight = FontWeight.Black,
            color = Color.White
        )
        Text(
            text = "Estadísticas y logros como cazador de ofertas",
            fontSize = 12.sp,
            color = TextMuted
        )

        Spacer(modifier = Modifier.height(16.dp))

        // Tarjeta Principal de Ahorro Acumulado
        Card(
            shape = RoundedCornerShape(18.dp),
            colors = CardDefaults.cardColors(containerColor = DarkSurface),
            modifier = Modifier.fillMaxWidth()
        ) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(
                        Brush.linearGradient(
                            colors = listOf(RadarGreenDark.copy(alpha = 0.25f), RadarGreen.copy(alpha = 0.15f))
                        )
                    )
                    .padding(20.dp)
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.fillMaxWidth()) {
                    Icon(
                        imageVector = Icons.Default.Savings,
                        contentDescription = null,
                        tint = RadarGreen,
                        modifier = Modifier.size(48.dp)
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text("Ahorro Potencial Acumulado", fontSize = 13.sp, color = TextMuted)
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = copFormatter.format(savingsData?.total_saved_cop ?: 0.0),
                        fontSize = 28.sp,
                        fontWeight = FontWeight.Black,
                        color = Color.White
                    )
                    Spacer(modifier = Modifier.height(10.dp))
                    Surface(
                        color = DarkCard,
                        shape = RoundedCornerShape(20.dp)
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            modifier = Modifier.padding(horizontal = 14.dp, vertical = 6.dp)
                        ) {
                            Icon(Icons.Default.EmojiEvents, contentDescription = null, tint = GoldStar, modifier = Modifier.size(16.dp))
                            Spacer(modifier = Modifier.width(6.dp))
                            Text(
                                text = savingsData?.rank ?: "Explorador Novato 🐣",
                                fontSize = 12.sp,
                                fontWeight = FontWeight.Bold,
                                color = LightText
                            )
                        }
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(20.dp))

        // Consejos para comprar en Colombia
        Text(
            text = "CONSEJOS DE CAZADOR EN COLOMBIA",
            fontSize = 14.sp,
            fontWeight = FontWeight.Bold,
            color = RadarGreen
        )

        Spacer(modifier = Modifier.height(10.dp))

        TipCard(
            title = "Evita ofertas infladas",
            desc = "Muchas tiendas suben los precios 2 semanas antes de CyberLunes para simular descuentos del 40%. Con DealRadar miras el histórico real."
        )

        Spacer(modifier = Modifier.height(8.dp))

        TipCard(
            title = "Envíos gratis en Amazon a Colombia",
            desc = "Recuerda que pedidos calificados en Amazon con valor mayor a $35 USD tienen envío internacional gratis a Colombia."
        )

        Spacer(modifier = Modifier.height(8.dp))

        TipCard(
            title = "Precios de Madrugón y Aniversarios",
            desc = "Alkosto y Éxito bajan tecnología los fines de semana en fechas de 'Trasnochón' o aniversarios. Deja tus alertas programadas."
        )
    }
}

@Composable
fun TipCard(title: String, desc: String) {
    Card(
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = DarkSurface),
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(modifier = Modifier.padding(14.dp), verticalAlignment = Alignment.Top) {
            Icon(Icons.Default.Lightbulb, contentDescription = null, tint = GoldStar, modifier = Modifier.size(20.dp))
            Spacer(modifier = Modifier.width(10.dp))
            Column {
                Text(text = title, fontSize = 13.sp, fontWeight = FontWeight.Bold, color = LightText)
                Spacer(modifier = Modifier.height(3.dp))
                Text(text = desc, fontSize = 12.sp, color = TextMuted, lineHeight = 16.sp)
            }
        }
    }
}

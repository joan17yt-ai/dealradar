package com.dealradar.app.ui.screens

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.NotificationsActive
import androidx.compose.material.icons.filled.OpenInBrowser
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.dealradar.app.data.api.DealRadarApiClient
import com.dealradar.app.data.model.AlertItem
import com.dealradar.app.ui.theme.*
import kotlinx.coroutines.launch
import java.text.NumberFormat
import java.util.Locale

@Composable
fun AlertsScreen() {
    val context = LocalContext.current
    val coroutineScope = rememberCoroutineScope()
    val prefs = context.getSharedPreferences("dealradar_prefs", Context.MODE_PRIVATE)
    val deviceId = prefs.getString("device_id", "demo_device_1") ?: "demo_device_1"

    var alerts by remember { mutableStateOf<List<AlertItem>>(emptyList()) }
    var isLoading by remember { mutableStateOf(true) }

    val copFormatter = NumberFormat.getCurrencyInstance(Locale("es", "CO")).apply {
        maximumFractionDigits = 0
    }

    fun loadAlerts() {
        isLoading = true
        coroutineScope.launch {
            try {
                val res = DealRadarApiClient.api.getUserAlerts(deviceId)
                alerts = res.alerts
            } catch (e: Exception) {
                e.printStackTrace()
            } finally {
                isLoading = false
            }
        }
    }

    LaunchedEffect(Unit) {
        loadAlerts()
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(DarkBackground)
            .padding(16.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text(
                    text = "MIS PRODUCTOS VIGILADOS",
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Black,
                    color = Color.White
                )
                Text(
                    text = "${alerts.size} alertas de precio activas",
                    fontSize = 12.sp,
                    color = TextMuted
                )
            }

            IconButton(onClick = { loadAlerts() }) {
                Icon(Icons.Default.NotificationsActive, contentDescription = "Refrescar", tint = RadarGreen)
            }
        }

        Spacer(modifier = Modifier.height(14.dp))

        if (isLoading) {
            Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                CircularProgressIndicator(color = RadarGreen)
            }
        } else if (alerts.isEmpty()) {
            Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("No tienes alertas activas.", color = LightText, fontSize = 16.sp, fontWeight = FontWeight.SemiBold)
                    Spacer(modifier = Modifier.height(6.dp))
                    Text(
                        "Busca un producto o escoge una ganga para comenzar a vigilar su precio.",
                        color = TextMuted,
                        fontSize = 13.sp,
                        textAlign = androidx.compose.ui.text.style.TextAlign.Center,
                        modifier = Modifier.padding(horizontal = 32.dp)
                    )
                }
            }
        } else {
            LazyColumn(
                verticalArrangement = Arrangement.spacedBy(12.dp),
                modifier = Modifier.fillMaxSize()
            ) {
                items(alerts) { alert ->
                    val isGoalReached = alert.current_best_price_cop != null &&
                            alert.current_best_price_cop <= alert.target_price_cop

                    Card(
                        shape = RoundedCornerShape(14.dp),
                        colors = CardDefaults.cardColors(containerColor = DarkSurface),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(modifier = Modifier.padding(14.dp)) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Surface(
                                    color = if (isGoalReached) RadarGreen.copy(alpha = 0.2f) else DarkCard,
                                    shape = RoundedCornerShape(6.dp)
                                ) {
                                    Text(
                                        text = if (isGoalReached) "🎯 ¡OFERTA ALCANZADA!" else "🔍 VIGILANDO PRECIO",
                                        fontSize = 11.sp,
                                        fontWeight = FontWeight.Bold,
                                        color = if (isGoalReached) RadarGreen else TextMuted,
                                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                                    )
                                }

                                IconButton(
                                    onClick = {
                                        coroutineScope.launch {
                                            try {
                                                DealRadarApiClient.api.deleteAlert(alert.id)
                                                loadAlerts()
                                                Toast.makeText(context, "Alerta eliminada", Toast.LENGTH_SHORT).show()
                                            } catch (e: Exception) {
                                                Toast.makeText(context, "Error al eliminar", Toast.LENGTH_SHORT).show()
                                            }
                                        }
                                    },
                                    modifier = Modifier.size(28.dp)
                                ) {
                                    Icon(
                                        Icons.Default.Delete,
                                        contentDescription = "Borrar",
                                        tint = DiscountRed,
                                        modifier = Modifier.size(18.dp)
                                    )
                                }
                            }

                            Spacer(modifier = Modifier.height(8.dp))

                            Text(
                                text = alert.product_title,
                                fontSize = 14.sp,
                                fontWeight = FontWeight.Bold,
                                color = LightText,
                                maxLines = 2
                            )

                            Spacer(modifier = Modifier.height(10.dp))

                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Column {
                                    Text("Tu precio objetivo:", fontSize = 11.sp, color = TextMuted)
                                    Text(
                                        copFormatter.format(alert.target_price_cop),
                                        fontSize = 14.sp,
                                        fontWeight = FontWeight.Bold,
                                        color = RadarGreen
                                    )
                                }

                                Column(horizontalAlignment = Alignment.End) {
                                    Text("Mejor precio actual:", fontSize = 11.sp, color = TextMuted)
                                    Text(
                                        if (alert.current_best_price_cop != null)
                                            copFormatter.format(alert.current_best_price_cop)
                                        else "Consultando...",
                                        fontSize = 14.sp,
                                        fontWeight = FontWeight.Bold,
                                        color = if (isGoalReached) RadarGreen else Color.White
                                    )
                                }
                            }

                            if (!alert.product_url.isNullOrEmpty()) {
                                Spacer(modifier = Modifier.height(10.dp))
                                OutlinedButton(
                                    onClick = {
                                        val intent = Intent(Intent.ACTION_VIEW, Uri.parse(alert.product_url))
                                        context.startActivity(intent)
                                    },
                                    shape = RoundedCornerShape(8.dp),
                                    colors = ButtonDefaults.outlinedButtonColors(contentColor = RadarGreen),
                                    modifier = Modifier.fillMaxWidth()
                                ) {
                                    Icon(Icons.Default.OpenInBrowser, contentDescription = null, modifier = Modifier.size(16.dp))
                                    Spacer(modifier = Modifier.width(6.dp))
                                    Text("Ver en ${alert.best_store ?: "Tienda"}", fontSize = 12.sp)
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

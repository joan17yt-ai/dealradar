package com.dealradar.app.ui.screens

import android.content.Context
import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Clear
import androidx.compose.material.icons.filled.NotificationsActive
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import com.dealradar.app.data.api.DealRadarApiClient
import com.dealradar.app.data.model.CreateAlertRequest
import com.dealradar.app.data.model.ScrapedItem
import com.dealradar.app.ui.theme.*
import kotlinx.coroutines.launch
import java.text.NumberFormat
import java.util.Locale

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SearchScreen() {
    val context = LocalContext.current
    val coroutineScope = rememberCoroutineScope()
    var searchQuery by remember { mutableStateOf("") }
    var results by remember { mutableStateOf<List<ScrapedItem>>(emptyList()) }
    var isLoading by remember { mutableStateOf(false) }

    // Dialog state
    var selectedItemForAlert by remember { mutableStateOf<ScrapedItem?>(null) }
    var targetPriceInput by remember { mutableStateOf("") }

    val prefs = context.getSharedPreferences("dealradar_prefs", Context.MODE_PRIVATE)
    val deviceId = prefs.getString("device_id", "demo_device_1") ?: "demo_device_1"

    val copFormatter = NumberFormat.getCurrencyInstance(Locale("es", "CO")).apply {
        maximumFractionDigits = 0
    }

    fun performSearch() {
        if (searchQuery.trim().isEmpty()) return
        isLoading = true
        coroutineScope.launch {
            try {
                val response = DealRadarApiClient.api.searchProducts(searchQuery.trim())
                results = response.results
            } catch (e: Exception) {
                Toast.makeText(context, "Error conectando con el servidor", Toast.LENGTH_SHORT).show()
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
    ) {
        Text(
            text = "BUSCADOR MULTITIENDA",
            fontSize = 18.sp,
            fontWeight = FontWeight.Black,
            color = Color.White
        )
        Text(
            text = "Compara precios en vivo en Mercado Libre, Alkosto, Éxito y Amazon",
            fontSize = 12.sp,
            color = TextMuted
        )

        Spacer(modifier = Modifier.height(14.dp))

        // Search Bar
        OutlinedTextField(
            value = searchQuery,
            onValueChange = { searchQuery = it },
            placeholder = { Text("Ej. iPhone 13, Portátil Lenovo, Nevera Haceb...", color = TextMuted) },
            leadingIcon = { Icon(Icons.Default.Search, contentDescription = null, tint = RadarGreen) },
            trailingIcon = {
                if (searchQuery.isNotEmpty()) {
                    IconButton(onClick = { searchQuery = "" }) {
                        Icon(Icons.Default.Clear, contentDescription = null, tint = TextMuted)
                    }
                }
            },
            singleLine = true,
            keyboardOptions = KeyboardOptions(imeAction = ImeAction.Search),
            keyboardActions = KeyboardActions(onSearch = { performSearch() }),
            shape = RoundedCornerShape(12.dp),
            colors = OutlinedTextFieldDefaults.colors(
                focusedContainerColor = DarkSurface,
                unfocusedContainerColor = DarkSurface,
                focusedBorderColor = RadarGreen,
                unfocusedBorderColor = DarkCard,
                focusedTextColor = LightText,
                unfocusedTextColor = LightText
            ),
            modifier = Modifier.fillMaxWidth()
        )

        Spacer(modifier = Modifier.height(10.dp))

        Button(
            onClick = { performSearch() },
            shape = RoundedCornerShape(10.dp),
            colors = ButtonDefaults.buttonColors(containerColor = RadarGreen, contentColor = DarkBackground),
            modifier = Modifier.fillMaxWidth()
        ) {
            Text(text = "Rastrear Precios en Colombia", fontWeight = FontWeight.Bold)
        }

        Spacer(modifier = Modifier.height(16.dp))

        if (isLoading) {
            Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    CircularProgressIndicator(color = RadarGreen)
                    Spacer(modifier = Modifier.height(12.dp))
                    Text("Consultando catálogos de tiendas...", color = TextMuted, fontSize = 13.sp)
                }
            }
        } else {
            LazyColumn(
                verticalArrangement = Arrangement.spacedBy(10.dp),
                modifier = Modifier.fillMaxSize()
            ) {
                items(results) { item ->
                    Card(
                        shape = RoundedCornerShape(12.dp),
                        colors = CardDefaults.cardColors(containerColor = DarkSurface),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(12.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            if (!item.image_url.isNullOrEmpty()) {
                                AsyncImage(
                                    model = item.image_url,
                                    contentDescription = item.title,
                                    contentScale = ContentScale.Fit,
                                    modifier = Modifier
                                        .size(60.dp)
                                        .clip(RoundedCornerShape(8.dp))
                                        .background(Color.White)
                                        .padding(2.dp)
                                )
                                Spacer(modifier = Modifier.width(10.dp))
                            }

                            Column(modifier = Modifier.weight(1f)) {
                                Text(
                                    text = item.store.uppercase(),
                                    fontSize = 10.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = RadarGreen
                                )
                                Text(
                                    text = item.title,
                                    fontSize = 13.sp,
                                    fontWeight = FontWeight.Medium,
                                    color = LightText,
                                    maxLines = 2
                                )
                                Text(
                                    text = copFormatter.format(item.price_cop),
                                    fontSize = 15.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = Color.White
                                )
                            }

                            IconButton(
                                onClick = {
                                    selectedItemForAlert = item
                                    targetPriceInput = ((item.price_cop * 0.9).toLong()).toString()
                                }
                            ) {
                                Icon(
                                    imageVector = Icons.Default.NotificationsActive,
                                    contentDescription = "Crear Alerta",
                                    tint = RadarGreen
                                )
                            }
                        }
                    }
                }
            }
        }
    }

    // Modal Crear Alerta
    if (selectedItemForAlert != null) {
        val item = selectedItemForAlert!!
        AlertDialog(
            onDismissRequest = { selectedItemForAlert = null },
            title = { Text("Activar Radar de Oferta", fontWeight = FontWeight.Bold, color = LightText) },
            text = {
                Column {
                    Text(text = item.title, fontSize = 13.sp, color = TextMuted, maxLines = 2)
                    Spacer(modifier = Modifier.height(10.dp))
                    Text(
                        text = "Precio actual: ${copFormatter.format(item.price_cop)} en ${item.store}",
                        fontSize = 13.sp,
                        color = Color.White
                    )
                    Spacer(modifier = Modifier.height(12.dp))
                    Text(
                        text = "¿A qué precio deseas que te avisemos? (COP):",
                        fontSize = 12.sp,
                        color = TextMuted
                    )
                    Spacer(modifier = Modifier.height(6.dp))
                    OutlinedTextField(
                        value = targetPriceInput,
                        onValueChange = { targetPriceInput = it },
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                        singleLine = true,
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedTextColor = LightText,
                            unfocusedTextColor = LightText
                        ),
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            },
            confirmButton = {
                Button(
                    onClick = {
                        val target = targetPriceInput.toDoubleOrNull()
                        if (target != null && target > 0) {
                            coroutineScope.launch {
                                try {
                                    DealRadarApiClient.api.createAlert(
                                        CreateAlertRequest(
                                            device_id = deviceId,
                                            product_title = item.title,
                                            query_keyword = item.title.take(60),
                                            target_price_cop = target,
                                            current_best_price_cop = item.price_cop,
                                            best_store = item.store,
                                            product_url = item.product_url,
                                            image_url = item.image_url
                                        )
                                    )
                                    Toast.makeText(context, "¡Radar activado con éxito!", Toast.LENGTH_SHORT).show()
                                } catch (e: Exception) {
                                    Toast.makeText(context, "Error guardando alerta", Toast.LENGTH_SHORT).show()
                                } finally {
                                    selectedItemForAlert = null
                                }
                            }
                        }
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = RadarGreen, contentColor = DarkBackground)
                ) {
                    Text("Confirmar Alerta")
                }
            },
            dismissButton = {
                TextButton(onClick = { selectedItemForAlert = null }) {
                    Text("Cancelar", color = TextMuted)
                }
            },
            containerColor = DarkSurface
        )
    }
}

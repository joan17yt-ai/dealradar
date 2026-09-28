package com.dealradar.app

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.EmojiEvents
import androidx.compose.material.icons.filled.NotificationsActive
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Whatshot
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.core.content.ContextCompat
import com.dealradar.app.data.api.DealRadarApiClient
import com.dealradar.app.data.model.CreateAlertRequest
import com.dealradar.app.data.model.DeviceRegisterRequest
import com.dealradar.app.ui.screens.AlertsScreen
import com.dealradar.app.ui.screens.DealsFeedScreen
import com.dealradar.app.ui.screens.SavingsScreen
import com.dealradar.app.ui.screens.SearchScreen
import com.dealradar.app.ui.theme.DarkCard
import com.dealradar.app.ui.theme.DarkSurface
import com.dealradar.app.ui.theme.DealRadarTheme
import com.dealradar.app.ui.theme.RadarGreen
import com.dealradar.app.ui.theme.TextMuted
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.util.UUID

sealed class NavigationTab(val route: String, val title: String, val icon: ImageVector) {
    object Feed : NavigationTab("feed", "Radar", Icons.Default.Whatshot)
    object Search : NavigationTab("search", "Buscar", Icons.Default.Search)
    object Alerts : NavigationTab("alerts", "Mis Alertas", Icons.Default.NotificationsActive)
    object Savings : NavigationTab("savings", "Mi Ahorro", Icons.Default.EmojiEvents)
}

class MainActivity : ComponentActivity() {

    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted: Boolean ->
        if (!isGranted) {
            Toast.makeText(this, "Activa las notificaciones para recibir alertas cuando bajen los precios", Toast.LENGTH_LONG).show()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Registrar o recuperar ID único del dispositivo
        val prefs = getSharedPreferences("dealradar_prefs", Context.MODE_PRIVATE)
        var deviceId = prefs.getString("device_id", null)
        if (deviceId == null) {
            deviceId = UUID.randomUUID().toString()
            prefs.edit().putString("device_id", deviceId).apply()
        }

        // Registrar dispositivo con el backend
        val finalDeviceId = deviceId
        CoroutineScope(Dispatchers.IO).launch {
            try {
                DealRadarApiClient.api.registerDevice(DeviceRegisterRequest(deviceId = finalDeviceId))
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }

        // Solicitar permisos de notificación en Android 13+
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                requestPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
            }
        }

        setContent {
            DealRadarTheme {
                var currentTab by remember { mutableStateOf<NavigationTab>(NavigationTab.Feed) }
                val coroutineScope = rememberCoroutineScope()

                Scaffold(
                    bottomBar = {
                        NavigationBar(
                            containerColor = DarkSurface,
                            contentColor = RadarGreen
                        ) {
                            val items = listOf(
                                NavigationTab.Feed,
                                NavigationTab.Search,
                                NavigationTab.Alerts,
                                NavigationTab.Savings
                            )
                            items.forEach { tab ->
                                val selected = currentTab == tab
                                NavigationBarItem(
                                    selected = selected,
                                    onClick = { currentTab = tab },
                                    icon = {
                                        Icon(
                                            imageVector = tab.icon,
                                            contentDescription = tab.title,
                                            tint = if (selected) RadarGreen else TextMuted
                                        )
                                    },
                                    label = {
                                        Text(
                                            text = tab.title,
                                            color = if (selected) RadarGreen else TextMuted
                                        )
                                    },
                                    colors = NavigationBarItemDefaults.colors(
                                        indicatorColor = DarkCard
                                    )
                                )
                            }
                        }
                    }
                ) { innerPadding ->
                    Surface(modifier = Modifier.padding(innerPadding)) {
                        when (currentTab) {
                            NavigationTab.Feed -> DealsFeedScreen(
                                onTrackDealClick = { deal ->
                                    coroutineScope.launch {
                                        try {
                                            DealRadarApiClient.api.createAlert(
                                                CreateAlertRequest(
                                                    device_id = finalDeviceId,
                                                    product_title = deal.title,
                                                    query_keyword = deal.title.take(60),
                                                    category = deal.category,
                                                    target_price_cop = deal.current_price_cop * 0.95,
                                                    current_best_price_cop = deal.current_price_cop,
                                                    best_store = deal.store,
                                                    product_url = deal.product_url,
                                                    image_url = deal.image_url
                                                )
                                            )
                                            Toast.makeText(this@MainActivity, "¡Alerta agregada para ${deal.title}!", Toast.LENGTH_SHORT).show()
                                            currentTab = NavigationTab.Alerts
                                        } catch (e: Exception) {
                                            Toast.makeText(this@MainActivity, "Error al crear la alerta", Toast.LENGTH_SHORT).show()
                                        }
                                    }
                                }
                            )
                            NavigationTab.Search -> SearchScreen()
                            NavigationTab.Alerts -> AlertsScreen()
                            NavigationTab.Savings -> SavingsScreen()
                        }
                    }
                }
            }
        }
    }
}

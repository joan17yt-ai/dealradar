package com.dealradar.app.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.*
import androidx.compose.runtime.Composable

private val DarkColorScheme = darkColorScheme(
    primary = RadarGreen,
    onPrimary = DarkBackground,
    secondary = RadarGreenDark,
    background = DarkBackground,
    surface = DarkSurface,
    surfaceVariant = DarkCard,
    onBackground = LightText,
    onSurface = LightText
)

@Composable
fun DealRadarTheme(
    darkTheme: Boolean = true, // Modo oscuro por defecto para estilo moderno/gamer/radar
    content: @Composable () -> Unit
) {
    MaterialTheme(
        colorScheme = DarkColorScheme,
        content = content
    )
}

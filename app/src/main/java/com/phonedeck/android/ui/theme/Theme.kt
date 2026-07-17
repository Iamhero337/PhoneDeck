package com.phonedeck.android.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val DarkColorScheme = darkColorScheme(
    primary = Color(0xFF4A90D9),
    secondary = Color(0xFF7B2FBE),
    surface = Color(0xFF1A1A2E),
    background = Color(0xFF0F0F1A),
    onPrimary = Color.White,
    onSecondary = Color.White,
    onSurface = Color.White,
    onBackground = Color.White,
    surfaceVariant = Color(0xFF2A2A3E),
    onSurfaceVariant = Color(0xFF8888AA),
    outline = Color(0xFF3A3A4E),
)

@Composable
fun PhoneDeckTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = DarkColorScheme,
        content = content
    )
}

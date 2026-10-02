package com.phonedeck.android.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.*
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.phonedeck.android.data.models.Page
import com.phonedeck.android.data.models.Tile

@Composable
fun TileGrid(
    page: Page,
    connected: Boolean,
    onTileTap: (Tile) -> Unit,
    modifier: Modifier = Modifier
) {
    LazyVerticalGrid(
        columns = GridCells.Fixed(2),
        contentPadding = PaddingValues(12.dp),
        horizontalArrangement = Arrangement.spacedBy(12.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
        modifier = modifier.fillMaxSize()
    ) {
        items(page.tiles, key = { it.id }) { tile ->
            TileButton(
                tile = tile,
                enabled = connected,
                onClick = { onTileTap(tile) }
            )
        }
    }
}

@Composable
private fun TileButton(
    tile: Tile,
    enabled: Boolean,
    onClick: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .aspectRatio(1.3f)
            .clickable(enabled = enabled, onClick = onClick),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = Color(tile.color),
            disabledContainerColor = Color(0xFF1A1A2E)
        ),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(12.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Icon(
                imageVector = getIconForTile(tile.icon),
                contentDescription = tile.label,
                tint = if (enabled) Color(tile.iconColor) else Color(0xFF555566),
                modifier = Modifier.size(32.dp)
            )
            Spacer(modifier = Modifier.height(6.dp))
            Text(
                text = tile.label,
                color = if (enabled) Color.White else Color(0xFF555566),
                fontSize = 13.sp,
                fontWeight = FontWeight.Medium,
                textAlign = TextAlign.Center,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis
            )
        }
    }
}

@Composable
fun PageIndicator(
    currentPage: Int,
    pages: List<Page>,
    onPageSelected: (Int) -> Unit,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 8.dp)
            .horizontalScroll(rememberScrollState()),
        horizontalArrangement = Arrangement.Center,
        verticalAlignment = Alignment.CenterVertically
    ) {
        pages.forEachIndexed { index, page ->
            val selected = index == currentPage
            TextButton(
                onClick = { onPageSelected(index) },
                modifier = Modifier.padding(horizontal = 4.dp)
            ) {
                Text(
                    text = page.name,
                    fontSize = 14.sp,
                    fontWeight = if (selected) FontWeight.Bold else FontWeight.Normal,
                    color = if (selected) Color(0xFF4A90D9) else Color(0xFF8888AA)
                )
            }
        }
    }
}

@Composable
fun ConnectionBadge(
    connected: Boolean,
    label: String,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier.padding(horizontal = 16.dp, vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.Center
    ) {
        Box(
            modifier = Modifier
                .size(8.dp)
                .background(
                    color = if (connected) Color(0xFF4CAF50) else Color(0xFFE53935),
                    shape = RoundedCornerShape(4.dp)
                )
        )
        Spacer(modifier = Modifier.width(8.dp))
        Text(
            text = label,
            fontSize = 12.sp,
            color = Color(0xFF8888AA)
        )
    }
}

private fun getIconForTile(icon: String) = when (icon) {
    "code" -> Icons.Default.Code
    "terminal" -> Icons.Default.Terminal
    "chrome", "public" -> Icons.Default.Public
    "music_note" -> Icons.Default.MusicNote
    "draw" -> Icons.Default.Draw
    "image" -> Icons.Default.Image
    "brush" -> Icons.Default.Brush
    "visibility" -> Icons.Default.Visibility
    "volume_up" -> Icons.AutoMirrored.Filled.VolumeUp
    "volume_down" -> Icons.AutoMirrored.Filled.VolumeDown
    "volume_off" -> Icons.AutoMirrored.Filled.VolumeOff
    "play_arrow" -> Icons.Default.PlayArrow
    "skip_next" -> Icons.Default.SkipNext
    "skip_previous" -> Icons.Default.SkipPrevious
    "brightness_high" -> Icons.Default.BrightnessHigh
    "brightness_low" -> Icons.Default.BrightnessLow
    "screenshot" -> Icons.Default.Screenshot
    "lock" -> Icons.Default.Lock
    "bedtime" -> Icons.Default.Bedtime
    "play_pause" -> Icons.Default.Pause
    "next" -> Icons.Default.SkipNext
    "prev" -> Icons.Default.SkipPrevious
    "brightness_up" -> Icons.Default.BrightnessHigh
    "brightness_down" -> Icons.Default.BrightnessLow
    "restart" -> Icons.Default.RestartAlt
    "shutdown" -> Icons.Default.PowerSettingsNew
    "logout" -> Icons.AutoMirrored.Filled.ExitToApp
    "hibernate" -> Icons.Default.Bedtime
    "smart_display" -> Icons.Default.SmartDisplay
    "search" -> Icons.Default.Search
    "forum" -> Icons.Default.Forum
    "chat" -> Icons.AutoMirrored.Filled.Chat
    "help" -> Icons.AutoMirrored.Filled.Help
    "menu_book" -> Icons.AutoMirrored.Filled.MenuBook
    "cloud" -> Icons.Default.Cloud
    "api" -> Icons.Default.Api
    "videocam" -> Icons.Default.Videocam
    "article" -> Icons.AutoMirrored.Filled.Article
    "folder" -> Icons.Default.Folder
    "mail" -> Icons.Default.Mail
    "calendar_month" -> Icons.Default.CalendarMonth
    "settings" -> Icons.Default.Settings
    "home" -> Icons.Default.Home
    "desktop_windows" -> Icons.Default.DesktopWindows
    "sports_esports" -> Icons.Default.SportsEsports
    "photo_camera" -> Icons.Default.PhotoCamera
    "mic" -> Icons.Default.Mic
    "mic_off" -> Icons.Default.MicOff
    "headphones" -> Icons.Default.Headphones
    "keyboard" -> Icons.Default.Keyboard
    "wifi" -> Icons.Default.Wifi
    "bluetooth" -> Icons.Default.Bluetooth
    "dark_mode" -> Icons.Default.DarkMode
    "light_mode" -> Icons.Default.LightMode
    "stop" -> Icons.Default.Stop
    "fast_forward" -> Icons.Default.FastForward
    "fast_rewind" -> Icons.Default.FastRewind
    "shuffle" -> Icons.Default.Shuffle
    "repeat" -> Icons.Default.Repeat
    "download" -> Icons.Default.Download
    "upload" -> Icons.Default.Upload
    "refresh" -> Icons.Default.Refresh
    "content_copy" -> Icons.Default.ContentCopy
    "content_paste" -> Icons.Default.ContentPaste
    "edit_note" -> Icons.Default.EditNote
    "calculate" -> Icons.Default.Calculate
    "timer" -> Icons.Default.Timer
    "notifications" -> Icons.Default.Notifications
    "shopping_cart" -> Icons.Default.ShoppingCart
    "star" -> Icons.Default.Star
    "favorite" -> Icons.Default.Favorite
    "bolt" -> Icons.Default.Bolt
    "rocket_launch" -> Icons.Default.RocketLaunch
    else -> Icons.Default.Apps
}
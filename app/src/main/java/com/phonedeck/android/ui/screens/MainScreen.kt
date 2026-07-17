package com.phonedeck.android.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.phonedeck.android.data.models.Tile
import com.phonedeck.android.ui.components.ConnectionBadge
import com.phonedeck.android.ui.components.PageIndicator
import com.phonedeck.android.ui.components.TileGrid
import com.phonedeck.android.viewmodel.MainViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainScreen(viewModel: MainViewModel) {
    val pages by viewModel.pages.collectAsState()
    val currentPageIndex by viewModel.currentPageIndex.collectAsState()
    val connectionStatus by viewModel.connectionStatus.collectAsState()
    val connected by viewModel.connected.collectAsState()
    val discoveredServerIp by viewModel.discoveredServerIp.collectAsState()

    var showConnectDialog by remember { mutableStateOf(false) }
    var serverIp by remember { mutableStateOf("") }
    
    // Auto-fill IP when discovered
    LaunchedEffect(discoveredServerIp) {
        if (discoveredServerIp.isNotBlank() && serverIp.isBlank()) {
            serverIp = discoveredServerIp
        }
    }
    
    var showAddSiteDialog by remember { mutableStateOf(false) }
    var newSiteName by remember { mutableStateOf("") }
    var newSiteUrl by remember { mutableStateOf("") }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF0F0F1A))
    ) {
        TopAppBar(
            title = {
                Text(
                    "PhoneDeck",
                    fontWeight = FontWeight.Bold,
                    fontSize = 22.sp
                )
            },
            actions = {
                if (currentPageIndex < pages.size && pages[currentPageIndex].id == "top_sites") {
                    IconButton(onClick = { showAddSiteDialog = true }) {
                        Icon(
                            Icons.Default.Add,
                            contentDescription = "Add Site",
                            tint = Color(0xFF4A90D9)
                        )
                    }
                }
                if (!connected) {
                    IconButton(onClick = { showConnectDialog = true }) {
                        Icon(
                            Icons.Default.CastConnected,
                            contentDescription = "Connect",
                            tint = Color(0xFF4A90D9)
                        )
                    }
                } else {
                    IconButton(onClick = { showConnectDialog = true }) {
                        Icon(
                            Icons.Default.Settings,
                            contentDescription = "Settings",
                            tint = Color(0xFF8888AA)
                        )
                    }
                }
            },
            colors = TopAppBarDefaults.topAppBarColors(
                containerColor = Color(0xFF0F0F1A),
                titleContentColor = Color.White
            )
        )

        if (pages.isNotEmpty() && currentPageIndex < pages.size) {
            val currentPage = pages[currentPageIndex]

            PageIndicator(
                pageCount = pages.size,
                currentPage = currentPageIndex,
                pages = pages,
                onPageSelected = { viewModel.selectPage(it) }
            )

            ConnectionBadge(
                connected = connected,
                label = connectionStatus
            )

            Box(modifier = Modifier.weight(1f)) {
                TileGrid(
                    page = currentPage,
                    connected = connected,
                    onTileTap = { tile ->
                        viewModel.sendCommand(tile.command)
                    }
                )

                if (!connected) {
                    Box(
                        modifier = Modifier.fillMaxSize(),
                        contentAlignment = Alignment.Center
                    ) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Icon(
                                Icons.Default.WifiOff,
                                contentDescription = null,
                                tint = Color(0xFF555566),
                                modifier = Modifier.size(48.dp)
                            )
                            Spacer(modifier = Modifier.height(12.dp))
                            Text(
                                "No desktop connected",
                                color = Color(0xFF8888AA),
                                fontSize = 16.sp
                            )
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                "Tap the connect icon to connect",
                                color = Color(0xFF555566),
                                fontSize = 13.sp
                            )
                        }
                    }
                }
            }

            Text(
                text = "Built with ❤️ by @iamhero337",
                color = Color(0xFF555566),
                fontSize = 12.sp,
                textAlign = TextAlign.Center,
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 16.dp)
            )
        }
    }

    if (showConnectDialog) {
        AlertDialog(
            onDismissRequest = { showConnectDialog = false },
            title = {
                Text(
                    if (connected) "Connected" else "Connect to Desktop",
                    fontWeight = FontWeight.Bold
                )
            },
            text = {
                Column {
                    if (connected) {
                        Text("Connected to server at $connectionStatus")
                        Spacer(modifier = Modifier.height(12.dp))
                        TextButton(onClick = {
                            serverIp = ""
                            showConnectDialog = false
                        }) {
                            Text("Disconnect", color = Color(0xFFE53935))
                        }
                    } else {
                        OutlinedTextField(
                            value = serverIp,
                            onValueChange = { serverIp = it },
                            label = { Text("Server IP") },
                            placeholder = { Text("e.g. 192.168.1.100") },
                            singleLine = true,
                            modifier = Modifier.fillMaxWidth(),
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedBorderColor = Color(0xFF4A90D9),
                                unfocusedBorderColor = Color(0xFF3A3A4E),
                                focusedLabelColor = Color(0xFF4A90D9),
                                unfocusedLabelColor = Color(0xFF8888AA),
                                cursorColor = Color(0xFF4A90D9),
                                focusedTextColor = Color.White,
                                unfocusedTextColor = Color.White
                            )
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        if (discoveredServerIp.isNotBlank() && serverIp == discoveredServerIp) {
                            Text(
                                "✅ Laptop auto-detected! Click connect.",
                                color = Color(0xFF4CAF50),
                                fontSize = 13.sp
                            )
                        } else if (discoveredServerIp.isNotBlank()) {
                            Text(
                                "Found server at: $discoveredServerIp",
                                color = Color(0xFF4A90D9),
                                fontSize = 13.sp
                            )
                        } else {
                            Text(
                                "Searching for laptop on WiFi...",
                                color = Color(0xFF8888AA),
                                fontSize = 12.sp
                            )
                        }
                    }
                }
            },
            confirmButton = {
                if (!connected) {
                    TextButton(
                        onClick = {
                            if (serverIp.isNotBlank()) {
                                viewModel.connect(serverIp.trim())
                                showConnectDialog = false
                            }
                        },
                        enabled = serverIp.isNotBlank()
                    ) {
                        Text("Connect", color = Color(0xFF4A90D9))
                    }
                } else {
                    TextButton(onClick = { showConnectDialog = false }) {
                        Text("Close")
                    }
                }
            },
            dismissButton = {
                TextButton(onClick = { showConnectDialog = false }) {
                    Text("Cancel", color = Color(0xFF8888AA))
                }
            },
            containerColor = Color(0xFF1A1A2E),
            titleContentColor = Color.White,
            textContentColor = Color.White
        )
    }

    if (showAddSiteDialog) {
        AlertDialog(
            onDismissRequest = { showAddSiteDialog = false },
            title = { Text("Add Top Site", fontWeight = FontWeight.Bold) },
            text = {
                Column {
                    OutlinedTextField(
                        value = newSiteName,
                        onValueChange = { newSiteName = it },
                        label = { Text("Site Name") },
                        placeholder = { Text("e.g. YouTube") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth(),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = Color(0xFF4A90D9),
                            unfocusedBorderColor = Color(0xFF3A3A4E),
                            focusedLabelColor = Color(0xFF4A90D9),
                            unfocusedLabelColor = Color(0xFF8888AA),
                            cursorColor = Color(0xFF4A90D9),
                            focusedTextColor = Color.White,
                            unfocusedTextColor = Color.White
                        )
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    OutlinedTextField(
                        value = newSiteUrl,
                        onValueChange = { newSiteUrl = it },
                        label = { Text("URL") },
                        placeholder = { Text("e.g. youtube.com") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth(),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = Color(0xFF4A90D9),
                            unfocusedBorderColor = Color(0xFF3A3A4E),
                            focusedLabelColor = Color(0xFF4A90D9),
                            unfocusedLabelColor = Color(0xFF8888AA),
                            cursorColor = Color(0xFF4A90D9),
                            focusedTextColor = Color.White,
                            unfocusedTextColor = Color.White
                        )
                    )
                }
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        if (newSiteName.isNotBlank() && newSiteUrl.isNotBlank()) {
                            viewModel.addTopSite(newSiteName.trim(), newSiteUrl.trim())
                            newSiteName = ""
                            newSiteUrl = ""
                            showAddSiteDialog = false
                        }
                    },
                    enabled = newSiteName.isNotBlank() && newSiteUrl.isNotBlank()
                ) {
                    Text("Add", color = Color(0xFF4A90D9))
                }
            },
            dismissButton = {
                TextButton(onClick = { showAddSiteDialog = false }) {
                    Text("Cancel", color = Color(0xFF8888AA))
                }
            },
            containerColor = Color(0xFF1A1A2E),
            titleContentColor = Color.White,
            textContentColor = Color.White
        )
    }
}

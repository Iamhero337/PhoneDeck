package com.phonedeck.android.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
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
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainScreen(viewModel: MainViewModel) {
    val pages by viewModel.pages.collectAsState()
    val currentPageIndex by viewModel.currentPageIndex.collectAsState()
    val connectionStatus by viewModel.connectionStatus.collectAsState()
    val connected by viewModel.connected.collectAsState()
    val discoveredServerIp by viewModel.discoveredServerIp.collectAsState()
    val lastCommandResult by viewModel.lastCommandResult.collectAsState()

    var showConnectDialog by remember { mutableStateOf(false) }
    var serverIp by remember { mutableStateOf("") }
    var showSettings by remember { mutableStateOf(false) }

    var showAddSiteDialog by remember { mutableStateOf(false) }
    var newSiteName by remember { mutableStateOf("") }
    var newSiteUrl by remember { mutableStateOf("") }

    val snackbarHostState = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()

    LaunchedEffect(lastCommandResult) {
        lastCommandResult?.let {
            scope.launch {
                snackbarHostState.showSnackbar(
                    message = it,
                    duration = SnackbarDuration.Short
                )
            }
            viewModel.clearCommandResult()
        }
    }

    Scaffold(
        snackbarHost = { SnackbarHost(snackbarHostState) },
        containerColor = Color(0xFF0F0F1A)
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .background(Color(0xFF0F0F1A))
                .padding(paddingValues)
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
                    IconButton(onClick = { showSettings = true }) {
                        Icon(
                            Icons.Default.Settings,
                            contentDescription = "Settings",
                            tint = if (connected) Color(0xFF4A90D9) else Color(0xFF8888AA)
                        )
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
                                Spacer(modifier = Modifier.height(16.dp))
                                FilledTonalButton(
                                    onClick = { showConnectDialog = true },
                                    shape = RoundedCornerShape(12.dp)
                                ) {
                                    Icon(Icons.Default.Wifi, contentDescription = null, modifier = Modifier.size(18.dp))
                                    Spacer(modifier = Modifier.width(8.dp))
                                    Text("Connect to Desktop")
                                }
                            }
                        }
                    }
                }

                Text(
                    text = "Built with \u2764 by @iamhero337",
                    color = Color(0xFF555566),
                    fontSize = 12.sp,
                    textAlign = TextAlign.Center,
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(bottom = 16.dp)
                )
            }
        }
    }

    if (showConnectDialog) {
        ConnectDialog(
            onDismiss = { showConnectDialog = false },
            connected = connected,
            connectionStatus = connectionStatus,
            discoveredServerIp = discoveredServerIp,
            serverIp = serverIp,
            onServerIpChange = { serverIp = it },
            onConnect = {
                if (serverIp.isNotBlank()) {
                    viewModel.connect(serverIp.trim())
                    showConnectDialog = false
                }
            },
            onDisconnect = {
                viewModel.disconnect()
                serverIp = ""
                showConnectDialog = false
            }
        )
    }

    if (showAddSiteDialog) {
        AddSiteDialog(
            onDismiss = { showAddSiteDialog = false; newSiteName = ""; newSiteUrl = "" },
            name = newSiteName,
            onNameChange = { newSiteName = it },
            url = newSiteUrl,
            onUrlChange = { newSiteUrl = it },
            onAdd = {
                if (newSiteName.isNotBlank() && newSiteUrl.isNotBlank()) {
                    viewModel.addTopSite(newSiteName.trim(), newSiteUrl.trim())
                    newSiteName = ""
                    newSiteUrl = ""
                    showAddSiteDialog = false
                }
            }
        )
    }

    if (showSettings) {
        SettingsScreen(
            viewModel = viewModel,
            onBack = { showSettings = false }
        )
    }
}

@Composable
fun ConnectDialog(
    onDismiss: () -> Unit,
    connected: Boolean,
    connectionStatus: String,
    discoveredServerIp: String,
    serverIp: String,
    onServerIpChange: (String) -> Unit,
    onConnect: () -> Unit,
    onDisconnect: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(if (connected) "Connected" else "Connect to Desktop", fontWeight = FontWeight.Bold) },
        text = {
            Column {
                if (connected) {
                    Text("Connected to server at $connectionStatus")
                    Spacer(modifier = Modifier.height(8.dp))
                    Text("Host: $discoveredServerIp", color = Color(0xFF8888AA), fontSize = 13.sp)
                    Spacer(modifier = Modifier.height(12.dp))
                    TextButton(onClick = onDisconnect) { Text("Disconnect", color = Color(0xFFE53935)) }
                } else {
                    OutlinedTextField(
                        value = serverIp,
                        onValueChange = onServerIpChange,
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
                        Text("\u2705 Laptop auto-detected! Click connect.", color = Color(0xFF4CAF50), fontSize = 13.sp)
                    } else if (discoveredServerIp.isNotBlank()) {
                        Text("Found server at: $discoveredServerIp", color = Color(0xFF4A90D9), fontSize = 13.sp)
                    } else {
                        Text("Searching for laptop on WiFi...", color = Color(0xFF8888AA), fontSize = 12.sp)
                    }
                }
            }
        },
        confirmButton = {
            if (!connected) {
                TextButton(onClick = onConnect, enabled = serverIp.isNotBlank()) {
                    Text("Connect", color = Color(0xFF4A90D9))
                }
            }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancel", color = Color(0xFF8888AA)) } },
        containerColor = Color(0xFF1A1A2E),
        titleContentColor = Color.White,
        textContentColor = Color.White
    )
}

@Composable
fun AddSiteDialog(
    onDismiss: () -> Unit,
    name: String,
    onNameChange: (String) -> Unit,
    url: String,
    onUrlChange: (String) -> Unit,
    onAdd: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Add Top Site", fontWeight = FontWeight.Bold) },
        text = {
            Column {
                OutlinedTextField(
                    value = name,
                    onValueChange = onNameChange,
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
                    value = url,
                    onValueChange = onUrlChange,
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
        confirmButton = { TextButton(onClick = onAdd, enabled = name.isNotBlank() && url.isNotBlank()) { Text("Add", color = Color(0xFF4A90D9)) } },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancel", color = Color(0xFF8888AA)) } },
        containerColor = Color(0xFF1A1A2E),
        titleContentColor = Color.White,
        textContentColor = Color.White
    )
}
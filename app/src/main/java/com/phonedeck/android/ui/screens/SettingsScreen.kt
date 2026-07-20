package com.phonedeck.android.ui.screens

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
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
import com.phonedeck.android.data.models.Page
import com.phonedeck.android.data.models.Tile
import com.phonedeck.android.data.repository.ConfigRepository
import com.phonedeck.android.data.repository.CrashLogger
import com.phonedeck.android.ui.theme.PhoneDeckTheme
import com.phonedeck.android.viewmodel.MainViewModel
import kotlinx.coroutines.launch
import java.util.UUID

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    viewModel: MainViewModel,
    onBack: () -> Unit
) {
    val pages by viewModel.pages.collectAsState()
    val connected by viewModel.connected.collectAsState()
    val discoveredServerIp by viewModel.discoveredServerIp.collectAsState()
    val connectionStatus by viewModel.connectionStatus.collectAsState()
    val hapticFeedback = remember { mutableStateOf(ConfigRepository.getHapticFeedback()) }
    val autoConnect = remember { mutableStateOf(ConfigRepository.getAutoConnect()) }
    val serverPort = remember { mutableStateOf(ConfigRepository.getServerPort()) }
    val darkMode = remember { mutableStateOf(true) }
    var showExportDialog by remember { mutableStateOf(false) }
    var showImportDialog by remember { mutableStateOf(false) }
    var importJson by remember { mutableStateOf("") }
    var exportJson by remember { mutableStateOf("") }
    var showResetConfirm by remember { mutableStateOf(false) }
    var showAddPageDialog by remember { mutableStateOf(false) }
    var newPageName by remember { mutableStateOf("") }
    var newPageIcon by remember { mutableStateOf("apps") }
    var showDebugDialog by remember { mutableStateOf(false) }
    val lastCrash = remember { mutableStateOf(CrashLogger.getLastCrash()) }

    val snackbarHostState = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()

    val showSnackbar = { msg: String ->
        scope.launch { snackbarHostState.showSnackbar(msg) }
    }

    LaunchedEffect(connected) {
        if (connected) {
            showSnackbar("Connected successfully!")
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
                .verticalScroll(rememberScrollState())
        ) {
            TopAppBar(
                title = { Text("Settings", fontWeight = FontWeight.Bold, fontSize = 22.sp, color = Color.White) },
                navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, "Back", tint = Color.White) } },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Color(0xFF0F0F1A), titleContentColor = Color.White)
            )

            Spacer(modifier = Modifier.height(16.dp))

            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = Color(0xFF1A1A2E)),
                shape = RoundedCornerShape(16.dp)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text("Connection", style = MaterialTheme.typography.titleMedium, color = Color(0xFF4A90D9))
                    Spacer(modifier = Modifier.height(16.dp))

                    SettingsRow(
                        title = "Auto-connect on launch",
                        subtitle = "Automatically connect to discovered server",
                        trailing = { Switch(checked = autoConnect.value, onCheckedChange = { autoConnect.value = it; ConfigRepository.setAutoConnect(it) }) }
                    )
                    Divider(color = Color(0xFF3A3A4E))
                    SettingsRow(
                        title = "Server Port",
                        subtitle = "Port the desktop server listens on (default 9090)",
                        trailing = {
                            OutlinedTextField(
                                value = serverPort.value.toString(),
                                onValueChange = { v -> v.toIntOrNull()?.let { serverPort.value = it; ConfigRepository.setServerPort(it) } },
                                singleLine = true,
                                modifier = Modifier.width(100.dp),
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
                    )
                    Divider(color = Color(0xFF3A3A4E))

                    Text("Manual Connect", color = Color.White, fontSize = 16.sp, fontWeight = FontWeight.Medium, modifier = Modifier.padding(top = 12.dp))
                    Spacer(modifier = Modifier.height(2.dp))
                    Text("Connect/disconnect from desktop server", color = Color(0xFF8888AA), fontSize = 13.sp)
                    Spacer(modifier = Modifier.height(12.dp))

                    if (connected) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column {
                                Text("Connected", color = Color(0xFF4CAF50), fontSize = 14.sp, fontWeight = FontWeight.Medium)
                                Text(connectionStatus, color = Color(0xFF8888AA), fontSize = 12.sp)
                            }
                            Button(
                                onClick = { viewModel.disconnect() },
                                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFE53935)),
                                shape = RoundedCornerShape(8.dp)
                            ) {
                                Text("Disconnect", color = Color.White)
                            }
                        }
                    } else {
                        var manualIp by remember { mutableStateOf("") }
                        if (discoveredServerIp.isNotBlank()) {
                            Row(
                                modifier = Modifier.fillMaxWidth().padding(bottom = 8.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Icon(Icons.Default.Wifi, contentDescription = null, tint = Color(0xFF4A90D9), modifier = Modifier.size(16.dp))
                                Spacer(modifier = Modifier.width(6.dp))
                                Text("Auto-detected: $discoveredServerIp", color = Color(0xFF4A90D9), fontSize = 13.sp)
                            }
                        }
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            OutlinedTextField(
                                value = manualIp,
                                onValueChange = { manualIp = it },
                                label = { Text("IP Address") },
                                placeholder = { Text("192.168.x.x") },
                                singleLine = true,
                                modifier = Modifier.weight(1f),
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
                            Button(
                                onClick = { if (manualIp.isNotBlank()) viewModel.connect(manualIp.trim()) },
                                enabled = manualIp.isNotBlank(),
                                shape = RoundedCornerShape(8.dp)
                            ) {
                                Text("Connect")
                            }
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = Color(0xFF1A1A2E)),
                shape = RoundedCornerShape(16.dp)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text("Feedback", style = MaterialTheme.typography.titleMedium, color = Color(0xFF4A90D9))
                    Spacer(modifier = Modifier.height(16.dp))

                    SettingsRow(
                        title = "Haptic Feedback",
                        subtitle = "Vibrate when tapping tiles",
                        trailing = { Switch(checked = hapticFeedback.value, onCheckedChange = { hapticFeedback.value = it; ConfigRepository.setHapticFeedback(it) }) }
                    )
                    Divider(color = Color(0xFF3A3A4E))
                    SettingsRow(
                        title = "Dark Mode",
                        subtitle = "Use dark theme (always on for now)",
                        trailing = { Switch(checked = darkMode.value, onCheckedChange = { darkMode.value = it }) }
                    )
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = Color(0xFF1A1A2E)),
                shape = RoundedCornerShape(16.dp)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text("Pages & Tiles", style = MaterialTheme.typography.titleMedium, color = Color(0xFF4A90D9))
                    Spacer(modifier = Modifier.height(16.dp))

                    SettingsRow(
                        title = "Add Custom Page",
                        subtitle = "Create a new page with your own tiles",
                        trailing = {
                            TextButton(onClick = { showAddPageDialog = true }) {
                                Text("Add", color = Color(0xFF4A90D9))
                            }
                        }
                    )
                    Divider(color = Color(0xFF3A3A4E))
                    SettingsRow(
                        title = "Reset to Defaults",
                        subtitle = "Remove all custom pages and top sites",
                        trailing = {
                            TextButton(onClick = { showResetConfirm = true }, colors = ButtonDefaults.textButtonColors(contentColor = Color(0xFFE53935))) {
                                Text("Reset", color = Color(0xFFE53935))
                            }
                        }
                    )
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = Color(0xFF1A1A2E)),
                shape = RoundedCornerShape(16.dp)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text("Backup & Restore", style = MaterialTheme.typography.titleMedium, color = Color(0xFF4A90D9))
                    Spacer(modifier = Modifier.height(16.dp))

                    SettingsRow(
                        title = "Export Configuration",
                        subtitle = "Copy or save your pages and tiles as JSON",
                        trailing = {
                            TextButton(onClick = {
                                exportJson = viewModel.exportConfig()
                                showExportDialog = true
                            }) {
                                Text("Export", color = Color(0xFF4A90D9))
                            }
                        }
                    )
                    Divider(color = Color(0xFF3A3A4E))
                    SettingsRow(
                        title = "Import Configuration",
                        subtitle = "Load pages and tiles from a JSON file",
                        trailing = {
                            TextButton(onClick = { showImportDialog = true }) {
                                Text("Import", color = Color(0xFF4A90D9))
                            }
                        }
                    )
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = Color(0xFF1A1A2E)),
                shape = RoundedCornerShape(16.dp)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text("About", style = MaterialTheme.typography.titleMedium, color = Color(0xFF4A90D9))
                    Spacer(modifier = Modifier.height(16.dp))

                    SettingsRow(
                        title = "PhoneDeck",
                        subtitle = "Version 1.4.0 • Built with ❤️ by @iamhero337",
                        trailing = {}
                    )
                    Divider(color = Color(0xFF3A3A4E))
                    SettingsRow(
                        title = "Open Source",
                        subtitle = "MIT License - View on GitHub",
                        trailing = {
                            TextButton(onClick = {
                                val intent = Intent(Intent.ACTION_VIEW, Uri.parse("https://github.com/iamhero337/PhoneDeck"))
                                (viewModel.getApplication() as Context).startActivity(intent)
                            }) {
                                Text("GitHub", color = Color(0xFF4A90D9))
                            }
                        }
                    )
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            if (lastCrash.value.isNotBlank()) {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFF2E1A1A)),
                    shape = RoundedCornerShape(16.dp)
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text("Debug", style = MaterialTheme.typography.titleMedium, color = Color(0xFFE53935))
                        Spacer(modifier = Modifier.height(8.dp))
                        Text("A crash was detected on last launch.", color = Color(0xFFEF9A9A), fontSize = 13.sp)
                        Spacer(modifier = Modifier.height(8.dp))
                        TextButton(onClick = { showDebugDialog = true }) {
                            Text("View Crash Details", color = Color(0xFFE53935))
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(32.dp))

            Text(
                "Built with \u2764 by @iamhero337",
                color = Color(0xFF555566),
                fontSize = 12.sp,
                textAlign = TextAlign.Center,
                modifier = Modifier.fillMaxWidth()
            )
        }
    }

    if (showDebugDialog) {
        AlertDialog(
            onDismissRequest = { showDebugDialog = false },
            title = { Text("Crash Report", fontWeight = FontWeight.Bold) },
            text = {
                Column(modifier = Modifier.fillMaxWidth()) {
                    Text("Copy this and send it to the developer:", color = Color(0xFF8888AA), fontSize = 13.sp)
                    Spacer(modifier = Modifier.height(8.dp))
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .heightIn(max = 300.dp)
                            .background(Color(0xFF0F0F1A), RoundedCornerShape(8.dp))
                            .verticalScroll(rememberScrollState())
                            .padding(12.dp)
                    ) {
                        Text(
                            text = lastCrash.value,
                            color = Color(0xFFEF9A9A),
                            fontSize = 11.sp,
                            style = androidx.compose.ui.text.TextStyle(fontFamily = androidx.compose.ui.text.font.FontFamily.Monospace)
                        )
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = {
                    val clipboard = (viewModel.getApplication() as Context).getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                    clipboard.setPrimaryClip(ClipData.newPlainText("PhoneDeck Crash", lastCrash.value))
                    showSnackbar("Crash report copied!")
                    showDebugDialog = false
                }) { Text("Copy to Clipboard", color = Color(0xFF4A90D9)) }
            },
            dismissButton = {
                Row {
                    TextButton(onClick = {
                        CrashLogger.clear()
                        lastCrash.value = ""
                        showDebugDialog = false
                    }) { Text("Clear", color = Color(0xFF8888AA)) }
                    TextButton(onClick = { showDebugDialog = false }) { Text("Close", color = Color(0xFF8888AA)) }
                }
            },
            containerColor = Color(0xFF1A1A2E),
            titleContentColor = Color.White,
            textContentColor = Color.White
        )
    }

    if (showAddPageDialog) {
        AlertDialog(
            onDismissRequest = { showAddPageDialog = false; newPageName = ""; newPageIcon = "apps" },
            title = { Text("Add Custom Page", fontWeight = FontWeight.Bold) },
            text = {
                Column {
                    OutlinedTextField(
                        value = newPageName,
                        onValueChange = { newPageName = it },
                        label = { Text("Page Name") },
                        placeholder = { Text("e.g. Development") },
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
                        if (newPageName.isNotBlank()) {
                            val page = Page(UUID.randomUUID().toString(), newPageName.trim(), emptyList())
                            viewModel.addCustomPage(page)
                            showAddPageDialog = false
                            newPageName = ""
                        }
                    },
                    enabled = newPageName.isNotBlank()
                ) { Text("Create", color = Color(0xFF4A90D9)) }
            },
            dismissButton = { TextButton(onClick = { showAddPageDialog = false }) { Text("Cancel", color = Color(0xFF8888AA)) } },
            containerColor = Color(0xFF1A1A2E),
            titleContentColor = Color.White,
            textContentColor = Color.White
        )
    }

    if (showResetConfirm) {
        AlertDialog(
            onDismissRequest = { showResetConfirm = false },
            title = { Text("Reset to Defaults?", fontWeight = FontWeight.Bold) },
            text = { Text("This will remove all custom pages and top sites. Default pages cannot be removed.") },
            confirmButton = {
                TextButton(onClick = {
                    viewModel.resetToDefaults()
                    showResetConfirm = false
                    showSnackbar("Reset to defaults")
                }) { Text("Reset", color = Color(0xFFE53935)) }
            },
            dismissButton = { TextButton(onClick = { showResetConfirm = false }) { Text("Cancel", color = Color(0xFF8888AA)) } },
            containerColor = Color(0xFF1A1A2E),
            titleContentColor = Color.White,
            textContentColor = Color.White
        )
    }

    if (showExportDialog) {
        AlertDialog(
            onDismissRequest = { showExportDialog = false },
            title = { Text("Export Configuration", fontWeight = FontWeight.Bold) },
            text = {
                Column(modifier = Modifier.fillMaxWidth()) {
                    Text("Copy this JSON to save your configuration:", color = Color(0xFF8888AA), fontSize = 13.sp)
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = exportJson,
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(200.dp)
                            .padding(12.dp)
                            .background(Color(0xFF0F0F1A), RoundedCornerShape(8.dp))
                            .fillMaxWidth(),
                        color = Color.White,
                        fontSize = 12.sp,
                        style = androidx.compose.ui.text.TextStyle(fontFamily = androidx.compose.ui.text.font.FontFamily.Monospace)
                    )
                }
            },
            confirmButton = {
                TextButton(onClick = {
                    val clipboard = (viewModel.getApplication() as Context).getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                    clipboard.setPrimaryClip(ClipData.newPlainText("PhoneDeck Config", exportJson))
                    showExportDialog = false
                    showSnackbar("Copied to clipboard!")
                }) { Text("Copy to Clipboard", color = Color(0xFF4A90D9)) }
            },
            dismissButton = { TextButton(onClick = { showExportDialog = false }) { Text("Close", color = Color(0xFF8888AA)) } },
            containerColor = Color(0xFF1A1A2E),
            titleContentColor = Color.White,
            textContentColor = Color.White
        )
    }

    if (showImportDialog) {
        AlertDialog(
            onDismissRequest = { showImportDialog = false; importJson = "" },
            title = { Text("Import Configuration", fontWeight = FontWeight.Bold) },
            text = {
                Column {
                    OutlinedTextField(
                        value = importJson,
                        onValueChange = { importJson = it },
                        label = { Text("Paste JSON Here") },
                        placeholder = { Text("Paste exported JSON config") },
                        singleLine = false,
                        modifier = Modifier.fillMaxWidth().height(200.dp),
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
                        if (importJson.isNotBlank()) {
                            viewModel.importConfig(importJson)
                            showImportDialog = false
                            importJson = ""
                            showSnackbar("Configuration imported!")
                        }
                    },
                    enabled = importJson.isNotBlank()
                ) { Text("Import", color = Color(0xFF4A90D9)) }
            },
            dismissButton = { TextButton(onClick = { showImportDialog = false }) { Text("Cancel", color = Color(0xFF8888AA)) } },
            containerColor = Color(0xFF1A1A2E),
            titleContentColor = Color.White,
            textContentColor = Color.White
        )
    }
}

@Composable
private fun SettingsRow(
    title: String,
    subtitle: String,
    trailing: @Composable () -> Unit
) {
    Row(
        modifier = Modifier.fillMaxWidth().padding(vertical = 12.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Column {
            Text(text = title, color = Color.White, fontSize = 16.sp, fontWeight = FontWeight.Medium)
            Spacer(modifier = Modifier.height(2.dp))
            Text(text = subtitle, color = Color(0xFF8888AA), fontSize = 13.sp)
        }
        trailing()
    }
}
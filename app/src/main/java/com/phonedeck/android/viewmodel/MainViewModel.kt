package com.phonedeck.android.viewmodel

import android.app.Application
import android.content.Context
import android.os.Vibrator
import android.os.VibrationEffect
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.phonedeck.android.data.models.Page
import com.phonedeck.android.data.models.Tile
import com.phonedeck.android.data.repository.ConfigRepository
import com.phonedeck.android.network.PhoneDeckClient
import com.phonedeck.android.network.MdnsScanner
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.Job
import org.json.JSONObject

class MainViewModel(application: Application) : AndroidViewModel(application) {

    private val client = PhoneDeckClient()
    private val mdnsScanner = MdnsScanner(application)
    private var discoveryJob: Job? = null
    private var connectionJob: Job? = null
    private var reconnectAttempts = 0
    private val vibrator = application.getSystemService(Context.VIBRATOR_SERVICE) as Vibrator

    private val _pages = MutableStateFlow<List<Page>>(emptyList())
    val pages: StateFlow<List<Page>> = _pages.asStateFlow()

    private val _currentPageIndex = MutableStateFlow(0)
    val currentPageIndex: StateFlow<Int> = _currentPageIndex.asStateFlow()

    private val _connectionStatus = MutableStateFlow("Disconnected")
    val connectionStatus: StateFlow<String> = _connectionStatus.asStateFlow()

    private val _connected = MutableStateFlow(false)
    val connected: StateFlow<Boolean> = _connected.asStateFlow()

    private val _discoveredServerIp = MutableStateFlow("")
    val discoveredServerIp: StateFlow<String> = _discoveredServerIp.asStateFlow()

    private val _lastCommandResult = MutableStateFlow<String?>(null)
    val lastCommandResult: StateFlow<String?> = _lastCommandResult.asStateFlow()

    private var connectedHost = ""
    private var responseJob: Job? = null

    init {
        ConfigRepository.init(application)
        loadPages()
        startDiscovery()
        collectCommandResponses()
    }

    private fun collectCommandResponses() {
        responseJob?.cancel()
        responseJob = viewModelScope.launch {
            client.commandResponses.collect { response ->
                try {
                    val json = JSONObject(response)
                    val status = json.optString("status", "")
                    val command = json.optString("command", "")
                    if (status == "error") {
                        val msg = json.optString("message", "Unknown error")
                        _lastCommandResult.value = "$command: $msg"
                    } else {
                        _lastCommandResult.value = "$command: OK"
                    }
                } catch (_: Exception) {
                    _lastCommandResult.value = "Server: $response"
                }
            }
        }
    }

    private fun loadPages() {
        viewModelScope.launch {
            _pages.value = ConfigRepository.getPages()
        }
    }

    private fun startDiscovery() {
        discoveryJob?.cancel()
        discoveryJob = viewModelScope.launch {
            mdnsScanner.discoverServices().collect { serviceInfo ->
                val host = serviceInfo.host.hostAddress
                if (host != null) {
                    _discoveredServerIp.value = host
                    if (!_connected.value && ConfigRepository.getAutoConnect()) {
                        connect(host)
                    }
                }
            }
        }
    }

    fun connect(host: String, port: Int = 9090) {
        connectionJob?.cancel()
        connectedHost = host
        reconnectAttempts = 0
        connectionJob = viewModelScope.launch {
            runConnectionLoop(host, port)
        }
    }

    private suspend fun runConnectionLoop(host: String, port: Int) {
        while (connectedHost.isNotBlank()) {
            try {
                client.connect(host, port).collect { state ->
                    when (state) {
                        is PhoneDeckClient.ConnectionState.Connected -> {
                            _connectionStatus.value = "Connected to ${state.serverName}"
                            _connected.value = true
                            reconnectAttempts = 0
                        }
                        is PhoneDeckClient.ConnectionState.Disconnected -> {
                            _connectionStatus.value = "Disconnected"
                            _connected.value = false
                            throw RuntimeException("Disconnected")
                        }
                        is PhoneDeckClient.ConnectionState.Error -> {
                            _connectionStatus.value = "Error: ${state.message}"
                            _connected.value = false
                            throw RuntimeException(state.message ?: "Error")
                        }
                    }
                }
            } catch (e: Exception) {
                if (connectedHost.isBlank()) break
                if (e.message == "Disconnected" || e.message?.contains("refused") == true || e.message?.contains("timeout") == true) {
                    reconnectAttempts++
                    val delayMs = minOf(1000L * (1 shl minOf(reconnectAttempts, 6)), 30000L)
                    _connectionStatus.value = "Reconnecting in ${delayMs / 1000}s..."
                    delay(delayMs)
                } else {
                    _connectionStatus.value = "Error: ${e.message}"
                    delay(10000)
                }
            }
        }
        _connectionStatus.value = "Disconnected"
        _connected.value = false
    }

    fun selectPage(index: Int) {
        if (index in _pages.value.indices) {
            _currentPageIndex.value = index
        }
    }

    fun sendCommand(command: String) {
        if (ConfigRepository.getHapticFeedback()) {
            vibrator.vibrate(VibrationEffect.createOneShot(15, VibrationEffect.DEFAULT_AMPLITUDE))
        }
        client.sendCommand(command)
        _lastCommandResult.value = "Sending: $command..."
    }

    fun addTopSite(label: String, url: String) {
        ConfigRepository.addTopSite(label, url)
        _pages.value = ConfigRepository.getPages()
    }

    fun removeTopSite(id: String) {
        ConfigRepository.removeTopSite(id)
        _pages.value = ConfigRepository.getPages()
    }

    fun clearCommandResult() {
        _lastCommandResult.value = null
    }

    fun disconnect() {
        connectionJob?.cancel()
        client.disconnect()
        _connected.value = false
        _connectionStatus.value = "Disconnected"
        connectedHost = ""
        reconnectAttempts = 0
        startDiscovery()
    }

    fun addCustomPage(page: Page) {
        viewModelScope.launch {
            ConfigRepository.addCustomPage(page)
            _pages.value = ConfigRepository.getPages()
        }
    }

    fun updatePage(page: Page) {
        viewModelScope.launch {
            ConfigRepository.updatePage(page)
            _pages.value = ConfigRepository.getPages()
        }
    }

    fun deletePage(pageId: String) {
        viewModelScope.launch {
            ConfigRepository.deletePage(pageId)
            _pages.value = ConfigRepository.getPages()
        }
    }

    fun reorderPages(pages: List<Page>) {
        viewModelScope.launch {
            ConfigRepository.reorderPages(pages)
            _pages.value = ConfigRepository.getPages()
        }
    }

    fun resetToDefaults() {
        viewModelScope.launch {
            ConfigRepository.resetToDefaults()
            _pages.value = ConfigRepository.getPages()
            _currentPageIndex.value = 0
        }
    }

    fun exportConfig(): String = ConfigRepository.exportConfig()

    fun importConfig(jsonString: String) {
        viewModelScope.launch {
            ConfigRepository.importConfig(jsonString)
            _pages.value = ConfigRepository.getPages()
        }
    }

    override fun onCleared() {
        client.disconnect()
        super.onCleared()
    }
}
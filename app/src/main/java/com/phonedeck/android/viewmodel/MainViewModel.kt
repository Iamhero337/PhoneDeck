package com.phonedeck.android.viewmodel

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.phonedeck.android.data.models.Page
import com.phonedeck.android.data.repository.ConfigRepository
import com.phonedeck.android.network.PhoneDeckClient
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.Job
import com.phonedeck.android.network.MdnsScanner

class MainViewModel(application: Application) : AndroidViewModel(application) {

    private val client = PhoneDeckClient()
    private val mdnsScanner = MdnsScanner(application)
    private var discoveryJob: Job? = null
    private var connectionJob: Job? = null
    private var reconnectAttempts = 0

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

    init {
        ConfigRepository.init(application)
        _pages.value = ConfigRepository.getPages()
        startDiscovery()
    }

    private fun startDiscovery() {
        discoveryJob?.cancel()
        discoveryJob = viewModelScope.launch {
            mdnsScanner.discoverServices().collect { serviceInfo ->
                if (!_connected.value && _discoveredServerIp.value.isBlank()) {
                    val host = serviceInfo.host.hostAddress
                    if (host != null) {
                        _discoveredServerIp.value = host
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
        client.sendCommand(command)
        _lastCommandResult.value = "Sent: $command"
    }

    fun addTopSite(label: String, url: String) {
        var cleanUrl = url.trim()
        if (!cleanUrl.startsWith("http://") && !cleanUrl.startsWith("https://")) {
            cleanUrl = "https://$cleanUrl"
        }
        ConfigRepository.addTopSite(label, cleanUrl)
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

    override fun onCleared() {
        client.disconnect()
        super.onCleared()
    }
}

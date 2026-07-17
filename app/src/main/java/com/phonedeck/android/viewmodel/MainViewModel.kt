package com.phonedeck.android.viewmodel

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.phonedeck.android.data.models.Page
import com.phonedeck.android.data.repository.ConfigRepository
import com.phonedeck.android.network.PhoneDeckClient
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

    init {
        ConfigRepository.init(application)
        _pages.value = ConfigRepository.getPages()
        startDiscovery()
    }

    private fun startDiscovery() {
        discoveryJob?.cancel()
        discoveryJob = viewModelScope.launch {
            mdnsScanner.discoverServices().collect { serviceInfo ->
                if (!_connected.value) {
                    val host = serviceInfo.host.hostAddress
                    if (host != null) {
                        _discoveredServerIp.value = host
                    }
                }
            }
        }
    }

    fun connect(host: String, port: Int = 9090) {
        viewModelScope.launch {
            client.connect(host, port).collect { state ->
                when (state) {
                    is PhoneDeckClient.ConnectionState.Connected -> {
                        _connectionStatus.value = "Connected to ${state.serverName}"
                        _connected.value = true
                    }
                    is PhoneDeckClient.ConnectionState.Disconnected -> {
                        _connectionStatus.value = "Disconnected"
                        _connected.value = false
                    }
                    is PhoneDeckClient.ConnectionState.Error -> {
                        _connectionStatus.value = "Error: ${state.message}"
                        _connected.value = false
                    }
                }
            }
        }
    }

    fun selectPage(index: Int) {
        if (index in _pages.value.indices) {
            _currentPageIndex.value = index
        }
    }

    fun sendCommand(command: String) {
        client.sendCommand(command)
    }

    fun addTopSite(label: String, url: String) {
        var cleanUrl = url.trim()
        if (!cleanUrl.startsWith("http://") && !cleanUrl.startsWith("https://")) {
            cleanUrl = "https://$cleanUrl"
        }
        ConfigRepository.addTopSite(label, cleanUrl)
        _pages.value = ConfigRepository.getPages()
    }

    override fun onCleared() {
        client.disconnect()
        super.onCleared()
    }
}

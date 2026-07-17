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

class MainViewModel(application: Application) : AndroidViewModel(application) {

    private val client = PhoneDeckClient()

    private val _pages = MutableStateFlow<List<Page>>(emptyList())
    val pages: StateFlow<List<Page>> = _pages.asStateFlow()

    private val _currentPageIndex = MutableStateFlow(0)
    val currentPageIndex: StateFlow<Int> = _currentPageIndex.asStateFlow()

    private val _connectionStatus = MutableStateFlow("Disconnected")
    val connectionStatus: StateFlow<String> = _connectionStatus.asStateFlow()

    private val _connected = MutableStateFlow(false)
    val connected: StateFlow<Boolean> = _connected.asStateFlow()

    init {
        _pages.value = ConfigRepository.getPages()
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

    override fun onCleared() {
        client.disconnect()
        super.onCleared()
    }
}

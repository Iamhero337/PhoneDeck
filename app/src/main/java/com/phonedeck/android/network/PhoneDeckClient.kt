package com.phonedeck.android.network

import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import java.util.concurrent.TimeUnit

class PhoneDeckClient {

    private val client = OkHttpClient.Builder()
        .readTimeout(0, TimeUnit.SECONDS)
        .connectTimeout(5, TimeUnit.SECONDS)
        .pingInterval(15, TimeUnit.SECONDS)
        .build()

    private var webSocket: WebSocket? = null

    sealed class ConnectionState {
        data object Disconnected : ConnectionState()
        data class Connected(val serverName: String) : ConnectionState()
        data class Error(val message: String) : ConnectionState()
    }

    fun connect(host: String, port: Int): Flow<ConnectionState> = callbackFlow {
        val request = Request.Builder()
            .url("ws://$host:$port")
            .build()

        val listener = object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                trySend(ConnectionState.Connected(host))
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                trySend(ConnectionState.Error(t.message ?: "Connection failed"))
            }

            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                webSocket.close(1000, null)
            }

            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                trySend(ConnectionState.Disconnected)
            }
        }

        webSocket = client.newWebSocket(request, listener)

        awaitClose {
            webSocket?.close(1000, "Client closing")
            client.dispatcher.executorService.shutdown()
        }
    }

    fun sendCommand(command: String) {
        webSocket?.send(command)
    }

    fun disconnect() {
        webSocket?.close(1000, "User disconnect")
        webSocket = null
    }
}

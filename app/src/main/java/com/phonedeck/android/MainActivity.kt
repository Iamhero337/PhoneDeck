package com.phonedeck.android

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.lifecycle.viewmodel.compose.viewModel
import com.phonedeck.android.data.repository.CrashLogger
import com.phonedeck.android.ui.screens.MainScreen
import com.phonedeck.android.ui.theme.PhoneDeckTheme
import com.phonedeck.android.viewmodel.MainViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.URL


const val CURRENT_VERSION = "v1.3.6"

private fun parseVersion(versionStr: String): List<Int> {
    val cleaned = versionStr.removePrefix("v")
    return cleaned.split(".").map { it.toIntOrNull() ?: 0 }
}

private fun isNewerVersion(latest: String, current: String): Boolean {
    val latestParts = parseVersion(latest)
    val currentParts = parseVersion(current)
    for (i in 0 until maxOf(latestParts.size, currentParts.size)) {
        val l = latestParts.getOrElse(i) { 0 }
        val c = currentParts.getOrElse(i) { 0 }
        if (l != c) return l > c
    }
    return false
}

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        CrashLogger.init(applicationContext)
        setContent {
            PhoneDeckTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = Color(0xFF0F0F1A)
                ) {
                    val viewModel: MainViewModel = viewModel()
                    MainScreen(viewModel = viewModel)
                    UpdateChecker(this@MainActivity)
                }
            }
        }
    }
}

@Composable
fun UpdateChecker(activity: ComponentActivity) {
    val showDialog = remember { mutableStateOf(false) }
    val latestUrl = remember { mutableStateOf("") }
    val latestVersion = remember { mutableStateOf("") }

    LaunchedEffect(Unit) {
        withContext(Dispatchers.IO) {
            try {
                val url = URL("https://api.github.com/repos/iamhero337/PhoneDeck/releases/latest")
                val connection = url.openConnection()
                connection.setRequestProperty("User-Agent", "Mozilla/5.0")
                val response = connection.getInputStream().bufferedReader().use { it.readText() }
                val json = JSONObject(response)
                val tag = json.getString("tag_name")
                if (isNewerVersion(tag, CURRENT_VERSION)) {
                    latestVersion.value = tag
                    latestUrl.value = json.getString("html_url")
                    showDialog.value = true
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    if (showDialog.value) {
        AlertDialog(
            onDismissRequest = { showDialog.value = false },
            title = { Text("Update Available") },
            text = { Text("A new version of PhoneDeck (${latestVersion.value}) is available. Would you like to download it now?") },
            confirmButton = {
                Button(onClick = {
                    val intent = Intent(Intent.ACTION_VIEW, Uri.parse(latestUrl.value))
                    activity.startActivity(intent)
                    showDialog.value = false
                }) { Text("Update") }
            },
            dismissButton = {
                Button(onClick = { showDialog.value = false }) { Text("Later") }
            }
        )
    }
}
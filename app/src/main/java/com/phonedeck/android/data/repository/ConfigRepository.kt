package com.phonedeck.android.data.repository

import android.content.Context
import android.content.SharedPreferences
import com.phonedeck.android.data.models.Page
import com.phonedeck.android.data.models.Tile
import org.json.JSONArray
import org.json.JSONObject
import java.util.UUID

object ConfigRepository {
    private var prefs: SharedPreferences? = null
    private val topSitesTiles = mutableListOf<Tile>()

    private val defaultPages = listOf(
        Page(
            id = "prod",
            name = "Prod",
            tiles = listOf(
                Tile("dev1", "VS Code", "code", "code"),
                Tile("dev2", "Terminal", "terminal", "terminal"),
                Tile("dev3", "Browser", "public", "browser"),
                Tile("dev4", "Spotify", "music_note", "spotify"),
            )
        ),
        Page(
            id = "design",
            name = "Design",
            tiles = listOf(
                Tile("ds1", "Figma", "draw", "figma"),
                Tile("ds2", "Photoshop", "image", "photoshop"),
                Tile("ds3", "Illustrator", "brush", "illustrator"),
                Tile("ds4", "Preview", "visibility", "preview"),
            )
        ),
        Page(
            id = "media",
            name = "Media",
            tiles = listOf(
                Tile("md1", "Volume Up", "volume_up", "volume_up"),
                Tile("md2", "Volume Down", "volume_down", "volume_down"),
                Tile("md3", "Mute", "volume_off", "mute"),
                Tile("md4", "Play/Pause", "play_arrow", "play_pause"),
                Tile("md5", "Next", "skip_next", "next"),
                Tile("md6", "Prev", "skip_previous", "prev"),
                Tile("md7", "Brightness +", "brightness_high", "brightness_up"),
                Tile("md8", "Brightness -", "brightness_low", "brightness_down"),
            )
        ),
        Page(
            id = "system",
            name = "System",
            tiles = listOf(
                Tile("sys1", "Screenshot", "screenshot", "screenshot"),
                Tile("sys2", "Lock", "lock", "lock"),
                Tile("sys3", "Sleep", "bedtime", "sleep"),
                Tile("sys4", "Browser", "public", "browser"),
                Tile("sys5", "Restart", "restart", "restart"),
                Tile("sys6", "Shutdown", "shutdown", "shutdown"),
                Tile("sys7", "Logout", "logout", "logout"),
                Tile("sys8", "Hibernate", "hibernate", "hibernate"),
            )
        ),
    )

    fun init(context: Context) {
        prefs = context.getSharedPreferences("phonedeck_prefs", Context.MODE_PRIVATE)
        loadTopSites()
    }

    private fun loadTopSites() {
        topSitesTiles.clear()
        val json = prefs?.getString("top_sites", "[]") ?: "[]"
        try {
            val array = JSONArray(json)
            for (i in 0 until array.length()) {
                val obj = array.getJSONObject(i)
                topSitesTiles.add(Tile(
                    id = obj.getString("id"),
                    label = obj.getString("label"),
                    icon = obj.getString("icon"),
                    command = obj.getString("command")
                ))
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    private fun saveTopSites() {
        val array = JSONArray()
        topSitesTiles.forEach {
            val obj = JSONObject()
            obj.put("id", it.id)
            obj.put("label", it.label)
            obj.put("icon", it.icon)
            obj.put("command", it.command)
            array.put(obj)
        }
        prefs?.edit()?.putString("top_sites", array.toString())?.apply()
    }

    fun addTopSite(label: String, url: String) {
        topSitesTiles.add(Tile(
            id = UUID.randomUUID().toString(),
            label = label,
            icon = "public",
            command = "open_url:$url"
        ))
        saveTopSites()
    }

    fun getPages(): List<Page> {
        val pages = defaultPages.toMutableList()
        pages.add(Page("top_sites", "Top Sites", topSitesTiles.toList()))
        return pages
    }
}

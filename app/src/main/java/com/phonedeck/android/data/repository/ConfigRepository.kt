package com.phonedeck.android.data.repository

import android.content.Context
import android.content.SharedPreferences
import com.phonedeck.android.data.models.Page
import com.phonedeck.android.data.models.Tile
import org.json.JSONArray
import org.json.JSONException
import org.json.JSONObject
import java.util.UUID

object ConfigRepository {
    private var prefs: SharedPreferences? = null
    private val topSitesTiles = mutableListOf<Tile>()
    private val customPages = mutableMapOf<String, Page>()

    private val defaultPages = listOf(
        Page(
            id = "prod",
            name = "Prod",
            tiles = listOf(
                Tile("dev1", "VS Code", "code", "code", 0xFF1E1E2E.toInt(), 0xFF4A90D9.toInt()),
                Tile("dev2", "Terminal", "terminal", "terminal", 0xFF1E1E2E.toInt(), 0xFF4A90D9.toInt()),
                Tile("dev3", "Browser", "public", "browser", 0xFF1E1E2E.toInt(), 0xFF4A90D9.toInt()),
                Tile("dev4", "Spotify", "music_note", "spotify", 0xFF1E1E2E.toInt(), 0xFF1DB954.toInt()),
            )
        ),
        Page(
            id = "design",
            name = "Design",
            tiles = listOf(
                Tile("ds1", "Figma", "draw", "figma", 0xFF1E1E2E.toInt(), 0xFFF24E1E.toInt()),
                Tile("ds2", "Photoshop", "image", "photoshop", 0xFF1E1E2E.toInt(), 0xFF31A8FF.toInt()),
                Tile("ds3", "Illustrator", "brush", "illustrator", 0xFF1E1E2E.toInt(), 0xFFFF9A00.toInt()),
                Tile("ds4", "Preview", "visibility", "preview", 0xFF1E1E2E.toInt(), 0xFF4A90D9.toInt()),
            )
        ),
        Page(
            id = "media",
            name = "Media",
            tiles = listOf(
                Tile("md1", "Volume Up", "volume_up", "volume_up", 0xFF1E1E2E.toInt(), 0xFF4CAF50.toInt()),
                Tile("md2", "Volume Down", "volume_down", "volume_down", 0xFF1E1E2E.toInt(), 0xFF4CAF50.toInt()),
                Tile("md3", "Mute", "volume_off", "mute", 0xFF1E1E2E.toInt(), 0xFF4CAF50.toInt()),
                Tile("md4", "Play/Pause", "play_pause", "play_pause", 0xFF1E1E2E.toInt(), 0xFF1DB954.toInt()),
                Tile("md5", "Next", "next", "next", 0xFF1E1E2E.toInt(), 0xFF1DB954.toInt()),
                Tile("md6", "Prev", "prev", "prev", 0xFF1E1E2E.toInt(), 0xFF1DB954.toInt()),
                Tile("md7", "Brightness +", "brightness_up", "brightness_up", 0xFF1E1E2E.toInt(), 0xFFFFC107.toInt()),
                Tile("md8", "Brightness -", "brightness_down", "brightness_down", 0xFF1E1E2E.toInt(), 0xFFFFC107.toInt()),
            )
        ),
        Page(
            id = "system",
            name = "System",
            tiles = listOf(
                Tile("sys1", "Screenshot", "screenshot", "screenshot", 0xFF1E1E2E.toInt(), 0xFF4A90D9.toInt()),
                Tile("sys2", "Lock", "lock", "lock", 0xFF1E1E2E.toInt(), 0xFFE53935.toInt()),
                Tile("sys3", "Sleep", "bedtime", "sleep", 0xFF1E1E2E.toInt(), 0xFF4A90D9.toInt()),
                Tile("sys4", "Browser", "public", "browser", 0xFF1E1E2E.toInt(), 0xFF4A90D9.toInt()),
                Tile("sys5", "Restart", "restart", "restart", 0xFF1E1E2E.toInt(), 0xFFF57C00.toInt()),
                Tile("sys6", "Shutdown", "shutdown", "shutdown", 0xFF1E1E2E.toInt(), 0xFFF57C00.toInt()),
                Tile("sys7", "Logout", "logout", "logout", 0xFF1E1E2E.toInt(), 0xFFF57C00.toInt()),
                Tile("sys8", "Hibernate", "hibernate", "hibernate", 0xFF1E1E2E.toInt(), 0xFFF57C00.toInt()),
            )
        ),
    )

    fun init(context: Context) {
        prefs = context.getSharedPreferences("phonedeck_prefs", Context.MODE_PRIVATE)
        loadTopSites()
        loadCustomPages()
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
                    command = obj.getString("command"),
                    color = obj.optInt("color", 0xFF1E1E2E.toInt()),
                    iconColor = obj.optInt("iconColor", 0xFF4A90D9.toInt()),
                ))
            }
        } catch (e: JSONException) {
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
            obj.put("color", it.color)
            obj.put("iconColor", it.iconColor)
            array.put(obj)
        }
        prefs?.edit()?.putString("top_sites", array.toString())?.apply()
    }

    fun addTopSite(label: String, url: String) {
        var cleanUrl = url.trim()
        if (!cleanUrl.startsWith("http://") && !cleanUrl.startsWith("https://")) {
            cleanUrl = "https://$cleanUrl"
        }
        topSitesTiles.add(Tile(
            id = UUID.randomUUID().toString(),
            label = label,
            icon = "public",
            command = "open_url:$cleanUrl",
            color = 0xFF1E1E2E.toInt(),
            iconColor = 0xFF4A90D9.toInt(),
        ))
        saveTopSites()
    }

    fun getTopSites(): List<Tile> = topSitesTiles.toList()

    fun removeTopSite(id: String) {
        topSitesTiles.removeAll { it.id == id }
        saveTopSites()
    }

    private fun loadCustomPages() {
        customPages.clear()
        val json = prefs?.getString("custom_pages", "{}") ?: "{}"
        try {
            val obj = JSONObject(json)
            val keys = obj.keys()
            while (keys.hasNext()) {
                val key = keys.next()
                val pageObj = obj.getJSONObject(key)
                val tilesArray = pageObj.getJSONArray("tiles")
                val tiles = mutableListOf<Tile>()
                for (i in 0 until tilesArray.length()) {
                    val tileObj = tilesArray.getJSONObject(i)
                    tiles.add(Tile(
                        id = tileObj.getString("id"),
                        label = tileObj.getString("label"),
                        icon = tileObj.getString("icon"),
                        command = tileObj.getString("command"),
                        color = tileObj.optInt("color", 0xFF2A2A3E.toInt()),
                        iconColor = tileObj.optInt("iconColor", 0xFF4A90D9.toInt()),
                    ))
                }
                customPages[key] = Page(
                    id = key,
                    name = pageObj.getString("name"),
                    tiles = tiles
                )
            }
        } catch (e: JSONException) {
            e.printStackTrace()
        }
    }

    private fun saveCustomPages() {
        val obj = JSONObject()
        customPages.forEach { (key, page) ->
            val pageObj = JSONObject()
            pageObj.put("name", page.name)
            val tilesArray = JSONArray()
            page.tiles.forEach { tile ->
                val tileObj = JSONObject()
                tileObj.put("id", tile.id)
                tileObj.put("label", tile.label)
                tileObj.put("icon", tile.icon)
                tileObj.put("command", tile.command)
                tileObj.put("color", tile.color)
                tileObj.put("iconColor", tile.iconColor)
                tilesArray.put(tileObj)
            }
            pageObj.put("tiles", tilesArray)
            obj.put(key, pageObj)
        }
        prefs?.edit()?.putString("custom_pages", obj.toString())?.apply()
    }

    fun getPages(): List<Page> {
        val pages = defaultPages.toMutableList()
        pages.add(Page("top_sites", "Top Sites", topSitesTiles.toList()))
        pages.addAll(customPages.values)
        return pages
    }

    fun addCustomPage(page: Page) {
        val newId = UUID.randomUUID().toString()
        val newPage = page.copy(id = newId)
        customPages[newId] = newPage
        saveCustomPages()
    }

    fun updatePage(page: Page) {
        customPages[page.id] = page
        saveCustomPages()
    }

    fun deletePage(pageId: String) {
        customPages.remove(pageId)
        saveCustomPages()
    }

    fun reorderPages(pages: List<Page>) {
        customPages.clear()
        pages.forEach { customPages[it.id] = it }
        saveCustomPages()
    }

    fun resetToDefaults() {
        topSitesTiles.clear()
        customPages.clear()
        saveTopSites()
        saveCustomPages()
    }

    fun exportConfig(): String {
        val obj = JSONObject()
        val pagesArray = JSONArray()
        getPages().forEach { page ->
            val pageObj = JSONObject()
            pageObj.put("id", page.id)
            pageObj.put("name", page.name)
            val tilesArray = JSONArray()
            page.tiles.forEach { tile ->
                val tileObj = JSONObject()
                tileObj.put("id", tile.id)
                tileObj.put("label", tile.label)
                tileObj.put("icon", tile.icon)
                tileObj.put("command", tile.command)
                tileObj.put("color", tile.color)
                tileObj.put("iconColor", tile.iconColor)
                tilesArray.put(tileObj)
            }
            pageObj.put("tiles", tilesArray)
            pagesArray.put(pageObj)
        }
        obj.put("pages", pagesArray)
        obj.put("version", "1.2.0")
        return obj.toString(2)
    }

    fun importConfig(jsonString: String) {
        try {
            val obj = JSONObject(jsonString)
            val pagesArray = obj.getJSONArray("pages")
            topSitesTiles.clear()
            customPages.clear()
            for (i in 0 until pagesArray.length()) {
                val pageObj = pagesArray.getJSONObject(i)
                val id = pageObj.getString("id")
                val name = pageObj.getString("name")
                val tilesArray = pageObj.getJSONArray("tiles")
                val tiles = mutableListOf<Tile>()
                for (j in 0 until tilesArray.length()) {
                    val tileObj = tilesArray.getJSONObject(j)
                    tiles.add(Tile(
                        id = tileObj.getString("id"),
                        label = tileObj.getString("label"),
                        icon = tileObj.getString("icon"),
                        command = tileObj.getString("command"),
                        color = tileObj.optInt("color", 0xFF2A2A3E.toInt()),
                        iconColor = tileObj.optInt("iconColor", 0xFF4A90D9.toInt()),
                    ))
                }
                if (id == "top_sites") {
                    topSitesTiles.addAll(tiles)
                } else if (!id.startsWith("prod") && !id.startsWith("design") && !id.startsWith("media") && !id.startsWith("system")) {
                    customPages[id] = Page(id, name, tiles)
                }
            }
            saveTopSites()
            saveCustomPages()
        } catch (e: JSONException) {
            e.printStackTrace()
        }
    }

    fun getHapticFeedback(): Boolean {
        return prefs?.getBoolean("haptic_feedback", true) ?: true
    }

    fun setHapticFeedback(enabled: Boolean) {
        prefs?.edit()?.putBoolean("haptic_feedback", enabled)?.apply()
    }

    fun getAutoConnect(): Boolean {
        return prefs?.getBoolean("auto_connect", true) ?: true
    }

    fun setAutoConnect(enabled: Boolean) {
        prefs?.edit()?.putBoolean("auto_connect", enabled)?.apply()
    }

    fun getServerPort(): Int {
        return prefs?.getInt("server_port", 9090) ?: 9090
    }

    fun setServerPort(port: Int) {
        prefs?.edit()?.putInt("server_port", port)?.apply()
    }
}
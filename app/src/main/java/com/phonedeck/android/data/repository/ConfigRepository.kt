package com.phonedeck.android.data.repository

import com.phonedeck.android.data.models.Page
import com.phonedeck.android.data.models.Tile

object ConfigRepository {

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
            )
        ),
    )

    fun getPages(): List<Page> = defaultPages
}

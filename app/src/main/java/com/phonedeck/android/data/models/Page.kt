package com.phonedeck.android.data.models

data class Tile(
    val id: String,
    val label: String,
    val icon: String = "",
    val command: String = "",
    val color: Long = 0xFF2A2A3E,
)

data class Page(
    val id: String,
    val name: String,
    val tiles: List<Tile> = emptyList(),
)

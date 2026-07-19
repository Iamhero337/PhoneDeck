package com.phonedeck.android.data.models

import kotlinx.serialization.Serializable

@Serializable
data class Tile(
    val id: String,
    val label: String,
    val icon: String = "",
    val command: String = "",
    val color: Int = 0xFF2A2A3E.toInt(),
    val iconColor: Int = 0xFF4A90D9.toInt()
)

@Serializable
data class Page(
    val id: String,
    val name: String,
    val tiles: List<Tile> = emptyList()
)
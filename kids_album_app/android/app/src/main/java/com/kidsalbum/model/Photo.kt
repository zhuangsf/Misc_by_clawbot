package com.kidsalbum.model

data class Photo(
    val id: Int,
    val category: String,
    val title: String,
    val emoji: String,
    val colorResId: Int
)

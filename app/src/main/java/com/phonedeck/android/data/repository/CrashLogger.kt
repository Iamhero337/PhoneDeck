package com.phonedeck.android.data.repository

import android.content.Context
import android.content.SharedPreferences
import java.io.StringWriter
import java.io.PrintWriter

object CrashLogger {
    private var prefs: SharedPreferences? = null

    fun init(context: Context) {
        prefs = context.getSharedPreferences("phonedeck_crashes", Context.MODE_PRIVATE)
        val prevHandler = Thread.getDefaultUncaughtExceptionHandler()
        Thread.setDefaultUncaughtExceptionHandler { thread, throwable ->
            saveCrash(throwable)
            prevHandler?.uncaughtException(thread, throwable)
        }
    }

    private fun saveCrash(throwable: Throwable) {
        try {
            val sw = StringWriter()
            val pw = PrintWriter(sw)
            throwable.printStackTrace(pw)
            pw.flush()
            prefs?.edit()?.putString("last_crash", sw.toString())?.apply()
        } catch (_: Exception) {}
    }

    fun getLastCrash(): String {
        return prefs?.getString("last_crash", "") ?: ""
    }

    fun clear() {
        prefs?.edit()?.remove("last_crash")?.apply()
    }
}

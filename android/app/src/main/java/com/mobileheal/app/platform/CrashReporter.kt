package com.mobileheal.app.platform

import android.content.Context
import android.os.Build
import com.google.firebase.crashlytics.FirebaseCrashlytics
import com.mobileheal.app.BuildConfig
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.File
import java.io.PrintWriter
import java.io.StringWriter
import kotlin.concurrent.thread

/**
 * Captures uncaught exceptions, persists them, and uploads them to the MobileHeal backend
 * (POST /api/crashes) on the next launch, where they become incidents for auto-heal.
 * Integrates with Firebase Crashlytics for real-time fatal and non-fatal crash tracking.
 */
object CrashReporter {
    private const val FILE = "pending_crash.json"

    fun install(ctx: Context, baseUrl: String) {
        val app = ctx.applicationContext

        // Explicitly enable Crashlytics collection and set custom keys
        runCatching {
            val crashlytics = FirebaseCrashlytics.getInstance()
            crashlytics.setCrashlyticsCollectionEnabled(true)
            crashlytics.setCustomKey("app_version", BuildConfig.VERSION_NAME)
            crashlytics.setCustomKey("device_model", "${Build.MANUFACTURER} ${Build.MODEL}")
            crashlytics.setCustomKey("api_level", Build.VERSION.SDK_INT)
            crashlytics.setCustomKey("profile_id", BuildConfig.PROFILE_ID)
            crashlytics.log("CrashReporter installed successfully")
        }

        val previous = Thread.getDefaultUncaughtExceptionHandler()
        Thread.setDefaultUncaughtExceptionHandler { t, e ->
            runCatching { File(app.filesDir, FILE).writeText(toJson(e, t.name).toString()) }
            previous?.uncaughtException(t, e)
        }
        uploadPending(app, baseUrl)
    }

    /** Set user identity in Crashlytics. */
    fun setUserId(userId: String) {
        runCatching { FirebaseCrashlytics.getInstance().setUserId(userId) }
    }

    /** Add custom key-value attributes to Crashlytics reports. */
    fun setCustomKey(key: String, value: String) {
        runCatching { FirebaseCrashlytics.getInstance().setCustomKey(key, value) }
    }

    /** Log custom breadcrumb messages to Crashlytics. */
    fun log(message: String) {
        runCatching { FirebaseCrashlytics.getInstance().log(message) }
    }

    /** Report a caught (non-fatal) exception immediately to Crashlytics and backend. */
    fun report(baseUrl: String, e: Throwable) {
        runCatching {
            val crashlytics = FirebaseCrashlytics.getInstance()
            crashlytics.log("Non-fatal error reported: ${e.message}")
            crashlytics.recordException(e)
        }
        thread { send(baseUrl, toJson(e, Thread.currentThread().name)) }
    }

    private fun uploadPending(ctx: Context, baseUrl: String) = thread {
        val f = File(ctx.filesDir, FILE)
        if (f.exists() && runCatching { send(baseUrl, JSONObject(f.readText())) }.getOrDefault(false)) f.delete()
    }

    private fun toJson(e: Throwable, threadName: String): JSONObject {
        val sw = StringWriter().also { e.printStackTrace(PrintWriter(it)) }
        return JSONObject()
            .put("exception", e.javaClass.name)
            .put("message", e.message ?: "")
            .put("stack", sw.toString())
            .put("thread", threadName)
            .put("device", "${Build.MANUFACTURER} ${Build.MODEL} (API ${Build.VERSION.SDK_INT})")
            .put("app_version", BuildConfig.VERSION_NAME)
    }

    private fun send(baseUrl: String, body: JSONObject): Boolean {
        val req = Request.Builder().url("$baseUrl/api/crashes")
            .post(body.toString().toRequestBody("application/json".toMediaType())).build()
        return OkHttpClient().newCall(req).execute().use { it.isSuccessful }
    }
}

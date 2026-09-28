package com.dealradar.app.service

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import androidx.core.app.NotificationCompat
import com.dealradar.app.MainActivity
import com.dealradar.app.data.api.DealRadarApiClient
import com.dealradar.app.data.model.DeviceRegisterRequest
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class DealRadarFirebaseMessagingService : FirebaseMessagingService() {

    override fun onNewToken(token: String) {
        super.onNewToken(token)
        // Guardar token y enviarlo al backend
        val prefs = getSharedPreferences("dealradar_prefs", Context.MODE_PRIVATE)
        prefs.edit().putString("fcm_token", token).apply()

        val deviceId = prefs.getString("device_id", null) ?: return
        CoroutineScope(Dispatchers.IO).launch {
            try {
                DealRadarApiClient.api.registerDevice(DeviceRegisterRequest(deviceId = deviceId, fcm_token = token))
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    override fun onMessageReceived(remoteMessage: RemoteMessage) {
        super.onMessageReceived(remoteMessage)

        val title = remoteMessage.notification?.title ?: remoteMessage.data["title"] ?: "¡Oferta detectada!"
        val body = remoteMessage.notification?.body ?: remoteMessage.data["body"] ?: "El precio de tu producto bajó."
        val productUrl = remoteMessage.data["product_url"]

        showNotification(title, body, productUrl)
    }

    private fun showNotification(title: String, body: String, productUrl: String?) {
        val channelId = "deal_alerts_channel"
        val notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                channelId,
                "Alertas de Precios",
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = "Notificaciones de ofertas alcanzadas en DealRadar"
            }
            notificationManager.createNotificationChannel(channel)
        }

        val intent = if (!productUrl.isNullOrEmpty()) {
            Intent(Intent.ACTION_VIEW, Uri.parse(productUrl))
        } else {
            Intent(this, MainActivity::class.java)
        }
        intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP)

        val pendingIntent = PendingIntent.getActivity(
            this,
            System.currentTimeMillis().toInt(),
            intent,
            PendingIntent.FLAG_ONE_SHOT or PendingIntent.FLAG_IMMUTABLE
        )

        val notificationBuilder = NotificationCompat.Builder(this, channelId)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle(title)
            .setContentText(body)
            .setAutoCancel(true)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setContentIntent(pendingIntent)

        notificationManager.notify(System.currentTimeMillis().toInt(), notificationBuilder.build())
    }
}

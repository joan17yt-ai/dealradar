package com.dealradar.app.data.api

import com.dealradar.app.data.model.*
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.*
import java.util.concurrent.TimeUnit

interface DealRadarApi {
    @GET("api/deals/feed")
    suspend fun getDealsFeed(@Query("category") category: String? = null): DealsFeedResponse

    @GET("api/search")
    suspend fun searchProducts(@Query("q") query: String): SearchResponse

    @GET("api/alerts")
    suspend fun getUserAlerts(@Query("device_id") deviceId: String): AlertsListResponse

    @POST("api/alerts")
    suspend fun createAlert(@Body request: CreateAlertRequest): Map<String, Any>

    @DELETE("api/alerts/{alert_id}")
    suspend fun deleteAlert(@Path("alert_id") alertId: Int): Map<String, Any>

    @POST("api/user/register")
    suspend fun registerDevice(@Body request: DeviceRegisterRequest): Map<String, Any>

    @GET("api/user/savings")
    suspend fun getUserSavings(@Query("device_id") deviceId: String): UserSavingsResponse
}

object DealRadarApiClient {
    // Reemplazar con la URL de producción de tu servidor backend en Render/Railway
    // Para emulador local de Android se usa http://10.0.2.2:8000/
    var baseUrl: String = "https://dealradar-backend.onrender.com/"

    private val logging = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BODY
    }

    private val okHttpClient = OkHttpClient.Builder()
        .addInterceptor(logging)
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(20, TimeUnit.SECONDS)
        .build()

    val api: DealRadarApi by lazy {
        Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(DealRadarApi::class.java)
    }
}

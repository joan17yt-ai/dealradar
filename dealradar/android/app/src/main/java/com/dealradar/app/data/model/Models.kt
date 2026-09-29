package com.dealradar.app.data.model

data class Deal(
    val id: Int,
    val title: String,
    val store: String,
    val category: String,
    val current_price_cop: Double,
    val original_price_cop: Double,
    val discount_percentage: Int,
    val product_url: String,
    val image_url: String?,
    val badge: String
)

data class DealsFeedResponse(
    val deals: List<Deal>
)

data class ScrapedItem(
    val title: String,
    val price_cop: Double,
    val original_price_cop: Double?,
    val discount_percentage: Int,
    val store: String,
    val product_url: String,
    val image_url: String?,
    val is_available: Boolean
)

data class SearchResponse(
    val query: String,
    val total_results: Int,
    val results: List<ScrapedItem>
)

data class AlertItem(
    val id: Int,
    val product_title: String,
    val query_keyword: String,
    val category: String,
    val target_price_cop: Double,
    val current_best_price_cop: Double?,
    val best_store: String?,
    val product_url: String?,
    val image_url: String?,
    val is_active: Boolean,
    val created_at: String?
)

data class AlertsListResponse(
    val alerts: List<AlertItem>
)

data class CreateAlertRequest(
    val device_id: String,
    val product_title: String,
    val query_keyword: String,
    val category: String = "general",
    val target_price_cop: Double,
    val current_best_price_cop: Double? = null,
    val best_store: String? = null,
    val product_url: String? = null,
    val image_url: String? = null
)

data class DeviceRegisterRequest(
    @com.google.gson.annotations.SerializedName("device_id")
    val deviceId: String,
    val fcm_token: String? = null
)

data class UserSavingsResponse(
    val total_saved_cop: Double,
    val alerts_count: Int,
    val rank: String
)

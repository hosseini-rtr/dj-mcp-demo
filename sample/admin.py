from django.contrib import admin


from .models import Customer, Order

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("id","name","email","created_at")
    
    search_fields = ["name"]
    ordering = ("-created_at",)
    
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "customer",
        "amount",
        "status",
        "created_at",
    )
    list_filter = (
        "status",
        "created_at",
    )
    search_fields = (
        "customer__name",
        "customer__email",
    )
    autocomplete_fields = ("customer",)
    ordering = ("-created_at",)
from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
# Register your models here.


from foodie.models import Vendors, Food, TelegramUser, Order, OrderItem, Cart, Location, Waiter

@admin.register(Order)
class CartOrderAdmin(ImportExportModelAdmin):
    # inlines = [CartOrderItemsInlineAdmin]
    # search_fields = ['oid', 'full_name', 'email', 'mobile']
    # list_editable = ['order_status', 'payment_status']
    list_filter = ['status','created_at']
    list_display = ['user', 'created_at','status','total_amount','delivery_no','delivery_address']

admin.site.register(Vendors)
admin.site.register(Food)
admin.site.register(TelegramUser)
admin.site.register(Cart)
admin.site.register(OrderItem)
admin.site.register(Location)
# admin.site.register(Waiter)



          
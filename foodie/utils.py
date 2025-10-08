# # bot/utils/telegram.py
# from asgiref.sync import sync_to_async
# from foodie.models import TelegramUser, Order, OrderItem, Vendors, Food
# import os
# PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY')

# @sync_to_async(thread_sensitive=True)
# def get_user_by_telegram_id(telegram_id):
#     """
#     Fetch a TelegramUser object by telegram_id.
#     Returns None if not found.
#     """
#     return TelegramUser.objects.filter(telegram_id=telegram_id).first()


# @sync_to_async(thread_sensitive=True)
# def get_order(telegram_id, created_at,status,total_amount, delivery_no, delivery_address):
#     user, _ = TelegramUser.objects.get_or_create(telegram_id=telegram_id)
#     return Order.objects.create(
#         telegram_id=user,
#         created_at=created_at,
#         status=status,
#         total_amount = total_amount,
#         delivery_no=delivery_no,
#         delivery_address=delivery_address,
#     )

# @sync_to_async(thread_sensitive=True)
# def get_orderitem(order_id,  food, quantity, price_at_order_time , vendor_id):
#     order = Order.objects.get(id=order_id)
#     vendor = Vendors.objects.get(id=vendor_id)
#     return OrderItem.objects.create(
#         order_id=order,
#         food=food,
#         quantity=quantity,
#         price_at_order_time=price_at_order_time,
#         vendor_id=vendor
#     )
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json
from .models import Order
from .models import Cart

@csrf_exempt
def paystack_webhook(request):
    data = json.loads(request.body.decode('utf-8'))
    
    # Paystack sends various events, we only care about successful payments
    if data.get("event") == "charge.success":
        payment_data = data.get("data", {})
        metadata = payment_data.get("metadata", {})
        telegram_id = metadata.get("telegram_id")
        order_id = metadata.get("order_id")
        cart_id = metadata.get("cart_id")
        # cart = metadata.get("cart")

        try:
            order = Order.objects.get(id=order_id, user__telegram_id=telegram_id)
            order.status = "paid"
            order.save()
            Cart.objects.filter(id=cart_id, user__telegram_id=telegram_id).delete()
            print(f"✅ Order {order_id} for user {telegram_id} marked as paid.")
        except Order.DoesNotExist:
            print("⚠️ Order not found or mismatch.")

    return HttpResponse(status=200)

# import json
# import requests
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from .models import Order  # your model

# PAYSTACK_SECRET_KEY = "sk_test_xxxxx"  # replace with your secret key

# @csrf_exempt
# def paystack_webhook(request):
#     try:
#         payload = json.loads(request.body.decode('utf-8'))
#         event = payload.get("event")

#         if event == "charge.success":
#             reference = payload["data"]["reference"]
#             amount = payload["data"]["amount"] / 100  # Paystack sends amount in kobo

#             # ✅ Find the order and update it
#             order = Order.objects.filter(reference=reference).first()
#             if order:
#                 order.status = "paid"
#                 order.save()

#         return JsonResponse({"status": "success"}, status=200)

#     except Exception as e:
#         print("Webhook error:", e)
#         return JsonResponse({"status": "error"}, status=400)

# import json
# import requests
# from django.views.decorators.csrf import csrf_exempt
# from django.http import JsonResponse
# from django.conf import settings
# from foodie.models import Food, TelegramUser, Order, OrderItem
# import os 
# import random
# from django.shortcuts import redirect


# from dotenv import load_dotenv
# load_dotenv()
# PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY')

# BOT_USERNAME = "chophive_bot"
# @csrf_exempt
# def verify_payment(request):
#     reference = None

#     # Handle GET (user redirected from Paystack)
#     if request.method == "GET":
#         reference = request.GET.get("reference")

#     # Handle POST (Paystack webhook)
#     elif request.method == "POST":
#         try:
#             payload = json.loads(request.body)
#         except json.JSONDecodeError:
#             return JsonResponse({"error": "Invalid JSON"}, status=400)

#         reference = payload.get("data", {}).get("reference")

#     if not reference:
#         return JsonResponse({"error": "No reference provided"}, status=400)

#     # Verify payment with Paystack API
#     headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
#     verify_res = requests.get(
#         f"https://api.paystack.co/transaction/verify/{reference}",
#         headers=headers
#     )
#     res_data = verify_res.json()
#     print("Paystack verification:", json.dumps(res_data, indent=2))
    
#     status_from_data = res_data.get("data", {}).get("status", "").lower()
#     if status_from_data == "success":
#         metadata = res_data["data"].get("metadata", {})

#         # If Paystack returns metadata as a string, parse it
#         if isinstance(metadata, str):
#             try:
#                 metadata = json.loads(metadata)
#             except json.JSONDecodeError:
#                 metadata = {}

#         telegram_id = metadata.get("telegram_id")
#         cart_items = metadata.get("cart", [])

#         if telegram_id and cart_items:
#             tg_user, _ = TelegramUser.objects.get_or_create(telegram_id=telegram_id)

#             order = Order.objects.create(
#                 telegram_id=tg_user,  # ✅ correct FK name
#                 # total_amount=sum(
#                 #     int((item["price"]) * int(item["portions"]) for item in cart_items)
#                 # ),
#                 total_amount = sum(int(item["price"]) for item in cart_items),
#                 delivery_no=random.randint(10000, 99999),
#                 status="paid",
#             )

#             for item in cart_items:
#                 try:
#                     food_obj = Food.objects.get(id=item["food_id"])
#                 except Food.DoesNotExist:
#                     continue
#                 OrderItem.objects.create(
#                     order=order,
#                     food=food_obj,
#                     quantity=item["portions"],
#                     price_at_order_time=item["price"],
#                     vendor=food_obj.vendor,
#                 )

#             BOT_USERNAME = "chophive_bot"
#             return redirect(f"https://t.me/{BOT_USERNAME}?")

#         return JsonResponse({
#             "status": "success",
#             "message": "Payment verified and order created",
#             "reference": reference
#         })
        

#     return JsonResponse({"status": "failed"}, status=400)


#     # if res_data.get("data", {}).get("status") == "success":
#     #     metadata = res_data["data"].get("metadata", {})
#     #     telegram_id = metadata.get("telegram_id")
#     #     cart_items = metadata.get("cart", [])

#     #     # ✅ Save Order to DB
#     #     if telegram_id and cart_items:
#     #         tg_user, _ = TelegramUser.objects.get_or_create(
#     #             telegram_id=telegram_id
#     #         )

#     #         order = Order.objects.create(
#     #             telegram_id=tg_user,
#     #             total_amount=sum(
#     #                 item["price"] * item["portions"] for item in cart_items
#     #             ),
#     #             delivery_no=random.randint(10000,99999),# last 5 digits of ref
#     #             status="paid",
#     #         )

#     #         for item in cart_items:
#     #             try:
#     #                 food_obj = Food.objects.get(id=item["food_id"])
#     #             except Food.DoesNotExist:
#     #                 continue
#     #             OrderItem.objects.create(
#     #                 order=order,
#     #                 food=food_obj,
#     #                 quantity=item["portions"],
#     #                 price_at_order_time=item["price"],
#     #                 vendor=food_obj.vendor,
#     #             )

#     #     return JsonResponse({
#     #         "status": "success",
#     #         "message": "Payment verified and order created",
#     #         "reference": reference
#     #     })

#     # return JsonResponse({"status": "failed"}, status=400)

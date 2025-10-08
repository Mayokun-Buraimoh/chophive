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

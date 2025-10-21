import os
import django

# Set up Django environment for ORM usage
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TelegramBot.settings')
django.setup()


from telegram import Update
from telegram.ext import ContextTypes
import traceback
import requests
import random
import uuid
import asyncio
from dotenv import load_dotenv
load_dotenv()


from django.core.exceptions import ObjectDoesNotExist

PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY')
PAYSTACK_PUBLISHABLE = os.getenv('PAYSTACK_PUBLIC_KEY')



from telegram import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import PicklePersistence,ApplicationBuilder, Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters, ContextTypes
from typing import Final
from foodie.models import Vendors, Food, TelegramUser, Order, OrderItem, Cart, Location, Waiter, WaiterAssignmentTracker
from asgiref.sync import sync_to_async
import asyncio, random, uuid, requests
# Telegram bot token and username

TOKEN = os.getenv("TELEGRAM_KEY")
BOT_USERNAME: Final = '@mayviccbot'

#chophive group chat id
CHAT_ID = "-4929820976"

# ADDRESS = 1
HALL, ADDRESS = range(2)
ASK_PHONE, ASK_EMAIL = range(2)
# Main reply keyboard for general use
main_keyboard = [
    ["Place an Order", "View cart"],
    ["Become a waiter", "Customer support"],
    ["Order History", "Delivery Details"],
    ["Clear Cart", "Checkout"],
]

reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)

# =========================================
# ORM FUNCTIONS
# =========================================

@sync_to_async(thread_sensitive=True)
def get_vendor_names_with_ids():
    return list(Vendors.objects.values_list('id', 'name'))

@sync_to_async(thread_sensitive=True)
def get_vendor_by_id(vendor_id):
    return Vendors.objects.get(id=vendor_id)

@sync_to_async(thread_sensitive=True)
def get_foods_by_vendor(vendor):
    return list(Food.objects.filter(vendor=vendor).values_list('id', 'name', 'price'))

@sync_to_async(thread_sensitive=True)
def get_food_by_id(food_id: int):
    return Food.objects.get(id=food_id)

@sync_to_async(thread_sensitive=True)
def update_or_create_telegram_user(telegram_id):
    TelegramUser.objects.update_or_create(
        telegram_id=telegram_id
        # defaults={"phone": phone}
    )

@sync_to_async(thread_sensitive=True)
def get_user_by_telegram_id(telegram_id):
    return TelegramUser.objects.filter(telegram_id=telegram_id).first()

@sync_to_async(thread_sensitive=True)
def get_location():
    return list(Location.objects.values("id", "name"))

from asgiref.sync import sync_to_async

@sync_to_async
def get_next_waiter(location):
    waiters = list(Waiter.objects.filter(location=location).order_by("id"))
    if not waiters:
        return None  # No waiter for this location

    # Get or create the tracker for this location
    tracker, _ = WaiterAssignmentTracker.objects.get_or_create(location=location)

    # Move to next waiter index (round-robin)
    tracker.last_assigned_index = (tracker.last_assigned_index + 1) % len(waiters)
    tracker.save()

    # Return selected waiter
    return waiters[tracker.last_assigned_index]

@sync_to_async(thread_sensitive=True)
def get_order(telegram_id):
    user, _ = TelegramUser.objects.get_or_create(telegram_id=telegram_id)
    return list(
        Order.objects.filter(user=user)
 # optional, if you want related data
    )



@sync_to_async(thread_sensitive=True)
def create_order(telegram_id,status,total_amount, delivery_no, delivery_address, waiter):
    user, _ = TelegramUser.objects.get_or_create(telegram_id=telegram_id)
    return Order.objects.create(
        user=user,
        # created_at=created_at,
        status=status,
        total_amount = total_amount,
        delivery_no=delivery_no,
        delivery_address=delivery_address,
        waiter=waiter,
     
    )

@sync_to_async(thread_sensitive=True)
def get_orderitem(order,  food, quantity, price_at_order_time , vendor):
    # order = Order.objects.get(id=order_id)
    # vendor = Vendors.objects.get(id=vendor_id)
    return OrderItem.objects.create(
        order=order,
        food=food,
        quantity=quantity,
        price_at_order_time=price_at_order_time,
        vendor=vendor
    )

@sync_to_async(thread_sensitive=True)
def save_phone(telegram_id, phone):
    # try:
    user = TelegramUser.objects.get(telegram_id=telegram_id)
    user.phone = phone
    user.save()
    # except ObjectDoesNotExist:
    #     user = TelegramUser.objects.create(
    #         telegram_id=telegram_id,
    #         phone=phone,
    #     )
    # return user

@sync_to_async(thread_sensitive=True)
def save_email(telegram_id, email):
    # try:
    user = TelegramUser.objects.get(telegram_id=telegram_id)
    user.email = email
    user.save()
    # except ObjectDoesNotExist:
    #     user = TelegramUser.objects.create(
    #         telegram_id=telegram_id,
    #         email=email,
    #     )
    # return user

@sync_to_async(thread_sensitive=True)
def save_cart_item(telegram_id, food_id, portions, vendor_id, plate_no):
    user, _ = TelegramUser.objects.get_or_create(telegram_id=telegram_id)
    food = Food.objects.get(id=food_id)
    vendor = Vendors.objects.get(id=vendor_id)
    Cart.objects.create(
        user=user,
        food=food,
        portions=portions,
        vendor=vendor,
        plate_no=plate_no
    )


@sync_to_async(thread_sensitive=True)
def get_food_prices(food_names):
    return dict(
        Food.objects.filter(name__in=food_names)
        .values_list('name', 'price')  # returns dict: {name: price}
    )


@sync_to_async(thread_sensitive=True)
def get_cart_items(telegram_id):
    user = TelegramUser.objects.filter(telegram_id=telegram_id).first()
    if not user:
        return []
    return list(
        Cart.objects.filter(user=user).select_related('food__vendor', 'vendor').order_by("plate_no")
    )

@sync_to_async(thread_sensitive=True)
def get_cart_item(item_id):
    return Cart.objects.select_related('food__vendor', 'vendor').filter(id=item_id).first()

@sync_to_async(thread_sensitive=True)
def edit_cart_item(item_id, portions):
    return Cart.objects.filter(id=item_id).update(portions=portions)

@sync_to_async(thread_sensitive=True)
def delete_cart_item(item_id):
    return Cart.objects.filter(id=item_id).delete()


    
@sync_to_async(thread_sensitive=True)
def clear_cart_items(telegram_id):
    user = TelegramUser.objects.filter(telegram_id=telegram_id).first()
    if user:
        Cart.objects.filter(user=user).delete()


@sync_to_async(thread_sensitive=True)
def checkout_items(telegram_id):
    user = TelegramUser.objects.filter(telegram_id=telegram_id).first()
    if not user:
        return []
    return list(
        Cart.objects.filter(user=user).select_related('food')
    )
# =========================================
# COMMAND HANDLERS
# =========================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    username = update.effective_user.username
    
    await update_or_create_telegram_user(user)
    
    await update.message.reply_text(
        f"👋Welcome to Chophive {username}\n\n  Thank you for choosing the number one food delivery service at Bowen University\n\n We've registered you using your telegram details. You can now place your orders\n\nSay no to long queues with ChopHive ",
        reply_markup=reply_markup
    )
    
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        '🆘 I can help you with these options. Choose below:',
        reply_markup=reply_markup
    )

# =========================================
# MESSAGE HANDLER
# =========================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    print(f'User ({update.message.chat.id}) in private: "{text}"')
  
    if text == "place an order":
        
        await ask_details(update, context)
        return
    
    if text == "view cart":
        await handle_view_cart(update, context)
        return
    
    if text == "clear cart":
        await clear_cart(update, context)
        return
    
    if text == "delivery details":
        await delivery_details(update, context)
        return
   
    # if text == "order history":
    #     await order_history(update, context)
    #     return

    if text == "checkout":
        await checkout(update, context)
        return
    
    if text.isdigit():
        await handle_portion_input(update, context)
        return

    responses = {
        "become a waiter": "🍽 Awesome! We’ll contact you with more details. Contact chophive01@gmail.com",
        "customer support": "📞 Connecting you to support, Email us here: chophive01@gmail.com",
    }

    reply = responses.get(text, '🤔 Sorry, I didn’t understand that. Choose an option below.')
    await update.message.reply_text(reply, reply_markup=reply_markup)

# =========================================
# VENDOR & FOOD FLOW
# =========================================

async def ask_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    user = await get_user_by_telegram_id(telegram_id)
    
    # if not user:
    #     await update.message.reply_text("Please register")
    #     return ConversationHandler.END
    
    # if user.phone and user.email:
    #     await send_vendor_list(update, context)
    if not user:
        await update_or_create_telegram_user(telegram_id)
        user = await get_user_by_telegram_id(telegram_id)
       
    if user.phone and user.email:
        await send_vendor_list(update, context)
        return ConversationHandler.END
     
    # if user and user.phone and user.email:
    #     await send_vendor_list(update, context)
    #     return
    
    if not user.phone:
        await update.message.reply_text(
        "🏠 Please enter your phone number\n",
        parse_mode="Markdown")
        return ASK_PHONE
    
    if not user.email:
        await update.message.reply_text(
        "🏠 Please enter your email address\n",
        parse_mode="Markdown")
        return ASK_EMAIL
          
async def send_vendor_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    # user = await get_user_by_telegram_id(telegram_id)
    # if not user:
    #     await update.message.reply_text("Please register")
    #     return ConversationHandler.END
    
    # if not user.phone:
    #     await update.message.reply_text(
    #     "🏠 Please enter your phone number\n",
    #     parse_mode="Markdown")
    #     return ASK_PHONE
    
    # if not user.email:
    #     await update.message.reply_text(
    #     "🏠 Please enter your email address\n",
    #     parse_mode="Markdown")
    #     return ASK_EMAIL
            
    vendor_names = await get_vendor_names_with_ids()
    if not vendor_names:
        await update.message.reply_text("❌ No vendors found at the moment.")
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(name, callback_data=f'vendor_{vendor_id}')]
                for vendor_id, name in vendor_names]
    markup = InlineKeyboardMarkup(keyboard)
    
    # if hasattr(update, "callback_query") and update.callback_query:
    #     await update.callback_query.edit_message_text(
    #         "🛒 Select a vendor to order from:", reply_markup=markup
    #    )
    #     return  # ✅ stop here so it won’t send twice
    # else:
    #     await update.message.reply_text(
    #         "🛒 Select a vendor to order from:", reply_markup=markup
    #     )
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text="🛒 Select a vendor to order from:",
            reply_markup=markup
        )
    else:
        await update.message.reply_text(
            text="🛒 Select a vendor to order from:",
            reply_markup=markup
        )

        
    return ConversationHandler.END
    # await update.message.reply_text("🛒 Select a vendor to order from:", reply_markup=markup)

async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        phone = update.message.text.strip()
    
    # await send_vendor_list(update, context)
    await save_phone(telegram_id, phone)
    await update.message.reply_text("✅ Phone number saved.")

    user = await get_user_by_telegram_id(telegram_id)
    if not user.email:
        await update.message.reply_text("📧 Please enter your email address:")
        return ASK_EMAIL
    
        # await save_phone(telegram_id,phone)
        # await update.message.reply_text("✅ Phone number saved.")
        
    await send_vendor_list(update, context)

    return ConversationHandler.END

async def handle_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    email = update.message.text.strip()
    
    await save_email(telegram_id, email)
    await update.message.reply_text("✅ Email saved.")
    
    user = await get_user_by_telegram_id(telegram_id)
    if not user.phone:
        await update.message.reply_text("📱 Please enter your phone number:")
        return ASK_PHONE
    
    await send_vendor_list(update, context)
    return ConversationHandler.END

async def handle_vendor_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # ✅ Handle Back button
    if query.data == "go_back_to_vendors":
        await go_back_to_vendors(update, context)
        return
    
    vendor_id = int(query.data.replace("vendor_", ""))
    context.user_data['last_selected_vendor'] = vendor_id

    vendor = await get_vendor_by_id(vendor_id)
    if not vendor:
        await query.edit_message_text("❗ Vendor not found. Please try again.")
        return
    
    number_keyboard = [
        [InlineKeyboardButton(str(i), callback_data=f"plates_{i}")]
        for i in range(1, 7)
    ]
    
    number_keyboard.append(
        [InlineKeyboardButton("⬅️ Back", callback_data="go_back_to_vendors")]
    )
     
    number_markup = InlineKeyboardMarkup(number_keyboard)
    await query.edit_message_text(
        f"🍽 How many packs of food would you like to order from *{vendor.name}*?",
        parse_mode="Markdown",
        reply_markup=number_markup
    )
 
async def go_back_to_vendors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Reuse send_vendor_list but modify it to handle both update types
    await send_vendor_list(update, context)


async def handle_plate_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "go_back_to_plates":
        await go_back_to_vendors(update, context)
        return
    
    plates = int(query.data.replace("plates_", ""))
    vendor_id = context.user_data.get("last_selected_vendor")
    
    
    
    if "cart" not in context.user_data:
        context.user_data['cart'] = {}
        context.user_data['total_plates'] = 0
        context.user_data['current_plate'] = 0
        
    start_plate = context.user_data['total_plates'] + 1
    end_plate = context.user_data['total_plates'] + plates
    for i in range(start_plate, end_plate + 1):
        context.user_data['cart'][i] = []
        
    context.user_data['total_plates'] = end_plate
    context.user_data['current_plate'] = start_plate
        
    # context.user_data['total_plates'] = plates
    # context.user_data['current_plate'] = 1
    # context.user_data['cart'] = {i: [] for i in range(1, plates + 1)}  # dict per plate

    vendor = await get_vendor_by_id(vendor_id)
    foods = await get_foods_by_vendor(vendor)
    if foods:
        message = f"🍽 *First plate * *{vendor.name} Menu:*\n\n👇 Tap a food item to order:"
        keyboard = [[InlineKeyboardButton(f"{name} - ₦{price}", callback_data=f"food_{food_id}")]
                    for food_id, name, price in foods]
        
        keyboard.append(
            [InlineKeyboardButton("⬅️ Back", callback_data="go_back_to_vendors")]
        )
        markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, parse_mode="Markdown", reply_markup=markup)
    else:
        await query.edit_message_text(f"😞 No food items found for *{vendor.name}*.", parse_mode="Markdown")
        
async def handle_food_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # if query.data == "go_back_to_food":
    #     await go_back_to_food(update, context)
    #     return
    
    food_id = int(query.data.replace("food_", ""))
    food = await get_food_by_id(food_id)
    context.user_data['selected_food'] = {'id': food.id, 'name': food.name, 'price': food.price}
    number_keyboard = [
        [InlineKeyboardButton(str(i), callback_data=f"portions_{i}")]
        for i in range(1, 7)
    ]
    number_keyboard.append(
            [InlineKeyboardButton("⬅️ Back", callback_data="continue_shopping")]
        )
    number_markup = InlineKeyboardMarkup(number_keyboard)
    # message = f"✅ You selected *{food.name}*\nPrice: ₦{food.price}\n\nHow many portions would you like? (Type a number)"
    # keyboard = [[InlineKeyboardButton()]
    #     markup = InlineKeyboardMarkup(keyboard)]
    await query.edit_message_text(
        f"✅ You selected *{food.name}*\nPrice: ₦{food.price}\n\n*How many spoons / portions would you like? (Select a number)*",
        parse_mode="Markdown",
        reply_markup=number_markup
    )


async def handle_portion_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    try:
        # portions = int(update.message.text.strip())
        query = update.callback_query
        await query.answer()
        data = query.data
        
        # Check if user is editing or adding
        
    
        # if query.data == "go_back_to_food":
        #     await handle_food_selection(update, context)
        #     return
        
        editing = data.startswith("edit_portions_")
        
        if editing:
            portions = int(data.replace("edit_portions_", ""))
        else:
            portions = int(data.replace("portions_", ""))

        # portions = int(data.replace("edit_portions_", "").replace("portions_", ""))
        
        if editing:
            item_id = context.user_data.get("edit_item_id")
            # await edit_cart_item(item_id, portions)

            if not item_id:
                await query.edit_message_text("⚠️ No item found to edit.")
                return
            
            await edit_cart_item(item_id, portions)
        
    
            await query.edit_message_text(f"✅ Updated to {portions} portion(s)!")
            await handle_view_cart(update, context)
            return
        
        food = context.user_data.get('selected_food')
        if not food:
            await update.message.reply_text("❗ You haven't selected a food item yet.")
            return
        
        total_price = food['price'] * portions
        plate_no = context.user_data["current_plate"]
        
        context.user_data['portion_count'] = portions
        context.user_data["cart"][plate_no].append({
            "food": food["name"],
            "portion_count": portions,
            "total_price": total_price,
        })
        # context.user_data.update({'portion_count': portions, 'total_price': total_price})

        keyboard = [
            [InlineKeyboardButton("🛒 Add to Cart", callback_data="add_to_cart")],
            [InlineKeyboardButton("🍽 Add more food *Go back* ", callback_data="continue_shopping")],
            [InlineKeyboardButton("🧾 Checkout", callback_data="checkout")],
            [InlineKeyboardButton("🧾 Next Plate", callback_data="next_plate")]
        ]
        # keyboard.append(
        #     [InlineKeyboardButton("⬅️ Back", callback_data="go_back_to_food")]
        # )
        markup = InlineKeyboardMarkup(keyboard)
        
        
        await query.message.reply_text(
            f"🧾 *{food['name']}* x {portions} portion(s)\nTotal: ₦{total_price}\n\nWhat next?",
            parse_mode="Markdown",
            reply_markup=markup
        )
    except ValueError:
        await update.message.reply_text("❗ Please type a valid number for portions.")

# async def go_back_to_food(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()

#     # Reuse send_vendor_list but modify it to handle both update types
#     await handle_food_selection(update, context)

async def handle_next_plate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    current = context.user_data["current_plate"]
    total = context.user_data["total_plates"]

    if current < total:
        context.user_data["current_plate"] += 1
        vendor_id = context.user_data.get("last_selected_vendor")
        vendor = await get_vendor_by_id(vendor_id)
        foods = await get_foods_by_vendor(vendor)

        # Build food buttons
        keyboard = [
            [InlineKeyboardButton(f"{name} - ₦{price}", callback_data=f"food_{food_id}")]
            for food_id, name, price in foods
        ]
        markup = InlineKeyboardMarkup(keyboard)

        # Ask user to select food for the new plate
        await query.edit_message_text(
            f"➡️ Now filling Plate {context.user_data['current_plate']} of {total}\n\n"
            f"🍽 *{vendor.name} Menu:*",
            parse_mode="Markdown",
            reply_markup=markup
        )
    else:
        await query.edit_message_text(
            "✅ All plates completed!\n🧾 Ready to checkout?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🧾Checkout", callback_data= "checkout")]
            ])
        )
        
async def handle_cart_or_continue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    vendor_id = context.user_data.get('last_selected_vendor')
    
    query = update.callback_query
    await query.answer()
    choice = query.data

    food = context.user_data.get('selected_food')
    portions = context.user_data.get('portion_count')
    
    plates = context.user_data.get('current_plate')
    if choice == "add_to_cart":
        if not food or not portions:
            await query.edit_message_text("❗ Missing food or portion info. Please start again.")
            return
        
        # cart = context.user_data.get('cart', [])
        await save_cart_item(telegram_id, food['id'], portions, vendor_id, plates)

        # cart.append({
        #     'food_id': food['id'],
        #     'name': food['name'],
        #     'portions': portions,
        #     'vendor_id': vendor_id
        # })

        cart = await get_cart_items(telegram_id)
         
        
        

        # context.user_data['cart'] = cart
        # Save to database
        # await save_cart_item(telegram_id, food['id'], portions)

        # Refresh cart count from DB
        # updated_cart = await get_cart_items(telegram_id)

        vendor_id = context.user_data.get('last_selected_vendor')
        if not vendor_id:
            await query.edit_message_text("❗ Vendor info missing. Please start again.")
            return
        
        vendor = await get_vendor_by_id(vendor_id)
        foods = await get_foods_by_vendor(vendor)
        keyboard = [
            # [InlineKeyboardButton("⬅️ Back to Food", callback_data="go_back_to_food")],
            [InlineKeyboardButton("⬅️ Back to Food(** Add more food **)", callback_data="continue_shopping")],
            [InlineKeyboardButton("🧾 Checkout", callback_data="checkout")],
        ]
        markup = InlineKeyboardMarkup(keyboard)

        # keyboard = [[InlineKeyboardButton(f"{name} - ₦{price}", callback_data=f"food_{food_id}")]
        #             for food_id, name, price in foods]
        markup = InlineKeyboardMarkup(keyboard)
        
        message = "🛒 *Your Cart:*\n\n"
        total_sum = 0
    
        current_plate = None
        for i, item in enumerate(cart, 1):
            food_name = item.food.name
            vendor_name = item.vendor.name
            portions = item.portions
            price = item.food.price
        # current_plate = None
            if current_plate != item.plate_no:
                current_plate = item.plate_no
                message += f"\n Plate {current_plate}:\n"
        # price = price_map.get(food_name, 0)  # fallback to 0 if missing
            total = price * portions
            message += f"{i}. ({vendor_name}) x {food_name} x {portions} → ₦{total}\n"
            total_sum += total
        
        message += f"\n💰 *Total: ₦{total_sum}*"

        
        await query.edit_message_text(
            # *{food['name']}*, {cart} added to cart!\n🛒 You now have {len(cart)} item(s).\n 
            f"✅ {message}",
            parse_mode="Markdown", reply_markup=markup
        )

    elif choice == "continue_shopping":
        vendor_id = context.user_data.get('last_selected_vendor')
        if not vendor_id:
            await query.edit_message_text("❗ Vendor info missing. Please start again.")
            return
        vendor = await get_vendor_by_id(vendor_id)
        foods = await get_foods_by_vendor(vendor)
        keyboard = [[InlineKeyboardButton(f"{name} - ₦{price}", callback_data=f"food_{food_id}")]
                    for food_id, name, price in foods]
        markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("🍽 Select another food item:", reply_markup=markup)

    elif choice == "checkout":
        receipt = await checkout(update, context)
        await update.callback_query.message.reply_text(receipt, parse_mode="Markdown")

        
async def handle_view_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    cart = await get_cart_items(telegram_id)
    if not cart:
        await update.message.reply_text("🛒 Your cart is empty.")
        return

    # food_names = [item['name'] for item in cart]
    # price_map = await get_food_prices(food_names)  # {name: price}

    message = "🛒 *Your Cart:*\n\n"
    total_sum = 0
    
    delivery_fee = None
    total_plate_cost = 0
    current_plate = None
    plate_count = 0
    
    keyboard = []

    for i, item in enumerate(cart, 1):
        food_name = item.food.name
        vendor_name = item.vendor.name
        portions = item.portions
        price = item.food.price
        delivery_fee = item.vendor.delivery_fee
        # current_plate = None
        if current_plate != item.plate_no:
            current_plate = item.plate_no
            plate_count += 1
            message += f"\n *Plate {current_plate}:*\n"

        
        # price = price_map.get(food_name, 0)  # fallback to 0 if missing
        total = price * portions
        message += f"{i}. ({vendor_name}) x {food_name} x {portions} → ₦{total}\n"
        total_sum += total
        
        keyboard.append([
            InlineKeyboardButton(
                f"{vendor_name} {food_name} × {portions} → ₦{total}",
                callback_data=f"manage_{item.id}"
            )
        ])

    plate_price = cart[0].vendor.plate_price if cart else 0
    total_plate_cost = plate_price * plate_count
  
    message += f" *Delivery fee is {delivery_fee}*\n"
    message += f" *Cost of the pack {total_plate_cost}*\n"
    message += f"\n\n💰 *Total: ₦{total_sum + delivery_fee + total_plate_cost}*\n"
    message += "🚫 *Tap any item below to edit or remove it*"
    
    keyboard.append([
        InlineKeyboardButton("🧹 Clear Cart", callback_data="clear_cart")
    ])


                    
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, parse_mode="Markdown", reply_markup=reply_markup)


async def handle_manage_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    item_id = int(query.data.split("_")[1])
    item = await get_cart_item(item_id)  # Create this helper to fetch a single item

    if not item:
        await query.edit_message_text("⚠️ Item not found in your cart.")
        return

    text = (
        f"🍔 *{item.food.name}*\n"
        f"Vendor: {item.vendor.name}\n"
        f"Price: ₦{item.food.price}\n"
        f"Current Quantity: {item.portions}\n\n"
        "What would you like to do?"
    )

    keyboard = [
        [
            InlineKeyboardButton("✏️ Edit Quantity", callback_data=f"edit_{item.id}"),
            InlineKeyboardButton("🗑 Delete Item", callback_data=f"delete_{item.id}")
        ],
        [InlineKeyboardButton("🔙 Back to Cart", callback_data="handle_view_cart")]
    ]

    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    
async def handle_edit_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    item_id = int(query.data.split("_")[1])
    item = await get_cart_item(item_id)

    if not item:
        await query.edit_message_text("⚠️ Item not found.")
        return
    
    context.user_data["edit_item_id"] = item_id
    
    number_keyboard = [
        [InlineKeyboardButton(str(i), callback_data=f"edit_portions_{i}")] for i in range(1, 7)
    ]
    
    number_keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="continue_shopping")])
    reply_markup = InlineKeyboardMarkup(number_keyboard)

    await query.edit_message_text(
        "✏️ *Select new portion count for this item:*",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )
    
    
    # Optionally refresh the cart
 

async def handle_delete_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    item_id = int(query.data.split("_")[1])
    
    # Delete from database (implement helper)
    await delete_cart_item(item_id)
    
    await query.edit_message_text("🗑 Item deleted successfully!")
    
    # Optionally refresh the cart
    await handle_view_cart(update, context)

async def clear_cart(update:Update, context:ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    await clear_cart_items(telegram_id)
    context.user_data['cart'] = {}
    context.user_data['total_plates'] = 0
    context.user_data['current_plate'] = 0
    
    if update.message:
        await update.message.reply_text("🛒 You have cleared your cart, continue shopping.")
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.message.reply_text("🛒 You have cleared your cart, continue shopping.")
    
async def checkout(update:Update, context:ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    cart = await get_cart_items(telegram_id)
    
    
    if hasattr(update, "callback_query") and update.callback_query:
        query = update.callback_query
        await query.answer()
        target_message = query.message
    else:
        target_message = update.message
        
    if not cart:
        await target_message.reply_text(
            " your cart is empty, add items to checkout",
            # reply_markup=reply_markup
        )
        return ConversationHandler.END
    
    locations = await get_location()
    
    keyboard = [
        [InlineKeyboardButton(loc["name"], callback_data=f"location_{loc['id']}")]
        for loc in locations
    ]
    # location_names = [[loc["name"]] for loc in locations]  # make it button-friendly
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # reply_markup = [
            # [InlineKeyboardButton("⬅️ Back to Food", callback_data="go_back_to_food")],
            # [InlineKeyboardButton(loc["name"], callback_data=f"location_{loc['id']}")]
            # for loc in locations
            
            # [InlineKeyboardButton("🧾 Checkout", callback_data="checkout")],
        # ]
    # reply_markup = ReplyKeyboardMarkup(location_names, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        "🏠 Please select your hall \n",
        reply_markup = reply_markup
        # parse_mode="Markdown"
    )
    return HALL


    # await update.message.reply_text(
    #     "🏠 Please enter your room number:\n",
    #     parse_mode="Markdown"
    # )
    # return ADDRESS

async def handle_hall(update:Update, context:ContextTypes.DEFAULT_TYPE):
    hall = update.message.text.strip()
    context.user_data["hall"] = hall
    await update.message.reply_text(
        "🕒 Please enter your *delivery address * in this format:\n\n"
        "`Room 202`",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return ADDRESS
    
async def handle_address(update:Update, context:ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    cart = await get_cart_items(telegram_id)
    address = update.message.text.strip()
    
    full_address = f"{context.user_data.get('hall')}, {address}"
    
    location_obj = await sync_to_async(Location.objects.filter(name=context.user_data.get("hall")).first)()
    assigned_waiter = None
    if location_obj:
        assigned_waiter = await get_next_waiter(location_obj)
        
    order = await create_order(
        telegram_id = telegram_id, 
        total_amount = sum(int(item.food.price) for item in cart),
        delivery_no=random.randint(10000, 99999),
        status="pending",
        delivery_address = f"{context.user_data.get('hall')}, {address}",
        # location=location_obj
        waiter=assigned_waiter if assigned_waiter else None
        # created_at=created_at,
    )
    
    for item in cart:
        # food_id = await get_food_by_id(item.food.id)
        # try:
        #     food_obj = item.food
        # except Food.DoesNotExist:
        #     continue
        await get_orderitem(
            order=order,
            food=item.food,
            quantity=item.portions,
            price_at_order_time=item.food.price,
            vendor=item.vendor,
        )


    # food_names = [item['name'] for item in cart]
    # price_map = await get_food_prices(food_names)  # {name: price}

    total_sum = sum(item.food.price * item.portions for item in cart)
    message = "🛒 *Total checkout amount:*"
    
    
    #doing this cos paystack only accepts json e.g strings
    cart_data = []

    for i, item in enumerate(cart, 1):
        food_name = item.food.name
        vendor = item.vendor.name
        portions = item.portions
        price = item.food.price  # fallback to 0 if missing
        total = price * portions

        cart_data.append({
            "food_id": item.food.id,
            "food_name": food_name,
            "vendor_id": item.vendor.id,
            "vendor_name": vendor,
            "price": price,
            "portions": portions
        })

        message += f"{i}. ({vendor}) x {food_name} x {portions} → ₦{total}\n"
        total_sum += total

    message += f"\n💰 *Total: ₦{total_sum}*"
 
    if assigned_waiter:
        message += f"\n *Assigned waiter: * {assigned_waiter.name}"
    reference = str(uuid.uuid4())
    data = {
        "email": f"user{telegram_id}@example.com",  # placeholder email
        "amount": int(total_sum * 100),  # amount in kobo
        "reference": reference,
        "currency": "NGN",
        "metadata": {
            "telegram_id": telegram_id,
            "cart": cart_data
        },
        "callback_url": "https://9f4dea2b20e8.ngrok-free.app/verify_payment/"  # optional, can be your site
        
    }

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    # Call Paystack to initialize transaction
    response = requests.post(
        "https://api.paystack.co/transaction/initialize",
        json=data,
        headers=headers
    )

    if response.status_code == 200:
        res_data = response.json()
        if res_data.get("status"):
            payment_url = res_data["data"]["authorization_url"]

            await update.message.reply_text(
                f"🛒 *Total: ₦{total_sum}*\n\n"
                f"💳 Click below to complete payment:\n{payment_url}",
                parse_mode="Markdown"
            )
            
             
        else:
            await update.message.reply_text("❌ Failed to initialize payment. Try again.")
    else:
        await update.message.reply_text("⚠️ Error connecting to payment gateway.")
    await update.message.reply_text(message, parse_mode="Markdown", reply_markup=reply_markup)
    return ConversationHandler.END

async def cancel(update, context):
    await update.message.reply_text("❌ Checkout cancelled.")
    return ConversationHandler.END

# async def order_history(update:Update, context:ContextTypes.DEFAULT_TYPE):
#     telegram_id = update.effective_user.id,
#     order=await get_order(telegram_id)
    
#     if not order:
#         await update.message.reply_text("❌ You don’t have any previous orders yet. Place an order to continue")
#         return
    
#     message = ""
#     for i, item in enumerate(order, 1):
#         status = item.status
#         if status == "paid":
#             message += (
#             f"\n💰 Address: {item.delivery_address}"
#             f"\n Delivery no {item.delivery_no}"
#             f"\n Status: {item.status}\n"
#         )
        
#     # message = f"\n💰 Address: {delivery_address}\n Delivery no {delivery_no}\n status {status}"

#     await update.message.reply_text(message, parse_mode="Markdown", reply_markup=reply_markup)
#     # send message to the group

    
async def delivery_details(update:Update, context:ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    order=await get_order(telegram_id)
    
    if not order:
        await update.message.reply_text("❌ You don’t have any orders yet.")
        return
    message = ""
    
    for i, item in enumerate(order, 1):
        status = item.status
        if status == "paid":
            message += (
            f"\n💰 Address: {item.delivery_address}"
            f"\n Delivery no {item.delivery_no}"
            f"\n Status: {item.status}\n"
        )
        
    # message = f"\n💰 Address: {delivery_address}\n Delivery no {delivery_no}\n status {status}"

    await update.message.reply_text(message, parse_mode="Markdown", reply_markup=reply_markup)
    # send message to the group
    send_to_group(message)

def send_to_group(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode" : "Markdown",
        "disable_notification": True  # optional, send silently
    }
    requests.post(url, data=payload)

# Example usage:

# async def order(update:Update, context:ContextTypes.DEFAULT_TYPE):


    
# views.py

# def paystack_callback(request):
#     reference = request.GET.get("reference")
#     verify_url = f"https://api.paystack.co/transaction/verify/{reference}"
#     headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}

#     r = requests.get(verify_url, headers=headers)
#     data = r.json()

#     if data["status"] and data["data"]["status"] == "success":
#         telegram_id = ... # lookup user from your DB using reference
#         message = "✅ Payment successful! Thank you."
#         requests.get(
#             f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
#             params={"chat_id": telegram_id, "text": message}
#         )

#     return JsonResponse({"status": "ok"})

    
# =========================================
# ERROR HANDLER
# =========================================

# async def error(update: object, context: ContextTypes.DEFAULT_TYPE):
#     print(f'⚠️ Update {update} caused error: {context.error}')

async def error(update, context):
    print(f"\n⚠️ Update {update} caused error: {context.error}")
    traceback.print_exception(type(context.error), context.error, context.error.__traceback__)
# =========================================
# MAIN
# =========================================

if __name__ == '__main__':
    # send_to_group("✅ New order received: 2x Jollof Rice, ₦4000")

    persistence = PicklePersistence(filepath='mayviccbot_data')
    app = Application.builder().token(TOKEN).persistence(persistence).build()

    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    
    conversation_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("(?i)^place an order$"), ask_details)],
    states={
        ASK_PHONE: [
            MessageHandler(filters.CONTACT, handle_phone),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone)
            ],
        ASK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    )
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("(?i)^checkout$"), checkout)],
        states={
            HALL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_hall)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_address)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv_handler)
    app.add_handler(conversation_handler)
    # app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ask_details))
    # from telegram.ext import filters

# Only respond to private chat messages
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, handle_message))

    app.add_handler(CallbackQueryHandler(handle_vendor_selection, pattern="^vendor_"))
    app.add_handler(CallbackQueryHandler(go_back_to_vendors, pattern="^go_back_to_vendors$"))
    app.add_handler(CallbackQueryHandler(handle_plate_number, pattern="^plates_"))
    app.add_handler(CallbackQueryHandler(handle_food_selection, pattern="^food_"))
    # app.add_handler(CallbackQueryHandler(go_back_to_food, pattern="^go_back_to_food$"))
    # app.add_handler(CallbackQueryHandler(handle_portion_input, pattern="^portions_"))
    app.add_handler(CallbackQueryHandler(handle_portion_input, pattern= "^(portions_|edit_portions_)"))
    app.add_handler(CallbackQueryHandler(handle_next_plate, pattern="^next_plate$"))
    app.add_handler(CallbackQueryHandler(handle_cart_or_continue, pattern="^(add_to_cart|continue_shopping|checkout)$"))
    app.add_handler(CallbackQueryHandler(handle_manage_item, pattern="^manage_\d+$"))
    app.add_handler(CallbackQueryHandler(handle_view_cart, pattern="^handle_view_cart$"))
    app.add_handler(CallbackQueryHandler(handle_edit_item, pattern="^edit_"))
    app.add_handler(CallbackQueryHandler(handle_delete_item, pattern="^delete_\d+$"))
    


 
    app.add_error_handler(error)
    

    print("🤖 Bot is running...")
    app.run_polling(poll_interval=2)





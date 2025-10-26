
from django.db import models
import uuid
from django.core.validators import RegexValidator
from datetime import timezone

class TelegramUser(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=150, null=True, blank=True)
    email = models.EmailField(max_length=100)
    phone = models.CharField(max_length=20, unique= True)
    joined_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.username} - {self.phone} - {self.email}" 
    
class Vendors(models.Model):
    name = models.CharField(max_length=255, unique=True)
    delivery_fee = models.IntegerField(default= 500)
    plate_price = models.IntegerField(default=200)
    
    def __str__(self):
        return self.name
    
class Food(models.Model):
    vendor = models.ForeignKey(Vendors, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    price = models.IntegerField()
    portion = models.IntegerField(null=True, blank= True)
    
    def __str__(self):
        return f"{self.name} - {self.vendor.name}"
    
class Cart(models.Model):
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    portions = models.PositiveIntegerField(default=1)
    plate_no = models.PositiveIntegerField(default=1)
    # added_at = models.DateTimeField(auto_now_add=True)
    checked_out = models.BooleanField(default=False)
    vendor = models.ForeignKey(Vendors, on_delete=models.CASCADE)
    
    def __str__(self):
        return str(self.user.telegram_id)
    
# class PendingPayment(models.Model) 
class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('on_the_way', 'On the Way'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    total_amount = models.IntegerField()
    delivery_no = models.IntegerField(unique=True, blank=True, null=True)
    delivery_address = models.TextField(blank=True, null=True)
    location = models.ForeignKey("Location", on_delete=models.CASCADE, null=True, blank=True)
    waiter = models.ForeignKey("Waiter", on_delete=models.SET_NULL, null=True, blank=True)

    # vendor = models.ForeignKey(Vendors, on_delete=models.CASCADE)
    # Optional: payment_status, notes, etc.


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price_at_order_time = models.DecimalField(max_digits=8, decimal_places=2)
    vendor = models.ForeignKey(Vendors, related_name='vendors', on_delete=models.CASCADE)
    # paid = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.order} - {self.vendor.name} - {self.food} - {self.quantity} - {self.price_at_order_time}"
    
class Location(models.Model):
    name = models.CharField(max_length=20, unique=True )
    
    def __str__(self):
        return self.name
    

class Waiter(models.Model):
    name = models.CharField(max_length=20)
    # user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
    phone_no = models.CharField(
        max_length=11,
        validators=[
            RegexValidator(
                regex=r'^\d{11}$',
                message='Phone number must contain exactly 11 digits.'
            )
        ]
    )
    
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.name
    
# to track waiters current items to be delivered
class WaiterAssignmentTracker(models.Model):
    location = models.OneToOneField(Location, on_delete=models.CASCADE)
    last_assigned_index = models.IntegerField(default=-1)

    def __str__(self):
        return f"{self.location.name} → Last index {self.last_assigned_index}"

class BroadcastMessage(models.Model):
    title = models.CharField(max_length=255)
    message = models.TextField()
    sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    
    
    
    
    
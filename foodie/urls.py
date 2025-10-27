from django.urls import path
from .views import paystack_webhook

app_name = 'foodie'

urlpatterns = [
    path('paystack/webhook/', paystack_webhook, name='paystack_webhook'),
]



# from django.urls import path
# from foodie import views


# app_name = 'foodie'

# urlpatterns =[
#     # path('verify_payment/', views.verify_payment, name='verify'),

# ]

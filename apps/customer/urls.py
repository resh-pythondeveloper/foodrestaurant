from django.urls import path
from .views import SendOTPView,CustomerRegisterView

urlpatterns = [
    path("otp/",SendOTPView.as_view()),
    path("customer/register/",CustomerRegisterView.as_view())
]

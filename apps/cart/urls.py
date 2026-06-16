from django.urls import path
from apps.cart.views import CartView
urlpatterns = [
    path("cart/",CartView.as_view()),
    path("cart/<int:id>/",CartView.as_view())
]

from django.urls import path
from .views import ProductView
urlpatterns = [
    path("product/",ProductView.as_view()),
    path("product/<int:id>",ProductView.as_view())
]

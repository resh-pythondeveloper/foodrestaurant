from rest_framework import serializers
from apps.cart.models import CartItem

class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_price = serializers.DecimalField(
        source="product.price",max_digits=10,decimal_places=2,read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model=CartItem
        fields="__all__"
    def get_total_price(self, obj):
        return obj.product.price * obj.quantity
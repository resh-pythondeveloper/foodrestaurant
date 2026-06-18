from django.shortcuts import render
from apps.cart.models import CartItem,Cart
from apps.recipe.models import Product
from apps.cart.serializers import CartItemSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.customer.models import Customer
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
# Create your views here.

class CartView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self, request):
        try:
            customer = Customer.objects.get(user=request.user)
        except Customer.DoesNotExist:
            return Response(
                {"message": "Customer not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        cart, created = Cart.objects.get_or_create(
            customer=customer
        )

        product_id = request.data.get("product")
        quantity = request.data.get("quantity", 1)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {"message": "Product not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={"quantity": quantity}
        )

        if not created:
            cart_item.quantity += int(quantity)
            cart_item.save()

        serializer = CartItemSerializer(cart_item)

        return Response(
            {
                "message": "Item added to cart",
                "data": serializer.data
            },
            status=status.HTTP_201_CREATED
        )
    
    def get(self,request):
        try:
            customer = Customer.objects.get(user=request.user)
        except Customer.DoesNotExist:
            return Response(
                {"message": "Customer not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        cart, created = Cart.objects.get_or_create(customer=customer)

        cart_items=CartItem.objects.filter(cart=cart)
        serializer=CartItemSerializer(cart_items,many=True)
        # total_amount = sum(
        #     item.product.price * item.quantity
        #     for item in cart_items
        # )
        total_amount=cart.total_price
        return Response({
            "cart_items": serializer.data,
            "total_amount": total_amount
        },status=status.HTTP_200_OK)
    
    def patch(self,request,id):
        try:
            customer = Customer.objects.get(user=request.user)
        except Customer.DoesNotExist:
            return Response(
                {"message": "Customer not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        cart, created = Cart.objects.get_or_create(customer=customer)
        quantity=request.data.get("quantity")
        if quantity < 1:
            return Response(
                {"message": "Quantity must be greater than 0"},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            cart_item=CartItem.objects.get(id=id,cart=cart)
        except CartItem.DoesNotExist:
            return Response({"message": "Cart item not found"},
            status=status.HTTP_404_NOT_FOUND)

        cart_item.quantity=quantity
        cart_item.save()
        serializer = CartItemSerializer(cart_item)

        return Response(
            {
                "message": "Quantity updated successfully",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )
    def delete(self, request, id):
        try:
            customer = Customer.objects.get(user=request.user)
        except Customer.DoesNotExist:
            return Response(
                {"message": "Customer not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        cart, created = Cart.objects.get_or_create(customer=customer)
        cart_item = CartItem.objects.get(id=id, cart=cart)
        cart_item.delete()

        return Response(
            {"message": "Item removed from cart"},
            status=status.HTTP_204_NO_CONTENT
        )
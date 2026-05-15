from django.shortcuts import render,get_object_or_404
from .serializers import ProductSerializer
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth.models import User
from apps.user.models import AppUser
from rest_framework.permissions import IsAuthenticated
from .models import Product
from rest_framework.pagination import PageNumberPagination

class ProductPagination(PageNumberPagination):
    page_size = 2
    page_size_query_param = 'page_size'
    max_page_size = 10


class ProductView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = request.user

            if not user.is_staff:
                return Response(
                    {"error": "Only admin can add product"},
                    status=status.HTTP_403_FORBIDDEN
                )

            try:
                appuser = AppUser.objects.get(user=user, is_deleted=False)
            except AppUser.DoesNotExist:
                return Response(
                    {"error": "AppUser not found or deleted"},
                    status=status.HTTP_404_NOT_FOUND
                )

            serializer = ProductSerializer(
                data=request.data,
                context={"request": request}
            )

            if serializer.is_valid():
                serializer.save()
                return Response(
                    {
                        "message": "product created successfully",
                        "data": serializer.data
                    },
                    status=status.HTTP_201_CREATED
                )

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"errors":str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def get(self,request,id=None):
        if id:
            product=get_object_or_404(Product,id=id)
            serializer=ProductSerializer(product)
            return Response(serializer.data,status=status.HTTP_200_OK)
        
        products=Product.objects.all()
        paginator = ProductPagination()
        paginated_products = paginator.paginate_queryset(
            products,
            request
        )

        serializer = ProductSerializer(
            paginated_products,
            many=True
        )

        return paginator.get_paginated_response(
            serializer.data
        )

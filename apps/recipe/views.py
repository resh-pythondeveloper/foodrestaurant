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
from datetime import datetime
from apps.google_drive.google_cloud import delete_file_from_drive

class ProductPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 20


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
        
        products=Product.objects.all().order_by("id")
        # Search
        search = request.GET.get("search")
        if search:
            products = products.filter(
                name__icontains=search
            )

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
    
    def patch(self,request,id=None):
        try:
            user = request.user

            if not user.is_staff:
                return Response(
                    {"error": "Only admin can edit product"},
                    status=status.HTTP_403_FORBIDDEN
                )

            try:
                appuser = AppUser.objects.get(user=user, is_deleted=False)
            except AppUser.DoesNotExist:
                return Response(
                    {"error": "AppUser not found or deleted"},
                    status=status.HTTP_404_NOT_FOUND
                )
            product=get_object_or_404(Product,id=id)
            serializer=ProductSerializer(product,data=request.data,partial=True,context={"request": request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data,status=status.HTTP_200_OK)
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error":str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def delete(self,request,id=None):
        try:
            user = request.user

            if not user.is_staff:
                return Response(
                    {"error": "Only admin can edit product"},
                    status=status.HTTP_403_FORBIDDEN
                )

            appuser = AppUser.objects.filter(
                user=user,
                is_deleted=False
            ).first()

            if not appuser:
                return Response(
                    {"error": "AppUser not found or deleted"},
                    status=status.HTTP_404_NOT_FOUND
                )
            product=get_object_or_404(Product,id=id)
            if product.image:

                for image in product.image:

                    file_id = image.get("file_id")

                    if file_id:
                        delete_file_from_drive(file_id)
            product.delete()
            return Response({"message":"product delete successfully"},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SessionWiseProductView(APIView):
    def get(self,request):
        current_hour = datetime.now().hour

        # Morning: 7 AM to 11 AM
        if 7 <= current_hour < 12:
            products = Product.objects.filter(
                session__morning=True,
                is_deleted=False
            ).order_by("id")

        # Afternoon: 12 PM to 3 PM
        elif 12 <= current_hour < 16:
            products = Product.objects.filter(
                session__afternoon=True,
                is_deleted=False
            ).order_by("id")

        # Evening: 6 PM to 12 AM
        elif 18 <= current_hour <= 23:
            products = Product.objects.filter(
                session__evening=True,
                is_deleted=False
            ).order_by("id")

        else:
            products = Product.objects.none()
            # Search
        search = request.GET.get("search")
        if search:
            products = products.filter(
                name__icontains=search
            )


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

from django.shortcuts import render,get_object_or_404
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Customer,CustomerOTP
from .serializers import CustomerSerializer,CustomerLoginserializer
from rest_framework import status
from utils.otp import generate_otp
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from django.conf import settings

class SendOTPView(APIView):

    def post(self, request):

        email = request.data.get("email")

        if not email:
            return Response(
                {"error": "Email required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if User.objects.filter(email=email).exists():
            return Response(
                {"error":"Email already registered"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        CustomerOTP.objects.filter(
            email=email).delete()

        otp = generate_otp()

        CustomerOTP.objects.create(
            email=email,
            otp=str(otp)
        )
        send_mail(
            subject="Your OTP",
            message=f"Your OTP is {otp}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False
        )

        return Response(
            {"message": "OTP sent successfully"},
            status=status.HTTP_200_OK
        )
    
class VerifyOTPView(APIView):

    def post(self, request):

        email = request.data.get("email")
        otp = request.data.get("otp")

        otp_obj = CustomerOTP.objects.filter(
            email=email,
            otp=otp
        ).last()

        if not otp_obj:
            return Response(
                {"error":"Invalid OTP"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if otp_obj.created_at < timezone.now() - timedelta(minutes=5):
            return Response({"error":"OTP expired"},status=status.HTTP_400_BAD_REQUEST)

        otp_obj.is_verified = True
        otp_obj.save()

        return Response(
            {"message":"OTP verified successfully"},
            status=status.HTTP_200_OK
        )
    
class CustomerRegisterView(APIView):
    def post(self,request):
        try:
            email = request.data.get("email")

            otp_obj = CustomerOTP.objects.filter(
                email=email,
                is_verified=True
            ).last()

            if not otp_obj:
                return Response(
                    {"error":"Email not verified"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = CustomerSerializer(
                data=request.data,
                context={"request": request}
            )

            if serializer.is_valid():

                serializer.save()
                otp_obj.delete()

                return Response(
                    {
                        "message": "Customer registered successfully",

                        "customer": serializer.data
                    },
                    status=status.HTTP_201_CREATED
                )

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:

            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class CustomerLoginView(APIView):
    def post(self, request):
        serializer = CustomerLoginserializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data["email"]
            password = serializer.validated_data["password"]

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response(
                    {"error": "Invalid email or password"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                customer = Customer.objects.get(user=user)
            except Customer.DoesNotExist:
                return Response(
                    {"error": "Customer account not found"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if user.check_password(password):
                token = RefreshToken.for_user(user)

                return Response(
                    {
                        "access_token": str(token.access_token),
                        "refresh_token": str(token),
                        "user": {
                            "id": user.id,
                            "username": user.username,
                            "email": user.email
                        }
                    },
                    status=status.HTTP_200_OK
                )

            return Response(
                {"error": "Invalid email or password"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
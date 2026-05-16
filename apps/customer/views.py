from django.shortcuts import render,get_object_or_404
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Customer,CustomerOTP
from .serializers import CustomerSerializer
from rest_framework import status
from utils.otp import generate_otp,send_otp_mobile


class SendOTPView(APIView):

    def post(self, request):

        mobile = request.data.get("mobile")

        if not mobile:
            return Response(
                {"error": "Mobile number required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        otp = generate_otp()

        CustomerOTP.objects.create(
            mobile=mobile,
            otp=str(otp)
        )

        send_otp_mobile(mobile, otp)

        return Response(
            {"message": "OTP sent successfully"},
            status=status.HTTP_200_OK
        )
    
class CustomerRegisterView(APIView):
    def post(self,request):
        try:

            serializer = CustomerSerializer(
                data=request.data,
                context={"request": request}
            )

            if serializer.is_valid():

                customer = serializer.save()

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
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
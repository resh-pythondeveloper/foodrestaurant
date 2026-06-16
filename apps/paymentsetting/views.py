from django.shortcuts import render
from apps.paymentsetting.serializers import PaymentSettingserializer
from apps.paymentsetting.models import PaymentSetting
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser,IsAuthenticated

class PaymentSettingAPIView(APIView):
    permission_classes = [IsAdminUser,IsAuthenticated]
    def post(self,request):
        serializer=PaymentSettingserializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

    def get(self,request,id=None):
        if id:
            try:
                payment_setting = PaymentSetting.objects.get(id=id)
            except PaymentSetting.DoesNotExist:
                return Response(
                    {"message": "Payment setting not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            serializer=PaymentSettingserializer(payment_setting)
            return Response(serializer.data,status=status.HTTP_200_OK)
        settings=PaymentSetting.objects.all()
        serializer=PaymentSettingserializer(settings,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    def patch(self,request,id):
        try:
            payment_setting = PaymentSetting.objects.get(id=id)
        except PaymentSetting.DoesNotExist:
            return Response(
                {"message": "Payment setting not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        if "is_active" in request.data:
            return Response(
                {
                    "message": "Use ActiveApiView to change active payment setting."
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer=PaymentSettingserializer(payment_setting,data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, id):
        
        try:
            payment_setting = PaymentSetting.objects.get(id=id)
        except PaymentSetting.DoesNotExist:
            return Response(
                {"message": "Payment setting not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if only one record exists
        if PaymentSetting.objects.count() == 1:
            return Response(
                {
                    "message": "Cannot delete the only payment setting. Create another payment setting first."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Prevent deleting active record
        if payment_setting.is_active:
            inactive_records = PaymentSetting.objects.filter(
                is_active=False
            )

            serializer = PaymentSettingserializer(
                inactive_records,
                many=True
            )

            return Response(
                {
                    "message": "Active payment setting cannot be deleted. Please activate another payment setting first.",
                    "inactive_payment_settings": serializer.data
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        payment_setting.delete()

        return Response(
            {
                "message": "Payment setting deleted successfully."
            },
            status=status.HTTP_200_OK
        )
    

class ActiveApiView(APIView):
    permission_classes = [IsAdminUser,IsAuthenticated]
    def patch(self, request, id):
        try:
            payment_setting = PaymentSetting.objects.get(id=id)
        except PaymentSetting.DoesNotExist:
            return Response(
                {"message": "Payment setting not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check only one record exists
        if PaymentSetting.objects.count() == 1:
            return Response(
                {
                    "message": "Create another payment setting first."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # If already active
        if payment_setting.is_active:
            inactive_records = PaymentSetting.objects.filter(
                is_active=False
            )

            serializer = PaymentSettingserializer(
                inactive_records,
                many=True
            )

            return Response(
                {
                    "message": "This payment setting is already active.",
                    "inactive_payment_settings": serializer.data
                },
                status=status.HTTP_200_OK
            )

        # Activate selected record
        PaymentSetting.objects.update(is_active=False)

        payment_setting.is_active = True
        payment_setting.save()

        return Response(
            {
                "message": "Payment setting activated successfully."
            },
            status=status.HTTP_200_OK
        )
        
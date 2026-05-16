from rest_framework import serializers
from .models import Customer,CustomerOTP
from apps.google_drive.google_cloud import upload_file_to_drive,delete_file_from_drive
from django.contrib.auth.models import User
from django.db import transaction

def clean_name(name):
    return name.replace(" ", "_").lower()

class CustomerSerializer(serializers.ModelSerializer):
    username=serializers.CharField()
    email=serializers.CharField()
    otp = serializers.CharField(write_only=True)
    password=serializers.CharField(write_only=True)
    confirm_password=serializers.CharField(write_only=True)
    profile_picture = serializers.ListField(
        child=serializers.CharField(),
        read_only=True
    )
    class Meta:
        model=Customer
        fields="__all__"
        read_only_fields=["is_deleted","customerid","user"]

    def validate(self, attrs):
        if attrs['password']!=attrs['confirm_password']:
            raise serializers.ValidationError("password and confirm password does not match")
        
        mobile = attrs.get("mobile")
        otp = attrs.get("otp")

        otp_obj = CustomerOTP.objects.filter(
            mobile=mobile,
            otp=otp
        ).last()

        if not otp_obj:
            raise serializers.ValidationError(
                "Invalid OTP"
            )

        return attrs
    
    def create(self, validated_data):
        request=self.context.get('request')
        file = request.FILES.get('profile_picture')
        validated_data.pop('confirm_password')

        password = validated_data.pop('password')
        username = validated_data.pop('username')
        email = validated_data.pop('email')
        validated_data.pop('otp')

        # create Django auth user
        with transaction.atomic():
            auth_user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
            )

            # create AppUser
            app_customer = Customer.objects.create(
                user=auth_user,
                **validated_data
            )
            if file:
                folder_name = f"{clean_name(app_customer.user.username)}_{app_customer.customerid}"

                uploaded = upload_file_to_drive(file, folder_name)

                pictures = app_customer.profile_picture or []
                pictures.append(uploaded)

                app_customer.profile_picture = pictures
                app_customer.save()
            CustomerOTP.objects.filter(
                mobile=app_customer.mobile
            ).delete()

            return app_customer
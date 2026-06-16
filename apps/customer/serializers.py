from rest_framework import serializers
from .models import Customer,CustomerOTP
from apps.google_drive.google_cloud import upload_file_to_drive,delete_file_from_drive
from django.contrib.auth.models import User
from django.db import transaction

def clean_name(name):
    return name.replace(" ", "_").lower()

class CustomerSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
    source='user.username'
)

    email = serializers.EmailField(
    source='user.email'
)
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
        
        user_data = attrs.get("user")

        email = user_data.get("email")
        username = user_data.get("username")


        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                "Email already exists"
            )
        
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError(
                "Username already exists"
            )

        return attrs
    
    def create(self, validated_data):
        request=self.context.get('request')
        file = request.FILES.get('profile_picture')
        validated_data.pop('confirm_password')

        password = validated_data.pop('password')
        user_data = validated_data.pop('user')

        username = user_data.get('username')
        email = user_data.get('email')

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

            return app_customer

class CustomerLoginserializer(serializers.Serializer):
    email=serializers.CharField()
    password=serializers.CharField()
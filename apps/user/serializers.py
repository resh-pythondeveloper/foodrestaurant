from rest_framework import serializers
from .models import AppUser
from django.contrib.auth.models import User
from apps.google_drive.google_cloud import upload_file_to_drive
from django.db import transaction

def clean_name(name):
    return name.replace(" ", "_").lower()

class UserSerializer(serializers.ModelSerializer):
    username=serializers.CharField()
    email=serializers.CharField()
    password=serializers.CharField(write_only=True)
    confirm_password=serializers.CharField(write_only=True)
    profile_picture = serializers.ListField(
        child=serializers.CharField(),
        read_only=True
    )
    class Meta:
        model=AppUser
        fields='__all__'
        read_only_fields=["userid","user","is_deleted"]

    def validate(self, attrs):
        if attrs['password']!=attrs['confirm_password']:
            raise serializers.ValidationError("password and confirm password do not same")
        return attrs
    
    def create(self, validated_data):
        # remove confirm_password
        request = self.context.get('request')
        file = request.FILES.get('profile_picture')
        validated_data.pop('confirm_password')

        password = validated_data.pop('password')
        username = validated_data.pop('username')
        email = validated_data.pop('email')

        # create Django auth user
        with transaction.atomic():
            auth_user = User.objects.create_user(
                username=username,
                email=email,
                password=password,is_staff=True
            )

            # create AppUser
            app_user = AppUser.objects.create(
                user=auth_user,
                **validated_data
            )
            if file:
                folder_name = f"{clean_name(app_user.user.username)}_{app_user.userid}"

                uploaded = upload_file_to_drive(file, folder_name)

                pictures = app_user.profile_picture or []
                pictures.append(uploaded)

                app_user.profile_picture = pictures
                app_user.save()

                return app_user


class UserLoginSerializer(serializers.Serializer):
    email=serializers.CharField()
    password=serializers.CharField()
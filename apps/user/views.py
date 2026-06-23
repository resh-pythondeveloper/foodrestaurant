from django.shortcuts import render
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from .serializers import UserSerializer,UserLoginSerializer
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password

class RegisterView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        try:
            serializer = UserSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "User created"})
            return Response(serializer.errors)
        except Exception as e:
            return Response({"error":str(e)},status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']

            try:
                user = User.objects.get(email=email,is_staff=True)
            except User.DoesNotExist:
                return Response(
                    {"error": "Invalid email or password"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check password
            if user.check_password(password):
                token = RefreshToken.for_user(user)

                return Response({
                    "access_token": str(token.access_token),
                    "refresh_token": str(token),
                    "user": {
                        "username": user.username,
                        "email": user.email
                    }
                }, status=status.HTTP_200_OK)

            return Response(
                {"error": "Invalid email or password"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

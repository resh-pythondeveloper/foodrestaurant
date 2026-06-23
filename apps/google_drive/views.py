from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import redirect
from .google_cloud import get_google_auth_url, get_credentials_from_code
from .models import GoogleAccount
from rest_framework import status

class GoogleLoginAPIView(APIView):
    def get(self, request):

        account = GoogleAccount.objects.first()

        # ✅ if already connected → block login
        if account and account.token:
            return Response(
                {"error": "Google already connected"},
                status=400
            )

        # ✅ if old oauth_state exists → clear it (important)
        request.session.pop("oauth_state", None)

        url = get_google_auth_url(request)
        return redirect(url)

class GoogleCallbackAPIView(APIView):
    def get(self, request):
        try:
            creds_data = get_credentials_from_code(request)

            if not creds_data:
                return Response(
                    {"error": "No credentials received"},
                    status=400
                )

            account, _ = GoogleAccount.objects.get_or_create(name="main")
            account.token = creds_data
            account.save()

            # ✅ VERY IMPORTANT: clear state after success
            request.session.pop("oauth_state", None)

            return Response({"message": "Google connected successfully"})

        except Exception as e:
            return Response({"error": str(e)}, status=400)
import os,io
import tempfile
from django.conf import settings
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from .models import GoogleAccount
from googleapiclient.http import MediaIoBaseUpload


# ✅ Create OAuth Flow (NO PKCE)
def get_flow(state=None):
    return Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_OAUTH["CLIENT_ID"],
                "client_secret": settings.GOOGLE_OAUTH["CLIENT_SECRET"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=settings.GOOGLE_OAUTH["SCOPES"],
        state=state,
        autogenerate_code_verifier=False  # 🔥 disable PKCE
    )


# ✅ Step 1: Generate Auth URL
def get_google_auth_url(request):
    flow = get_flow()
    flow.redirect_uri = settings.GOOGLE_OAUTH["REDIRECT_URI"]

    auth_url, state = flow.authorization_url(
        access_type='offline',
        prompt='consent',
        include_granted_scopes='true'
    )

    # ✅ ONLY THIS
    request.session['oauth_state'] = state
    request.session.save()

    print("Saved State:", state)
    print("Session Key:", request.session.session_key)

    return auth_url

def get_credentials_from_code(request):
    session_state = request.session.get('oauth_state')
    request_state = request.GET.get('state')

    # print("SESSION STATE:", session_state)
    # print("REQUEST STATE:", request_state)
    # print("Callback Session Key:", request.session.session_key)
    # print("Session Contents:", dict(request.session))

    if not session_state:
        raise Exception("State missing from session")

    if session_state != request_state:
        raise Exception("State mismatch")

    flow = get_flow(state=session_state)
    flow.redirect_uri = settings.GOOGLE_OAUTH["REDIRECT_URI"]

    flow.fetch_token(
        authorization_response=request.build_absolute_uri()
    )

    creds = flow.credentials
    request.session.pop("oauth_state", None)


    return {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes
    }


# ✅ Get stored credentials
def get_owner_credentials():
    account = GoogleAccount.objects.first()

    if not account:
        raise Exception("Google account not connected")

    data = account.token

    creds = Credentials(
        token=data.get("token"),
        refresh_token=data.get("refresh_token"),
        token_uri=data.get("token_uri"),
        client_id=data.get("client_id"),
        client_secret=data.get("client_secret"),
        scopes=data.get("scopes"),
    )

    # Auto refresh
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        account.token["token"] = creds.token
        account.save()

    return creds


# ✅ Create folder
def get_or_create_folder(service, name, parent_id=None):
    query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"

    if parent_id:
        query += f" and '{parent_id}' in parents"

    result = service.files().list(q=query, fields="files(id)").execute()
    folders = result.get("files", [])

    if folders:
        return folders[0]["id"]

    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder"
    }

    if parent_id:
        metadata["parents"] = [parent_id]

    folder = service.files().create(body=metadata, fields="id").execute()
    return folder["id"]


# ✅ Upload single file
# def upload_file_owner_drive(file, app_user):
#     creds = get_owner_credentials()
#     service = build('drive', 'v3', credentials=creds)

#     root = get_or_create_folder(service, "MyApp")
#     user_folder = get_or_create_folder(service, f"user_{app_user.user.id}", root)

#     with tempfile.NamedTemporaryFile(delete=False) as tmp:
#         for chunk in file.chunks():
#             tmp.write(chunk)
#         tmp_path = tmp.name

#     media = MediaFileUpload(tmp_path, resumable=True)

#     uploaded = service.files().create(
#         body={"name": file.name, "parents": [user_folder]},
#         media_body=media,
#         fields="id,name"
#     ).execute()

#     file_id = uploaded["id"]

#     service.permissions().create(
#         fileId=file_id,
#         body={"role": "reader", "type": "anyone"}
#     ).execute()

#     os.remove(tmp_path)

#     return {
#         "file_id": file_id,
#         "url": f"https://drive.google.com/file/d/{file_id}/view"
#     }

# def upload_file_owner_drive(file, app_user):
#     creds = get_owner_credentials()
#     service = build('drive', 'v3', credentials=creds)

#     root = get_or_create_folder(service, "MyApp")
#     user_folder = get_or_create_folder(service, f"user_{app_user.user.id}", root)

#     file_stream = io.BytesIO(file.read())

#     media = MediaIoBaseUpload(
#         file_stream,
#         mimetype=file.content_type,
#         resumable=True
#     )

#     uploaded = service.files().create(
#         body={"name": file.name, "parents": [user_folder]},
#         media_body=media,
#         fields="id,name"
#     ).execute()

#     file_id = uploaded["id"]

#     service.permissions().create(
#         fileId=file_id,
#         body={"role": "reader", "type": "anyone"}
#     ).execute()

#     return {
#         "file_id": file_id,
#         "url": f"https://drive.google.com/file/d/{file_id}/view"
#     }

def upload_file_to_drive(file, folder_name):
    creds = get_owner_credentials()
    service = build('drive', 'v3', credentials=creds)

    root = get_or_create_folder(service, "MyApp")
    target_folder = get_or_create_folder(service, folder_name, root)

    file_stream = io.BytesIO(file.read())

    media = MediaIoBaseUpload(
        file_stream,
        mimetype=file.content_type,
        resumable=True
    )

    uploaded = service.files().create(
        body={"name": file.name, "parents": [target_folder]},
        media_body=media,
        fields="id,name"
    ).execute()

    file_id = uploaded["id"]

    service.permissions().create(
        fileId=file_id,
        body={"role": "reader", "type": "anyone"}
    ).execute()

    return {
        "file_id": file_id,
        "url": f"https://drive.google.com/file/d/{file_id}/view"
    }

# ✅ Delete file from Google Drive
def delete_file_from_drive(file_id):

    try:
        creds = get_owner_credentials()

        service = build(
            'drive',
            'v3',
            credentials=creds
        )

        service.files().delete(
            fileId=file_id
        ).execute()

        return True

    except Exception as e:
        print("Delete Error:", str(e))
        return False
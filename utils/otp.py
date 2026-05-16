import random
import requests

def generate_otp():
    return random.randint(100000, 999999)


def send_otp_mobile(mobile, otp):

    url = "https://www.fast2sms.com/dev/bulkV2"

    payload = {
        "variables_values": str(otp),
        "route": "otp",
        "numbers": mobile,
    }

    headers = {
        "authorization": "YOUR_FAST2SMS_API_KEY"
    }

    response = requests.post(
        url,
        data=payload,
        headers=headers
    )

    return response.json()
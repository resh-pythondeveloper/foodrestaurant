from rest_framework import serializers
from apps.paymentsetting.models import PaymentSetting

class PaymentSettingserializer(serializers.ModelSerializer):
    class Meta:
        model=PaymentSetting
        fields="__all__"
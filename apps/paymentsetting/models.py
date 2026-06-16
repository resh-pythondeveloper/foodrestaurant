from django.db import models

# Create your models here.
class PaymentSetting(models.Model):
    account_holder_name = models.CharField(max_length=100)
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=50)
    ifsc_code = models.CharField(max_length=20)
    upi_id = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)

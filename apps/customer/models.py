from django.db import models
from django.db import transaction
from django.contrib.auth.models import User
# Create your models here.
class Customer(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    customerid=models.CharField(max_length=20,unique=True)
    mobile=models.CharField(max_length=50,unique=True)
    profile_picture=models.JSONField(default=list)
    is_deleted=models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.customerid:
            with transaction.atomic():
                last_user = Customer.objects.select_for_update().order_by('-id').first()

                if last_user and last_user.customerid:
                    last_id = int(last_user.customerid.replace('CUST', ''))
                    new_id = last_id + 1
                else:
                    new_id = 1

                self.customerid = f"CUST{new_id:04d}"

        super().save(*args, **kwargs)

class CustomerOTP(models.Model):
    email=models.EmailField()
    otp = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.mobile
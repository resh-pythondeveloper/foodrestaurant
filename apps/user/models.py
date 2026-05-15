from django.db import models
from django.contrib.auth.models import User
from django.db import transaction
# Create your models here.
class AppUser(models.Model):
    userid=models.CharField( max_length=50,unique=True)
    mobile=models.CharField( max_length=20,unique=True)
    profile_picture=models.JSONField(default=list)
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    is_deleted = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.userid:
            with transaction.atomic():
                last_user = AppUser.objects.select_for_update().order_by('-id').first()

                if last_user and last_user.userid:
                    last_id = int(last_user.userid.replace('USR', ''))
                    new_id = last_id + 1
                else:
                    new_id = 1

                self.userid = f"USR{new_id:04d}"

        super().save(*args, **kwargs)
from django.db import models

# Create your models here.
class GoogleAccount(models.Model):
    name = models.CharField(max_length=100, default="main")
    token = models.JSONField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
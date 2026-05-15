from django.db import models
from django.db import transaction

class Product(models.Model):
    productid = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    session=models.JSONField(default=dict)
    image = models.JSONField(default=list)
    is_deleted=models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.productid:
            with transaction.atomic():
                last_product = Product.objects.select_for_update().order_by('-id').first()

                if last_product and last_product.productid:
                    last_id = int(last_product.productid.replace('PRD', ''))
                    new_id = last_id + 1
                else:
                    new_id = 1

                self.productid = f"PRD{new_id:04d}"

        super().save(*args, **kwargs)
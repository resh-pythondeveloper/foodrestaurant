from rest_framework import serializers
from .models import Product
from apps.google_drive.google_cloud import upload_file_to_drive

def clean_name(name):
    return name.replace(" ", "_").lower()

class ProductSerializer(serializers.ModelSerializer):
    image = serializers.ListField(
        child=serializers.CharField(),
        read_only=True
    )
    class Meta:
        model=Product
        fields="__all__"
        read_only_fields=["productid","is_deleted"]

    def create(self, validated_data):
        request = self.context.get('request')
        files = request.FILES.getlist('image')  # ✅ multiple files

        product = Product.objects.create(**validated_data)

        uploaded_images = []

        if files:
            folder_name = f"{clean_name(product.name)}_{product.productid}"

            for file in files:
                uploaded = upload_file_to_drive(file, folder_name)
                uploaded_images.append(uploaded)

        product.image = uploaded_images
        product.save()

        return product
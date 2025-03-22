from rest_framework import serializers
from .models import ReceiptFile

class ReceiptFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReceiptFile
        fields = '__all__'

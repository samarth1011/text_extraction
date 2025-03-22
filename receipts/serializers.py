from rest_framework import serializers
from .models import Receipt, ReceiptFile

class ReceiptFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReceiptFile
        fields = '__all__'

class ReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipt
        fields = '__all__'

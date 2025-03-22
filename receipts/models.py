from django.db import models

class ReceiptFile(models.Model):
    file_name = models.CharField(max_length=255)
    file_path = models.TextField()
    is_valid = models.BooleanField(default=False)
    invalid_reason = models.TextField(null=True, blank=True)
    is_processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.file_name} - {'Valid' if self.is_valid else 'Invalid'}"

class Receipt(models.Model):
    purchased_at = models.DateTimeField(null=True, blank=True)
    merchant_name = models.CharField(max_length=255, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    file_path = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Receipt from {self.merchant_name or 'Unknown'} - {self.total_amount or 'N/A'}"
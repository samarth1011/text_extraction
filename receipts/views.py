import os
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ReceiptFile
from .serializers import ReceiptFileSerializer
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import PyPDF2

import pytesseract
from pdf2image import convert_from_path
from datetime import datetime
import re

from rest_framework import status
from .models import ReceiptFile, Receipt

class UploadReceiptView(APIView):
    def post(self, request):
        file = request.FILES.get('file')

        # Validate that a file was provided
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate file type (PDF only)
        if not file.name.endswith('.pdf'):
            return Response({'error': 'Only PDF files are allowed'}, status=status.HTTP_400_BAD_REQUEST)

        # Save file to media directory
        file_path = os.path.join(settings.MEDIA_ROOT, 'receipts', file.name)
        default_storage.save(file_path, ContentFile(file.read()))

        # Save metadata in the database
        receipt_file = ReceiptFile.objects.create(
            file_name=file.name,
            file_path=file_path,
            is_valid=False,  # Initially set as false, will validate later
        )

        return Response({'message': 'File uploaded successfully', 'file_id': receipt_file.id}, status=status.HTTP_201_CREATED)

class ValidateReceiptView(APIView):
    def post(self, request):
        
        file_id = request.data.get('file_id')
        print("Received request to validate file_id:", file_id)
        # Retrieve the file from the database
        try:
            receipt_file = ReceiptFile.objects.get(id=file_id)
        except ReceiptFile.DoesNotExist:
            return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if the file is a valid PDF
        try:
            with open(receipt_file.file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                if len(reader.pages) == 0:
                    raise ValueError("Empty PDF")
            receipt_file.is_valid = True
            receipt_file.invalid_reason = None
        except Exception as e:
            receipt_file.is_valid = False
            receipt_file.invalid_reason = str(e)

        receipt_file.save()

        return Response({'message': 'File validated successfully', 'is_valid': receipt_file.is_valid}, status=status.HTTP_200_OK)
    
class ProcessReceiptView(APIView):
    def post(self, request):
        file_id = request.data.get('file_id')

        try:
            receipt_file = ReceiptFile.objects.get(id=file_id)
        except ReceiptFile.DoesNotExist:
            return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

        if not receipt_file.is_valid:
            return Response({'error': 'File is not valid'}, status=status.HTTP_400_BAD_REQUEST)

        if receipt_file.is_processed:
            return Response({'error': 'File is already processed'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Convert PDF to images
            images = convert_from_path(receipt_file.file_path)

            extracted_text = ""
            for img in images:
                extracted_text += pytesseract.image_to_string(img)

            # Extract data using regex
            merchant_name = self.extract_merchant_name(extracted_text)
            total_amount = self.extract_total_amount(extracted_text)
            purchased_at = self.extract_date(extracted_text)

            # Save extracted data
            Receipt.objects.create(
                purchased_at=purchased_at,
                merchant_name=merchant_name,
                total_amount=total_amount,
                file_path=receipt_file.file_path
            )

            receipt_file.is_processed = True
            receipt_file.save()

            return Response({
                'message': 'Receipt processed successfully',
                'merchant_name': merchant_name,
                'total_amount': total_amount,
                'purchased_at': purchased_at
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def extract_merchant_name(self, text):
        lines = text.split("\n")
        return lines[0] if lines else "Unknown Merchant"

    def extract_total_amount(self, text):
        match = re.search(r'Total\s*[:\s$]*([\d,]+\.\d{2})', text, re.IGNORECASE)
        return float(match.group(1)) if match else None

    def extract_date(self, text):
        match = re.search(r'(\d{2}/\d{2}/\d{4})', text)
        return datetime.strptime(match.group(1), "%m/%d/%Y") if match else None

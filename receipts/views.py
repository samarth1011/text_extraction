import os
from django.conf import settings
from django.shortcuts import render
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

from rest_framework import generics, filters
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from .models import Receipt
from .serializers import ReceiptSerializer
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def home(request):
    return render(request, 'index.html')


@method_decorator(csrf_exempt, name='dispatch')
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


@method_decorator(csrf_exempt, name='dispatch')
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


@method_decorator(csrf_exempt, name='dispatch')   
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
            if not os.path.exists(receipt_file.file_path):
                return Response({'error': 'File path does not exist'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            images = convert_from_path(receipt_file.file_path)
            extracted_text = "\n".join(pytesseract.image_to_string(img) for img in images)

            print("Extracted Text:\n", extracted_text)

            # Extract details using regex
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
                'merchant_name': merchant_name or "Unknown",
                'total_amount': total_amount or 0.0,
                'purchased_at': purchased_at.strftime("%Y-%m-%d") if purchased_at else "Unknown"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def extract_merchant_name(self, text):
        """Extracts the merchant name from the receipt text."""
        lines = text.strip().split("\n")
        
        # Common irrelevant words at the top of receipts
        ignore_keywords = ["total", "receipt", "invoice", "date", "tax", "amount", "payment", "transaction"]
        
        # Common merchant keywords (helps in filtering)
        merchant_keywords = ["store", "shop", "supermarket", "mart", "inc", "ltd", "cafe", "bakery", "restaurant", "hotel", "market", "pharmacy"]
        
        for line in lines[:7]:  # Check only the first few lines
            cleaned_line = re.sub(r"[^a-zA-Z0-9\s&.'-]", "", line).strip()  # Remove special characters except common name characters

            if len(cleaned_line) > 3 and not any(word.lower() in cleaned_line.lower() for word in ignore_keywords):
                # Check if the line contains store-related keywords or is in uppercase
                if any(word.lower() in cleaned_line.lower() for word in merchant_keywords) or cleaned_line.isupper():
                    return cleaned_line

        return "Unknown Merchant"
    
    def extract_total_amount(self, text):
        """Extracts the total amount from the receipt text."""
        total_patterns = [
            r"Total\s*[:\s$]*([\d,]+\.\d{2})",  # Matches "Total: $929.98" or "Total Amount: 929.98"
            r"Amount\s*[:\s$]*([\d,]+\.\d{2})",  # Matches "Amount: 299.99"
            r"Grand Total\s*[:\s$]*([\d,]+\.\d{2})",  # Matches "Grand Total: 120.50"
        ]

        for pattern in total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1).replace(",", ""))  # Remove commas and convert to float

        return None

    def extract_date(self, text):
        """Extracts the purchase date from the receipt text."""
        date_patterns = [
            r"(\d{2}/\d{2}/\d{4})",  # Matches "03/22/2025"
            r"(\d{4}-\d{2}-\d{2})",  # Matches "2025-03-22"
            r"(\d{2} [A-Za-z]{3} \d{4})",  # Matches "22 Mar 2025"
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return datetime.strptime(match.group(1), "%m/%d/%Y")
                except ValueError:
                    try:
                        return datetime.strptime(match.group(1), "%Y-%m-%d")
                    except ValueError:
                        return datetime.strptime(match.group(1), "%d %b %Y")

        return None
@method_decorator(csrf_exempt, name='dispatch')
class ReceiptListView(generics.ListCreateAPIView):
    """List all receipts or create a new one"""
    queryset = Receipt.objects.all()
    serializer_class = ReceiptSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['merchant_name', 'purchased_at', 'total_amount']
    search_fields = ['merchant_name']
    ordering_fields = ['purchased_at', 'total_amount']

@method_decorator(csrf_exempt, name='dispatch')
class ReceiptDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a receipt"""
    queryset = Receipt.objects.all()
    serializer_class = ReceiptSerializer

from django.http import JsonResponse
from .models import Receipt

def get_receipts(request):
    receipts = Receipt.objects.all().values("id", "merchant_name", "total_amount", "purchased_at", "file_path")
    return JsonResponse(list(receipts), safe=False)

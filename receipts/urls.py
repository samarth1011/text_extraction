from django.conf import settings
from django.urls import path
from .views import ReceiptDetailView, ReceiptListView, UploadReceiptView, ValidateReceiptView, ProcessReceiptView, get_receipts, home
from django.conf.urls.static import static
urlpatterns = [

    path('', home, name='home'),

    path('api/upload/', UploadReceiptView.as_view(), name='upload_receipt'),
    path('api/validate/', ValidateReceiptView.as_view(), name='validate_receipt'),
    path('api/process/', ProcessReceiptView.as_view(), name='process_receipt'),
     path('api/receipts/', ReceiptListView.as_view(), name='receipt-list'),
      path("api/all-receipts/", get_receipts, name="get_receipts"),
    path('api/receipts/<int:pk>/', ReceiptDetailView.as_view(), name='receipt-detail'),
]


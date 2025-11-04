# ocr_module/urls.py

from django.urls import path
from . import views

app_name = 'ocr_module'

urlpatterns = [
    # http://127.0.0.1:8000/api/ocr/upload/?file
    path('upload/', views.upload_file, name='upload_file'),
]
# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path, re_path
from app import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Matches any html file 
    re_path(r'^.*\.html', views.pages, name='pages'),

    # The home page
    path('', views.index, name='home'),

    path('check', views.check),
    path('upload', views.upload),
    path('document', views.document_list),
    path('dataset', views.dataset_list),
    path('fingerprint/<filename>', views.get_fingerprint),
    path('similarity/<uuid:id>/check', views.similarity_check),
    path('dataset/<uuid:id>/finish', views.dataset_finishing),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

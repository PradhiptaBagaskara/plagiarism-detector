# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2020 - Winnowing Similarity Measurement
"""

from django.urls import path, re_path
from app import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Matches any html file 
    re_path(r'^.*\.html', views.pages, name='pages'),

    # The home page
    path('', views.check, name='home'),

    path('check', views.check, name='demo_check'),

    path('re_fingerprint', views.re_fingerprint, name='document.re_fingerprint'),
    path('re_check', views.re_check, name='document.re_check'),

    path('document', views.document_list, name='document.index'),
    path('document/upload', views.document_upload, name='document.upload'),
    path('document/<uuid:id>', views.document_show, name='document.show'),
    path('document/<uuid:id>/edit', views.document_edit, name='document.edit'),
    path('document/<uuid:id>/delete', views.document_delete, name='document.delete'),
    path('document/<uuid:id>/finish', views.document_finishing, name='document.finish'),
    path('document/<uuid:id>/fingerprint', views.document_fingerprint, name='document.fingerprint'),
    path('document/<uuid:id>/html', views.document_html, name='document.html'),
    path('document/<uuid:id>/pdf', views.document_pdf, name='document.pdf'),
    path('document/<uuid:id>/text', views.document_text, name='document.text'),
    path('document/<uuid:id>/similarity', views.document_similarity, name='document.similarity'),
    path('document/<uuid:id>/check', views.similarity_check, name='document.check'),

    path('dataset', views.dataset_list, name='dataset.index'),
    path('dataset/upload', views.dataset_upload, name='dataset.upload'),
    path('dataset/upload_batch', views.dataset_upload_batch, name='dataset.upload_batch')
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

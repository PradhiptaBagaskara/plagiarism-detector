# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2020 - Winnowing Similarity Measurement
"""

from django.contrib import admin
from django.urls import path, include  # add this

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("authentication.urls")),  # add this
    path("", include("app.urls"))  # add this
]

# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2020 - Winnowing Similarity Measurement
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

application = get_wsgi_application()

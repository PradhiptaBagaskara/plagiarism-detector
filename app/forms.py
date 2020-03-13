# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class InputForm(forms.Form):
    origin = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "placeholder" : "Text Asli",
                "class" : "form-control",
            }
        )
    )
    referer = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "placeholder" : "Text Pembanding",
                "class" : "form-control",
            }
        )
    )

    gram_option = forms.ChoiceField(
        widget=forms.Select(
            attrs={
                "class" : "form-control",
            }
        ), 
        choices=[(b, b) for b in range(4, 16)]
        )
    
    winnow_option = forms.ChoiceField(
        widget=forms.Select(
            attrs={
                "class" : "form-control",
            }
        ), 
        choices=[(1, 'Winnowing with wordgram'), (2, 'Winnowing with ngram')]
        )

    debug = forms.ChoiceField(
        widget=forms.Select(
            attrs={
                "class" : "form-control",
            }
        ), 
        choices=[(0, 'Off'), (1, 'On')]
        )

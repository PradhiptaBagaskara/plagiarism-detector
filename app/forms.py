# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2020 - Winnowing Similarity Measurement
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from app.models import Document


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
        choices=[(b, b) for b in range(1, 16)]
        )
    
    winnow_option = forms.ChoiceField(
        widget=forms.Select(
            attrs={
                "class" : "form-control",
            }
        ), 
        choices=[(1, 'wordgram')]
        )

    plag_option = forms.ChoiceField(
        widget=forms.Select(
            attrs={
                "class" : "form-control",
            }
        ), 
        choices=[(1, 'Winnowing'), (2, 'Rabin-Karp')]
        )
    debug = forms.ChoiceField(
        widget=forms.Select(
            attrs={
                "class" : "form-control",
            }
        ), 
        choices=[(0, 'Off'), (1, 'On')]
        )


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        widgets = {
            'title': forms.TextInput(
                attrs={
                    "placeholder": "Judul Dokumen",
                    "class": "form-control",
                }
            ),
            'author': forms.TextInput(
                attrs={
                    "placeholder": "Pengarang",
                    "class": "form-control",
                }
            ),
            'content': forms.FileInput(
                attrs={
                    "placeholder": "File",
                    "class": "custom-file-input",
                    "accept": ".doc,.docx,.pdf"
                }
            ),
            'keyword': forms.TextInput(
                attrs={
                    "placeholder": "Keyword",
                    "class": "form-control",
                }
            ),
            'lang': forms.TextInput(
                attrs={
                    "placeholder": "Language",
                    "class": "form-control",
                }
            ),
        }
        fields = ['title', 'author', 'content', 'keyword', 'lang']
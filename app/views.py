# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from django.template import loader
from django.http import HttpResponse
from binfile.distance_measurement import *
from binfile.check import checks as chk
from .forms import InputForm, DocumentForm
# from django_q.tasks import async
from .models import Document, Similarity

@login_required(login_url="/login/")
def index(request):
    return render(request, "index.html")

@login_required(login_url="/login/")
def pages(request):
    context = {}
    # All resource paths end in .html.
    # Pick out the html file name from the url. And load that template.
    try:

        load_template = request.path.split('/')[-1]
        template = loader.get_template('pages/' + load_template)
        return HttpResponse(template.render(context, request))

    except:

        template = loader.get_template( 'pages/error-404.html' )
        return HttpResponse(template.render(context, request))

@login_required(login_url="/login/")
def check(request):
    form = InputForm(request.POST or None)
    msg = None
    data = None
    diff = None

    if request.method == "POST":
        if form.is_valid():
            origin = form.cleaned_data.get("origin")
            referer = form.cleaned_data.get("referer")
            gram_option = int(form.cleaned_data.get("gram_option"))
            winnow_option = int(form.cleaned_data.get("winnow_option"))
            debug = bool(form.cleaned_data.get("debug") == '1')
            plag = int(form.cleaned_data.get("plag_option"))
            diff = chk(origin, referer, gram_option, winnow_option, debug,plag)
            if diff is not None:
                data = diff
            else:    
                msg = 'Error on Checking'
        else:
            msg = 'No input specified'
        print(msg) 

    context = {"form": form, "msg": msg, "data": data}
    template = loader.get_template('check.html')
    return HttpResponse(template.render(context, request))

@login_required(login_url="/login/")
def upload(request):
    form = DocumentForm(request.POST, request.FILES)
    msg = None

    if request.method == "POST":
        if form.is_valid():
            doc = form.save(commit=False)
            doc.user = request.user
            doc.save()
            msg = 'Valid'
        else:
            msg = 'No input specified'

    context = {"form": form, "msg": msg}
    template = loader.get_template('upload_document.html');
    return HttpResponse(template.render(context, request))

@login_required(login_url="/login/")
def document_list(request):
    documents = Document.objects.filter(user=request.user)
    msg = ""
    context = {"documents": documents, "msg": msg}
    template = loader.get_template('document_list.html');
    return HttpResponse(template.render(context, request))

@login_required
def get_fingerprint(request, filename):
    print(filename)   
    file = get_object_or_404(Document, filename=filename)

    response = HttpResponse(file.get_fingerprint())
    response.status_code = 200
    response['Access-Control-Allow-Origin'] = '*'
    response['Content-Type'] = 'text/json'
    return response
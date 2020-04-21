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
from .task import process_doc, finishing_dataset, check_similarity

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
            process_doc(doc.id) # 
            msg = 'Valid'
            return redirect("/document")
        else:
            msg = 'No input specified'

    context = {"form": form, "msg": msg}
    template = loader.get_template('document/upload.html');
    return HttpResponse(template.render(context, request))

@login_required(login_url="/login/")
def document_list(request):
    documents = Document.objects.filter(user=request.user, is_dataset=False)
    msg = ""
    context = {"documents": documents, "msg": msg}
    template = loader.get_template('document/index.html');
    return HttpResponse(template.render(context, request))

@login_required(login_url="/login/")
def dataset_list(request):
    datasets = Document.objects.filter(is_dataset=True)
    msg = ""
    context = {"datasets": datasets, "msg": msg}
    template = loader.get_template('dataset/index.html');
    return HttpResponse(template.render(context, request))

@login_required(login_url="/login/")
def dataset_finishing(request, id):
    dataset = get_object_or_404(Document, id=id)
    if dataset.is_dataset:
        finishing_dataset(dataset.id)
    return HttpResponse(dataset.status)

@login_required(login_url="/login/")
def similarity_check(request, id):
    document = get_object_or_404(Document, id=id)
    if not document.is_dataset:
        check_similarity(document.id)
    return HttpResponse(document.status)

@login_required
def get_fingerprint(request, filename):
    file = get_object_or_404(Document, filename=filename)

    response = HttpResponse(file.get_fingerprint())
    response.status_code = 200
    response['Access-Control-Allow-Origin'] = '*'
    response['Content-Type'] = 'text/json'
    return response
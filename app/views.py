# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.template import loader
from django.http import HttpResponse
from binfile.distance_measurement import *
from binfile.check import checks as chk
from .forms import InputForm

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
            diff = chk(origin, referer, gram_option, winnow_option, debug)
            if diff is not None:
                data = diff
            else:    
                msg = 'Error on Checking'
        else:
            msg = 'No input specified' 

    context = {"form" : form, "msg" : msg, "data" : data}
    template = loader.get_template('check.html');
    return HttpResponse(template.render(context, request))
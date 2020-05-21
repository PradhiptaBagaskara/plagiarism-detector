from django.contrib.auth.models import User
from django_q.tasks import async
from app.models import Document, Similarity
from binfile.distance_measurement import cosine_sim, jaccard_similarity, dice_similarity, mahalanobis_distance, \
    euclidean_distance, minkowski_distance, manhattan_distance, weighted_euclidean_distance
from django.conf import settings

import glob
import re
import os
import json

from django.core.files.base import ContentFile
from django.core.files import File

import asyncio, time
from functools import wraps
from concurrent import futures

IGNORE = [
    "env",
    ".local",
    ".git",
]

_DEFAULT_POOL = futures.ThreadPoolExecutor(max_workers=200)


def threadpool(f, executor=None):
    @wraps(f)
    def wrap(*args, **kwargs):
        asyncio.set_event_loop(asyncio.new_event_loop())
        return asyncio.wrap_future((executor or _DEFAULT_POOL).submit(f, *args, **kwargs))

    return wrap


#  for datasets
def process_path(path, username='admin'):
    if not path.endswith("/"):
        path = path + "/"

    if not path.endswith("**"):
        path = path + "**"

    for filename in glob.iglob(path, recursive=True):
        print("Checking", filename)
        will_ignore = False
        for ignore in IGNORE:
            if re.match(ignore, filename):
                print("IGNORING", filename)
                will_ignore = True
                break

        if not will_ignore:
            print("PROCESSING", filename)
            # async(process_file_by_path, filename)
            process_file_by_path(filename, username)

    return path


# @threadpool
def process_file_by_path(path, username='admin'):
    _, ext = os.path.splitext(path)
    original_filename = os.path.basename(path)
    if ext not in [".pdf", ".docx", ".doc"]:
        return

    print("PROCESSING ONE FILE", path)
    if not os.path.isfile(path):
        print("NOT A FILE", path)
        return

    try:
        sf = Document.objects.get(content=path)  # filename
    except Document.DoesNotExist:
        # If it does NOT have an entry, create one
        sf = Document()

    user = User.objects.get(username=username)  # static
    sf.user = user
    with open(path, mode="rb") as file:
        sf.content.save(name=os.path.basename(path), content=file)

    sf.original_filename = original_filename
    sf.save()
    finishing_dataset(sf.id)
    # async(finishing_dataset, sf.id)
    os.remove(path)
    print("DELETE FILE ", path)

    return sf.id


# @threadpool
def finishing_dataset(id):
    try:
        sf = Document.objects.get(id=id)
    except Document.DoesNotExist:
        return

    sf.extract_content()
    sf.translate()
    sf.fingerprinting(save=True, debug=True)
    sf.is_dataset = True
    sf.save()

    return sf


# for user document
@threadpool
def process_doc(id):
    try:
        sf = Document.objects.get(id=id)  # filename
    except Document.DoesNotExist:
        print("NOT EXIST", id)
        return

    sf.extract_content()
    sf.translate()
    sf.fingerprinting()
    sf.save()
    check_similarity(sf.id)


def process_hook(task):
    print(task.result)


# should call from view
def extract_n_process(name, username='admin'):
    from pyunpack import Archive
    dest = os.path.join(settings.MEDIA_ROOT, 'extract')
    src = os.path.join(settings.MEDIA_ROOT, name)
    Archive(src).extractall(dest, auto_create_dir=True)
    process_path(dest, username)
    # os.remove(src)
    # print('Source Deleted')


# @threadpool
def check_similarity(id):
    try:
        sf = Document.objects.get(id=id)
    except Document.DoesNotExist:
        print("Document not Exist")
        return

    datasets = Document.objects.filter(is_dataset=True, status="finished")

    for d in datasets:
        cosine = round(cosine_sim(sf.get_fingerprint()['fingerprint'], d.get_fingerprint()['fingerprint']) * 100, 2)
        jaccard = round(jaccard_similarity(sf.get_fingerprint()['fingerprint'], d.get_fingerprint()['fingerprint']) * 100, 2)
        dice = round(dice_similarity(sf.get_fingerprint()['fingerprint'], d.get_fingerprint()['fingerprint']) * 100, 2)
        manhattan = round(manhattan_distance(sf.get_fingerprint()['fingerprint'], d.get_fingerprint()['fingerprint']) * 100, 2)
        mahalanobis = round(mahalanobis_distance(sf.get_fingerprint()['fingerprint'], d.get_fingerprint()['fingerprint']) * 100, 2)
        minkowski = round(minkowski_distance(sf.get_fingerprint()['fingerprint'], d.get_fingerprint()['fingerprint'], 2) * 100, 2)
        euclidean = round(euclidean_distance(sf.get_fingerprint()['fingerprint'], d.get_fingerprint()['fingerprint']) * 100, 2)
        weighted = round(weighted_euclidean_distance(sf.get_fingerprint()['fingerprint'], d.get_fingerprint()['fingerprint'], 3) * 100, 2)

        sf.add_similarity(
            d,
            cosine=cosine,
            jaccard=jaccard,
            dice=dice,
            manhattan=manhattan,
            mahalanobis=mahalanobis,
            minkowski=minkowski,
            euclidean=euclidean,
            weighted=weighted
        )


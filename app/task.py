from django.contrib.auth.models import User
from django_q.tasks import async
from app.models import Document, Similarity
from binfile.distance_measurement import cosine_sim, cosine_similarity, jaccard_similarity, dice_similarity, mahalanobis_distance, \
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

_DEFAULT_POOL = futures.ThreadPoolExecutor(max_workers=8)


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


@threadpool
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


@threadpool
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
    from sklearn.preprocessing import normalize
    import numpy as np
    from scipy.spatial import distance
    try:
        sf = Document.objects.get(id=id)
    except Document.DoesNotExist:
        print("Document not Exist")
        return

    datasets = Document.objects.filter(is_dataset=True, status="finished")

    for d in datasets:
        t_origin = sf.get_fingerprint()['fingerprint']
        t_referer = d.get_fingerprint()['fingerprint']

        if len(t_origin) > len(t_referer):
            n_origin = t_origin
            n_referer = t_referer + [0 for i in range(abs(len(t_origin) - len(t_referer)))]
            # t_origin = t_origin[:len(t_referer)]
        elif len(t_origin) < len(t_referer):
            n_referer = t_referer
            n_origin = t_origin + [0 for i in range(abs(len(t_origin) - len(t_referer)))]
        else:
            n_referer = t_referer
            n_origin = t_origin

        matrix = [[], []]
        matrix[0] = normalize(np.asarray([n_origin], dtype=np.float), norm="l2", axis=1)
        matrix[1] = normalize(np.asarray([n_referer], dtype=np.float), norm="l2", axis=1)
        matrix[0] = matrix[0][0]
        matrix[1] = matrix[1][0]

        cosine = round(cosine_sim(n_origin, n_referer) * 100, 2)
        print(cosine, "++++++++++++++")
        jaccard = round(jaccard_similarity(n_origin, n_referer) * 100, 2)
        dice = round(dice_similarity(n_origin, n_referer) * 100, 2)

        euclidean = euclidean_distance(matrix[0], matrix[1])
        manhattan = manhattan_distance(matrix[0], matrix[1])

        minkowski = minkowski_distance(matrix[0], matrix[1], 3)
        weighted = weighted_euclidean_distance(matrix[0], matrix[1], 2)
        mahalanobis = mahalanobis_distance(matrix[0], matrix[1])

        # print((cosine, jaccard, dice, euclidean, manhattan, minkowski, weighted, mahalanobis))
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


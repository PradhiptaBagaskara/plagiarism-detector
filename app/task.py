from django.contrib.auth.models import User
from django_q.tasks import async
from app.models import Document, Similarity
from binfile.distance_measurement import cosine_sim, cosine_similarity, jaccard_similarity, dice_similarity, mahalanobis_distance, \
    euclidean_distance, minkowski_distance, manhattan_distance, weighted_euclidean_distance, weighted_euclidean_distances
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
    from sklearn.metrics.pairwise import pairwise_distances
    import numpy as np

    try:
        sf = Document.objects.get(id=id)
    except Document.DoesNotExist:
        print("Document not Exist")
        return

    datasets = Document.objects.filter(is_dataset=True, status="finished")
    similarities = []
    fingerprints = []
    fingerprints.append(sf.get_fingerprint()['fingerprint'])
    minlen = len(fingerprints[0])
    for d in datasets:
        t_origin = sf.get_fingerprint()['fingerprint']
        t_referer = d.get_fingerprint()['fingerprint']

        if len(t_origin) == 1 or len(t_referer) == 1:
            print("Fingerprint not valid!", d.id)
            continue

        fingerprints.append(t_referer)
        minlen = min(minlen, len(t_referer))

        cosine = cosine_sim(t_origin, t_referer) * 100
        jaccard = jaccard_similarity(t_origin, t_referer) * 100
        dice = dice_similarity(t_origin, t_referer) * 100

        similarities.append([
            d,
            jaccard,
            dice,
            cosine,
        ])

        # print((cosine, jaccard, dice, euclidean, manhattan, minkowski, weighted, mahalanobis), "=================")

    for i, m in enumerate(fingerprints):  # trim length
        if len(m) > minlen:
            fingerprints[i] = m[:minlen]

    matx = normalize(np.asarray(fingerprints, dtype=np.float))
    # matx = fingerprints

    for i, n in enumerate(matx):
        if i == 0:
            continue
        euclidean = np.max(1 - pairwise_distances([matx[0]], [n], metric='euclidean') / np.max(pairwise_distances(matx, metric='euclidean'))) * 100
        manhattan = np.max(1 - pairwise_distances([matx[0]], [n], metric='manhattan') / np.max(pairwise_distances(matx, metric='manhattan'))) * 100
        minkowski = np.max(1 - pairwise_distances([matx[0]], [n], metric='minkowski') / np.max(pairwise_distances(matx, metric='minkowski'))) * 100
        weighted = np.max(1 - weighted_euclidean_distance(matx[0], n, 5) / np.max(weighted_euclidean_distances(matx, 5))) * 100
        mahalanobis = mahalanobis_distance(matx[0], n)
        similarities[i-1] = similarities[i-1] + [euclidean, manhattan, minkowski, weighted, mahalanobis]
        # print(similarities[i-1])

    for sim in similarities:
        d, jaccard, dice, cosine, euclidean, manhattan, minkowski, weighted, mahalanobis = sim

        # print((cosine, jaccard, dice, euclidean, manhattan, minkowski, weighted, mahalanobis), "=================")

        sf.add_similarity(
            d,
            cosine=cosine,
            jaccard=jaccard,
            dice=dice,
            manhattan=manhattan,
            minkowski=minkowski,
            euclidean=euclidean,
            weighted=weighted,
            mahalanobis=mahalanobis
        )


def randome():
    from random import randint
    ma = []
    mb = []

    for a in range(100):
        ma.append(randint(0, 200))
        mb.append(randint(0, 200))

    return [ma, mb]


def normalize(x, y):
    from sklearn.preprocessing import normalize
    import numpy as np

    return normalize(np.asarray([x, y], dtype=np.float), norm="l1", axis=1)

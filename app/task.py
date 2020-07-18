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

from math import *
import numpy as np

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

_DEFAULT_POOL = futures.ThreadPoolExecutor(max_workers=4)


def threadpool(f, executor=None):
    @wraps(f)
    def wrap(*args, **kwargs):
        asyncio.set_event_loop(asyncio.new_event_loop())
        return asyncio.wrap_future((executor or _DEFAULT_POOL).submit(f, *args, **kwargs))

    return wrap

def process_time(id, type="PROCESS", start=None):
    if start:
        elapsed = time.time() - start
        msg = "FINISHED, {}, {}, {}".format(type, id, elapsed)
        with open(os.path.join(settings.MEDIA_ROOT, 'logging.csv'), 'a') as f:
            f.write(msg+'\n')
        print(msg)
        return elapsed, msg
    else:
        start = time.time()
        msg = "START, {}, {}, {}".format(type, id, start)
        # with open(os.path.join(settings.MEDIA_ROOT, 'logging.csv'), 'a') as f:
        #     f.write(msg+'\n')
        print(msg)
        return start, msg


#  for datasets
def process_path(path, username='admin'):
    if not path.endswith("/"):
        path = path + "/"

    if not path.endswith("**"):
        path = path + "**"

    import time
    start = time.time()
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

    print("=== Finished on ", time.time() - start)
    return path


def projson():
    from os import path
    pathh = path.join(settings.MEDIA_ROOT, 'export')
    if not pathh.endswith("/"):
        pathh = pathh + "/"

    if not pathh.endswith("**"):
        pathh = pathh + "**"

    import time
    start = time.time()
    arrai = []
    for filename in glob.iglob(pathh, recursive=True):
        print("Checking", filename)
        will_ignore = False
        for ignore in IGNORE:
            if re.match(ignore, filename):
                print("IGNORING", filename)
                will_ignore = True
                break

        if path.isfile(filename) and not will_ignore and not filename.endswith('merged.json'):
            print("PROCESSING", filename)
            aa = []
            with open(filename, 'r') as fa:
                aa = fa.read()
                aa = json.loads(aa)
            arrai = arrai + aa

    with open(path.join(settings.MEDIA_ROOT, 'export', 'merged.json'), 'w+') as ff:
        ff.write(json.dumps(arrai))

    print("=== Finished on ", time.time() - start)
    return pathh


@threadpool
def process_file_by_path(path, username='admin'):
    _, ext = os.path.splitext(path)
    original_filename = os.path.basename(path)
    if ext not in [".pdf", ".docx", ".doc"]:
        return

    start, _ = process_time(sf.id.hex, type="DATASET FILE")
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
    sf.is_dataset = True
    sf.save()
    finishing_dataset(sf.id)
    process_time(sf.id.hex, type="DATASET FILE", start=start)
    os.remove(path)
    print("DELETE FILE ", path)

    return sf.id


@threadpool
def finishing_dataset(id):
    try:
        sf = Document.objects.get(id=id)
    except Document.DoesNotExist:
        return

    start, _ = process_time(sf.id.hex, type="DATASET FINISH")
    sf.extract_content()
    time.sleep(0.5)
    sf.translate()
    time.sleep(3)
    sf.fingerprinting(save=True, debug=True)
    sf.save()
    process_time(sf.id.hex, type="DATASET FINISH", start=start)


    return sf


# for user document
@threadpool
def process_doc(id):
    try:
        sf = Document.objects.get(id=id)  # filename
    except Document.DoesNotExist:
        print("NOT EXIST", id)
        return
    
    start, _ = process_time(sf.id.hex, type="PROCESS DOC")
    sf.extract_content()
    sf.translate()
    sf.fingerprinting(debug=True)
    sf.save()
    check_similarity(sf.id)
    process_time(sf.id.hex, type="PROCESS DOC", start=start)


# should call from view
def extract_n_process(name, username='admin'):
    from pyunpack import Archive
    dest = os.path.join(settings.MEDIA_ROOT, 'extract')
    src = os.path.join(settings.MEDIA_ROOT, name)
    Archive(src).extractall(dest, auto_create_dir=True)
    process_path(dest, username)
    os.remove(src)
    print('Source Deleted')


def translate_and_finish():
    untranslated = Document.objects.filter(is_dataset=True)
    for unt in untranslated:
        # unt.extract_content()
        # unt.translate()
        # print("Translating ", unt.id)
        unt.fingerprinting(save=True, debug=True)
        print("Fingerprinting ", unt.id)
        # time.sleep(5)


@threadpool
def check_similarity(id):
    from sklearn.preprocessing import normalize
    from sklearn.metrics.pairwise import pairwise_distances

    mode = 1

    try:
        sf = Document.objects.get(id=id)
    except Document.DoesNotExist:
        print("Document not Exist")
        return
    start, _ = process_time(sf.id.hex, type="SIMILARITY")
    sf.status = Document.Statuses.PROCESS
    sf.save()

    datasets = Document.objects.filter(is_dataset=True, status="finished")
    similarities = []
    fingerprints = []
    t_origin = sf.get_fingerprint()['fingerprint']
    t_debug = sf.get_fingerprint()['debug']
    fingerprints.append(t_origin)
    minlen = len(fingerprints[0])
    maxlen = len(fingerprints[0])

    bag = []

    for d in datasets:
        reff = d.get_fingerprint()
        t_referer = reff['fingerprint']

        if len(t_origin) <= 1 or len(t_referer) <= 1:
            print("Fingerprint not valid!", d.id)
            continue
        
        az = set(t_referer).intersection(set(t_origin))
        asz = [x[0] for x in t_debug['hashes'] if x[1] in az]
        bag.append(asz)

        text1, text2 = padd_to_max(t_origin, t_referer) if mode == 1 else trim_to_min(t_origin, t_referer)
        cosine = cosine_sim(text1, text2) * 100
        jaccard = jaccard_similarity(text1, text2) * 100
        dice = dice_similarity(text1, text2) * 100

        minlen = min(minlen, len(t_referer))
        maxlen = max(maxlen, len(t_referer))
        fingerprints.append(t_referer) # append as set

        similarities.append([
            d,
            jaccard,
            dice,
            cosine,
        ])

        # print((cosine, jaccard, dice, euclidean, manhattan, minkowski, weighted, mahalanobis), "=================")
    # fingerprints, _,_ = norm(fingerprints)
    
    if mode == 0:
        for i, m in enumerate(fingerprints):  # trim length
            if len(m) > minlen:
                fingerprints[i] = m[:minlen]
    elif mode == 1:
        for i, m in enumerate(fingerprints):  # padding
            if len(m) < maxlen:
                fingerprints[i] = m + [0.0 for a in range(0, maxlen - len(m))]
     
    matx = normalize(np.asarray(fingerprints, dtype=np.float))
    # matx = fingerprints

    with open(os.path.join(settings.MEDIA_ROOT, 'data', 'bag-'+sf.id.hex+'.json'), 'w') as fx:
        # fx.write(json.dumps(matx))
        fx.write(json.dumps(bag))

    # tcov = np.array(matx).T
    # # print(cov.shape)
    # ccov = np.cov(tcov)
    # iccov = np.linalg.inv(ccov)

    for i, n in enumerate(matx):
        if i == 0:
            continue
        euclidean = euclidean_distance(matx[0], n)
        manhattan = manhattan_distance(matx[0], n)
        minkowski = minkowski_distance(matx[0], n, 2)
        weighted = weighted_euclidean_distance(matx[0], n, 5)
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

    sf.status = Document.Statuses.FINISHED
    sf.save()
    process_time(sf.id.hex, type="SIMILARITY", start=start)

@threadpool
def refingerprint():
    docs = Document.objects.all()

    for d in docs:
        print(d.fingerprinting(debug=True))
        # if d.is_dataset:
        # else:
        #     print(d.fingerprinting())
    
    return True


def recheck():
    docs = Document.objects.filter(is_dataset=False)

    for d in docs:
        check_similarity(d.id)
    
    return True


def randome():
    from random import randint
    ma = []
    mb = []

    for a in range(100):
        ma.append(randint(0, 200))
        mb.append(randint(0, 200))

    return [ma, mb]


def norm(arr):
    maxes = max(map(max, arr))
    minus = min(map(min, arr))
    new = []

    for i, a in enumerate(arr):
        subnew = []
        for s in arr[i]:
            subnew.append((s-minus)/(maxes-minus))
        new.append(subnew)

    return new, minus, maxes


def trim_to_min(text1 = [], text2 = []):
    text1 = list(set(text1))
    text2 = list(set(text2))

    if len(text1) > len(text2):
        text1 = text1[:len(text2)]
    elif len(text1) < len(text2):
        text2 = text2[:len(text1)]

    return text1, text2

def padd_to_max(text1 = [], text2 = []):
    text1 = text1
    text2 = text2

    if len(text1) > len(text2):
        text2 = text2 + [0 for a in range(0, len(text1) - len(text2))]
    elif len(text1) < len(text2):
        text1 = text1 + [0 for a in range(0, len(text2) - len(text1))]

    return text1, text2


class NRollingHash(object):
    def __init__(self, text, base_size=256, modulo=1000003, kgram=5):
        self.text = text
        self.base_size = base_size
        self.modulo = modulo
        self.modulo_power = 1
        self.kgram = kgram
        self.hashes = []
        super().__init__()

    def normal_hash(self, text):
        text = text.split(' ')
        p_hash = 0
        self.modulo_power = 1
        for i in range(len(text)):
            p_hash = (hash(text[i]) + p_hash * self.base_size) % self.modulo
            if i == len(text) - 1:
                continue
            self.modulo_power = (self.modulo_power * self.base_size) % self.modulo
        return p_hash 

    def rolling_hash(self, ohash, pre, nex):
        return ((ohash - hash(pre) * self.modulo_power) * self.base_size + hash(nex)) % self.modulo

    def hash_kgrams(self, kgrams=[]): # mod
        prev_kgram = kgrams[0]
        self.hashes = []
        prev_hash = self.normal_hash(' '.join(prev_kgram))
        self.hashes.append(prev_hash)
        # print(prev_hash, prev_kgram)
        for i, cur_kgram in enumerate(kgrams[1:]):
            prev_hash = self.rolling_hash(
                prev_hash, prev_kgram[0], cur_kgram[-1])
            self.hashes.append(prev_hash)
            prev_kgram = cur_kgram
            # print(prev_hash, prev_kgram)

        return self.hashes

    def compare(self):
        text = self.text.split(' ')
        p_len = self.kgram
        cur_gram = ' '.join(text[0:p_len])
        cur_hash = self.normal_hash(cur_gram)
        rolled = []
        normal = []
        rolled.append((cur_hash, cur_gram))
        print('N', cur_gram)

        for i in range(0, len(text) - p_len + 1):
            cur_gram = ' '.join(text[i:i+p_len])
            print('N', cur_gram)

            nh = self.normal_hash(cur_gram)
            normal.append((nh, cur_gram))
            
            if i == len(text) - p_len:
                    continue
            # print(text[i:i+p_len])
            # print(text[i], text[i+p_len])
            cur_hash = self.rolling_hash(cur_hash, text[i], text[i+p_len])
            rolled.append((cur_hash, [text[i], text[i+p_len]]))
        
        valid = []

        for a, b in zip(rolled, normal):
            valid.append(a[0] == b[0])

        return normal, rolled, len(set(valid)) == 1 and valid[0]


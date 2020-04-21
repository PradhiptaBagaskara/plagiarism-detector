from django.contrib.auth.models import User
# from django_q.tasks import async
from app.models import Document, Similarity
from binfile.distance_measurement import cosine_sim, jaccard_similarity, dice_similarity

import glob
import re
import os
import json

from django.core.files.base import ContentFile
from django.core.files import File

IGNORE = [
    "env",
    ".local",
    ".git",
]

#  for datasets
def process_path(path):

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
            process_file_by_path(filename)

    return path

def process_file_by_path(path):
    _, ext = os.path.splitext(path)
    print(ext)
    if ext not in [".pdf"]:
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

    user = User.objects.get(username='admin')  # static
    sf.user = user
    with open(path, mode="rb") as file:
        sf.content.save(name=os.path.basename(path), content=file)

    sf.save()
    finishing_dataset(sf.id)

    return sf.id

def finishing_dataset(id):
    try:
        sf = Document.objects.get(id=id)
    except Document.DoesNotExist:
        return

    sf.extract_content()
    sf.fingerprinting()
    sf.is_dataset = True
    sf.save()

    return sf

# for user document
def process_doc(id):
    try:
        sf = Document.objects.get(id=id)  # filename
    except Document.DoesNotExist:
        print("NOT EXIST", id)
        return

    sf.extract_content()
    sf.fingerprinting()
    sf.save()
    check_similarity(sf.id)

    return sf.id

def process_hook(task):
    print(task.result)

def check_similarity(id):
    try:
        sf = Document.objects.get(id=id)
    except Document.DoesNotExist:
        print("Document not Exist")
        return

    datasets = Document.objects.filter(is_dataset=True, status="finished")
    similarty = sf.similarity if hasattr(sf, 'similarity') else Similarity(document=sf)
    similarty.save()
    sim = {}

    for d in datasets:
        pre = {
            'winnowing': {
                'cosine': cosine_sim(sf.get_fingerprint()['word_winnowing'], d.get_fingerprint()['word_winnowing']),
                'jaccard': jaccard_similarity(sf.get_fingerprint()['word_winnowing'], d.get_fingerprint()['word_winnowing']),
                'dice': dice_similarity(sf.get_fingerprint()['word_winnowing'], d.get_fingerprint()['word_winnowing']),
            }
        }
        sim[d.id.hex] = pre

    res = json.dumps(sim)

    similarty.content.save('any', content=ContentFile(res))

    print(res)


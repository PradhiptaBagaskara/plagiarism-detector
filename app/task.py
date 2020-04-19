from django.contrib.auth.models import User
# from django_q.tasks import async
from app.models import Document

import glob
import re
import os

IGNORE = [
    "env",
    ".local",
    ".git",
]


def process_path(path):

    if not path.endswith("/"):
        path = path + "/"

    # if not path.endswith("**"):
    #     path = path + "**"

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


def process_hook(task):
    print(task.result)


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
    sf.extract_content()
    sf.fingerprinting()
    sf.save()

    return sf.id

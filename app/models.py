# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

from django.db import models
from django.contrib.auth.models import User
import uuid
import mimetypes
import os
from io import StringIO
from pdfminer.high_level import extract_text, extract_text_to_fp
from pdfminer.layout import LAParams

from binfile.winnowing_ngram import winnow as n_winnow
from binfile.winnowing_wordgram import winnow as word_winnow
from binfile.rabin import rabin_word
from django.utils.translation import gettext as _
import json

from django.core.files.base import ContentFile
from django.core.files import File

from google.cloud import translate_v2 as translate

# Create your models here.

def _get_upload_path(instance, filename):
  ident = uuid.uuid4().hex
  if instance.user:
    path = "document/%s-%s-%s" % (
      ident[:2],
      ident[:8],
      filename
    )
  else:
    path = "unsorted/%s-%s-%s" % (
      ident[:2],
      ident[:8],
      filename
    )

  if not instance.filename:
    instance.filename = filename

  return path

def _similarity_result_path(instance, filename):
  ident = uuid.uuid4().hex
  if instance.content.name:
      instance.content.delete()

  if instance.document:
    path = "similarity/%s%s" % (
      instance.document.filename,
      ".txt"
    )
  else:
    path = "similarity/%s-%s-%s" % (
      ident[:2],
      ident[:8],
      filename
    )

  return path

def _text_path(instance, filename):
  if instance.text.name:
      instance.text.delete()

  path = "text/%s%s" % (
    instance.filename,
    ".txt"
  )

  return path

def _html_path(instance, filename):
  if instance.html.name:
      instance.html.delete()

  path = "html/%s%s" % (
    instance.filename,
    ".html"
  )

  return path

def _fingerprint_path(instance, filename):
  if instance.fingerprint.name:
      instance.fingerprint.delete()

  path = "fingerprint/%s%s" % (
    instance.filename,
    ".fp"
  )

  return path

class Document(models.Model):

  class Statuses(models.TextChoices):
    UPLOADED = 'uploaded', _('Uploaded')
    PROCESS = 'process', _('Process')
    FINISHED = 'finished', _('Finished')

  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  filename = models.CharField(max_length=128, db_index=True, blank=True)
  metadata = models.TextField(blank=True, null=True)
  lang = models.CharField(max_length=50, blank=True)
  user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
  title = models.CharField(max_length=191, null=True, blank=True)
  author = models.CharField(max_length=191, null=True, blank=True)
  content = models.FileField(upload_to=_get_upload_path, max_length=191, unique=True, db_index=True)
  text = models.FileField(upload_to=_text_path, max_length=191)
  html = models.FileField(upload_to=_html_path, max_length=191)
  keyword = models.CharField(max_length=191, null=True, blank=True)
  size_bytes = models.IntegerField(default=0, db_index=True)
  fingerprint = models.FileField(upload_to=_fingerprint_path, max_length=191)
  is_dataset = models.BooleanField(default=False)
  status = models.CharField(max_length=10, choices=Statuses.choices, default=Statuses.UPLOADED)
  created = models.DateTimeField(auto_now_add=True, editable=False, help_text="DB Insertion Time")
  modified = models.DateTimeField(auto_now=True, editable=False, help_text="DB Modification Time")

  def __str__(self):
    return "{}".format(self.content.name)

  def save(self, *args, **kwargs):

    self.size_bytes = self.content.size
    self.filename, _ = os.path.splitext(os.path.basename(self.content.path))
    super(Document, self).save(*args, **kwargs)

  def extract_content(self):
    if not self.text.name or self.text.name == "":
        self.status = "process"
        text = StringIO()
        html = StringIO()
        extract_text_to_fp(self.content, text)
        extract_text_to_fp(self.content, html, laparams=LAParams(), output_type='html', codec=None)
        with ContentFile(content=text.getvalue().encode("utf-8")) as file:
            self.text.save(name='any', content=File(file))

        with ContentFile(content=html.getvalue().encode("utf-8")) as file:
            self.html.save(name='any', content=file)

    return "{}".format(self.text.name)

  def translate(self):
    text = self.get_text()
    if text is None:
        return

    # os.environ['GRPC_DNS_RESOLVER'] = 'native'
    translate_client = translate.Client()

    try:
      result = translate_client.translate(text, target_language="id")
      self.lang = result['detectedSourceLanguage']
      with ContentFile(content=result['translatedText'].encode("utf-8")) as file:
          self.text.save(name='any', content=File(file))
      return True
    except:
      print("Translate Error")
      return False

  def fingerprinting(self, save=True, debug=False):
    if not self.text.name:
        return

    kgram = 6

    result = {}
    jsonf = {}
    with self.text.open(mode="rb") as file:
        read = file.read().decode('utf-8')
        result['word_winnowing'] = word_winnow(text=read, k=kgram, debug=debug)
        result['n_winnowing'] = n_winnow(text=read, k=kgram, debug=debug)
        result['rabin'] = rabin_word(text=read, k=kgram, debug=debug)
        jsonf['word_winnowing'] = result['word_winnowing']['data']
        jsonf['n_winnowing'] = result['n_winnowing']['data']
        jsonf['rabin'] = result['rabin']['data']

    if save:
        self.status = "finished"
        name, _ = os.path.splitext(os.path.basename(self.content.path))
        filename = '%s.fp' % name
        fp = json.dumps(jsonf).encode("utf-8")
        with ContentFile(content=fp) as file:
            self.fingerprint.save(name=filename, content=file)
    
    return result

  def get_text(self):
    if not self.text.name:
      return

    text = ""
    with self.text.open(mode="rb") as file:
      text = file.read().decode('utf-8')

    return "{}".format(text)

  def get_html(self):
    if not self.html.name:
      return

    html = ""
    with self.html.open(mode="rb") as file:
      html = file.read().decode('utf-8')

    return "{}".format(html)

  def get_fingerprint(self):
    if not self.fingerprint:
      return

    fp = ""
    with self.fingerprint.open(mode="rb") as file:
        fp = file.read().decode('utf-8')
    
    return json.loads(fp)

  def get_actions(self):
    html = '<div class="btn-group">'
    html += '<a href="/fingerprint/{}" class="btn btn-primary"> Fingerprint</a>'.format(self.filename)
    if self.is_dataset and self.status != 'finished':
      html += '<a href="/dataset/{}/finish" class="btn btn-warning"> Finish Dataset</a>'.format(self.id)
    if not self.is_dataset and self.status == 'finished' and hasattr(self, 'similarity') and self.similarity.content.name == '':
      html += '<a href="/similarity/{}/check" class="btn btn-warning"> Check</a>'.format(self.id)
    html += '<a href="#" class="btn btn-success"> Edit</a>'
    html += '</div>'
    
    return html

  def serialize(self):
    return {
      "id": self.id,
      "author": self.author,
      "title": self.title,
      "keyword": self.keyword,
      "fingerprint": self.fingerprint,
      "name": self.content.name,
      "filename": self.filename,
      "metadata": self.metadata,
      "size_bytes": self.size_bytes,
      "content_path": self.content.path,
      "created": self.created.isoformat() if self.created else None,
      "modified": self.modified.isoformat() if self.modified else None,
    }
  

class Similarity(models.Model):
  document = models.OneToOneField("Document", related_name="similarity", on_delete=models.CASCADE)
  content = models.FileField(upload_to=_similarity_result_path, max_length=191, blank=True)
  created = models.DateTimeField(auto_now_add=True, editable=False, help_text="DB Insertion Time")
  modified = models.DateTimeField(auto_now=True, editable=False, help_text="DB Modification Time")

  def __str__(self):
    return "%s Similarity" % self.document.filename

  def get_result(self):
    if not self.content.name:
      return
    
    result = ""
    with self.content.open(mode="rb") as file:
      result = file.read().decode("utf-8")

    return result


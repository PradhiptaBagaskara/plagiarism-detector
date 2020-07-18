# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2020 - Winnowing Similarity Measurement
"""

from django.db import models
from django.contrib.auth.models import User
from django.shortcuts import resolve_url
import uuid
import mimetypes
import os
from io import StringIO
from pdfminer.high_level import extract_text, extract_text_to_fp
from pdfminer.layout import LAParams
from django.conf import settings
import mammoth

from django.conf import settings

from binfile.winnowing_ngram import winnow as n_winnow
from binfile.winnowing_wordgram import winnow as word_winnow
from binfile.rabin import rabin_word
from binfile.fingerprint import WinnowingFingerprint
from django.utils.translation import gettext as _
import json

from django.core.files.base import ContentFile
from django.core.files import File

from django.template.loader import render_to_string

from google.cloud import translate_v2 as translate
from math import *


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


def _simfmt(point, enable=True):
    if enable:
        # return pow(10, -point) * 100
        return round(point, 3)
    return point


class Document(models.Model):
    class Statuses(models.TextChoices):
        UPLOADED = 'uploaded', _('Uploaded')
        PROCESS = 'process', _('Process')
        FINISHED = 'finished', _('Finished')

    class Meta:
        permissions = (
            ("add_dataset", "can add dataset"),
            ("change_dataset", "can change dataset"),
            ("delete_dataset", "can delete dataset"),
            ("view_dataset", "can view dataset"),
        )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filename = models.CharField(max_length=128, db_index=True, blank=True)
    original_filename = models.CharField(max_length=128, blank=True)
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
    similarities = models.ManyToManyField('self', through='Similarity', symmetrical=False, related_name='similar_to')
    status = models.CharField(max_length=10, choices=Statuses.choices, default=Statuses.UPLOADED)
    created = models.DateTimeField(auto_now_add=True, editable=False, help_text="DB Insertion Time")
    modified = models.DateTimeField(auto_now=True, editable=False, help_text="DB Modification Time")

    def __str__(self):
        return "{}".format(self.content.name)

    def add_similarity(self, dataset, cosine=0.0, jaccard=0.0, dice=0.0, manhattan=0.0, minkowski=0.0, mahalanobis=0.0, euclidean=0.0, weighted=0.0):
        similarity, created = Similarity.objects.update_or_create(
            document=self,
            dataset=dataset,
        )

        similarity.cosine = cosine
        similarity.jaccard = jaccard
        similarity.dice = dice
        similarity.manhattan = manhattan
        similarity.minkowski = minkowski
        similarity.mahalanobis = mahalanobis
        similarity.euclidean = euclidean
        similarity.weighted = weighted
        similarity.save()

        return similarity

    def remove_similarity(self, dataset):
        Similarity.objects.filter(
            document=self,
            dataset=dataset).delete()
        return

    def get_datasets(self):
        return self.similarities.filter(
            to_datasets__document=self)

    def get_similarity(self, as_table=False):
        sort = ['-dice', '-jaccard', '-cosine', 'euclidean', 'weighted', 'minkowski', 'manhattan']
        # sort = ['-euclidean', '-weighted', '-manhattan']
        similarity = Similarity.objects.filter(document=self).order_by(*sort)[:10]
        result = []
        if as_table:
            res = list(similarity)
            # jsoning = []
            for item in res:
                # jsoning.append(item.serialize())
                result.append(item)

            # pa = os.path.join(settings.MEDIA_ROOT, 'export', self.id.hex+'.json')
            # with open(pa, mode='w+') as fa:
            #     aa = json.dumps(jsoning)
            #     fa.write(aa)


            result = render_to_string('document/includes/similarity-table.html', {'data': result})
        else:
            result = similarity
            result.label = [a[:15] for a in similarity.values_list('dataset__original_filename', flat=True)]
            result.cosine = list(similarity.values_list('cosine', flat=True))
            result.dice = list(similarity.values_list('dice', flat=True))
            result.jaccard = list(similarity.values_list('jaccard', flat=True))
            
            result.minkowski = [_simfmt(a) for a in similarity.values_list('minkowski', flat=True)]
            result.manhattan = [_simfmt(a) for a in similarity.values_list('manhattan', flat=True)]
            result.euclidean = [_simfmt(a) for a in similarity.values_list('euclidean', flat=True)]
            result.weighted = [_simfmt(a) for a in similarity.values_list('weighted', flat=True)]
            result.mahalanobis = [_simfmt(a, False) for a in similarity.values_list('mahalanobis', flat=True)]

        return result

    def get_compared_to(self):
        return self.similar_to.filter(
            form_documents__dataset=self)

    def save(self, *args, **kwargs):
        if self.content.name:
            self.size_bytes = self.content.size
            self.filename, _ = os.path.splitext(os.path.basename(self.content.path))

        super(Document, self).save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        if self.fingerprint.name != '' and self.fingerprint.storage.exists(self.fingerprint.name):
            self.fingerprint.delete()
        if self.html.name != '' and self.html.storage.exists(self.html.name):
            self.html.delete()
        if self.text.name != '' and self.text.storage.exists(self.text.name):
            self.text.delete()
        try:
            if self.content.name != '' and self.content.storage.exists(self.content.name):
                self.content.delete()
        except PermissionError:
            print("permission error : ", self.content.path)

        super().delete()

    def extract_content(self):
        self.status = Document.Statuses.PROCESS

        text = StringIO()
        html = StringIO()

        _, ext = os.path.splitext(self.content.path)
        with self.content as file:
            if ext == ".pdf":
                laparams = LAParams()
                setattr(laparams, 'all_texts', True)
                extract_text_to_fp(self.content, text, laparams=laparams)
                extract_text_to_fp(self.content, html, laparams=laparams, output_type='html', codec=None)
            elif ext in [".docx", ".doc"]:
                result = mammoth.convert_to_html(file)
                html.write(result.value)
                result = mammoth.extract_raw_text(file)
                text.write(result.value)

        with ContentFile(content=text.getvalue().encode("utf-8")) as file:
            self.text.save(name='any', content=file)

        with ContentFile(content=html.getvalue().encode("utf-8")) as file:
            self.html.save(name='any', content=file)

        return "{}".format(self.text.name)

    def translate(self):
        if settings.TRANSLATION_ENABLED:
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
        kgram = 7

        result = {}
        jsonf = {}
        wf = WinnowingFingerprint(kgram_len=kgram, window_len=5, base=256, modulo=100003)
        with self.text.open() as file:
            read = file.read().decode('utf-8')
            # import StemmerFactory class
            # from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
            # # create stemmer
            # factory = StemmerFactory()
            # stemmer = factory.create_stemmer()
            # # stemming process
            # read = stemmer.stem(read)
            result['fingerprint'] = wf.generate(str=read, debug=debug) if settings.FINGERPRINTING == 'winnowing' else \
                                    rabin_word(text=read, k=kgram, debug=debug)

            jsonf['fingerprint'] = result['fingerprint']['data']
            jsonf['debug'] = result['fingerprint']['steps']

        if save:
            self.status = Document.Statuses.FINISHED
            name, _ = os.path.splitext(os.path.basename(self.content.path))
            filename = '%s.fp' % name
            fp = json.dumps(jsonf).encode("utf-8")
            with ContentFile(content=fp) as file:
                self.fingerprint.save(name=filename, content=file)

        return "{} Finished".format(self.id)

    def get_text(self):
        if not self.text.name:
            return

        text = ""
        with self.text as file:
            text = file.read().decode('utf-8')

        return "{}".format(text)

    def get_html(self):
        if not self.html.name:
            return

        html = ""
        with self.html as file:
            html = file.read().decode('utf-8')

        return "{}".format(html)

    def get_fingerprint(self):
        if not self.fingerprint:
            return
        fp = ""
        with self.fingerprint.open() as file:
            fp = file.read().decode('utf-8')

        return json.loads(fp)

    def get_actions(self):
        html = '<div class="btn-group">'
        # html += self.btn('fingerprint')
        html += self.btn('show')
        if self.status != 'finished':
            html += self.btn('finish')

        if not self.is_dataset and self.status == 'finished':
            if self.similarities.count() > 0:
                html += self.btn('similarity')
                html += self.btn('check')
            # else:

        html += self.btn('edit')
        html += self.btn('delete')
        html += '</div>'
        return html

    def btn(self, name='show'):
        buttons = {
            "show": '<a href="%s" class="btn btn-success"> Show</a>' % resolve_url(to='document.show', id=self.id),
            "edit": '<a href="%s" class="btn btn-success"> Edit</a>' % resolve_url(to='document.edit', id=self.id),
            "delete": '<a href="%s" class="btn btn-danger"> Delete</a>' % resolve_url(to='document.delete', id=self.id),
            "finish": '<a href="%s" class="btn btn-warning"> Finishing</a>' % resolve_url(to='document.finish',
                                                                                          id=self.id),
            "fingerprint": '<a href="%s" class="btn btn-primary"> Fingerprint</a>' % resolve_url(
                to='document.fingerprint', id=self.id),
            "check": '<a href="%s" class="btn btn-warning"> Check</a>' % resolve_url(to='document.check', id=self.id),
            "similarity": '<a href="%s" class="btn btn-success"> Result</a>' % resolve_url(to='document.similarity',
                                                                                           id=self.id),
        }
        return buttons.get(name, "")

    def status_badge(self):
        type = '%s' % 'success' if self.status == 'finished' else 'warning' if self.status == 'process' else 'primary'
        badge = '<h5><span class="badge badge-%s">%s</span></h5>' % (type, self.status)
        return badge

    def serialize(self):
        return {
            "id": self.id.hex,
            "author": self.author,
            "title": self.title,
            "keyword": self.keyword,
            "fingerprint": resolve_url(to='document.fingerprint', id=self.id),
            "name": self.content.name,
            "filename": self.filename,
            "metadata": self.metadata,
            "size_bytes": self.size_bytes,
            "content_path": self.content.path,
            "created": self.created.isoformat() if self.created else None,
            "modified": self.modified.isoformat() if self.modified else None,
        }


class Similarity(models.Model):
    document = models.ForeignKey("Document", related_name="form_documents", on_delete=models.CASCADE)
    dataset = models.ForeignKey("Document", related_name="to_datasets", on_delete=models.CASCADE)
    cosine = models.FloatField(null=True, default=0.0)
    jaccard = models.FloatField(null=True, default=0.0)
    dice = models.FloatField(null=True, default=0.0)
    manhattan = models.FloatField(null=True, default=0.0)
    minkowski = models.FloatField(null=True, default=0.0)
    mahalanobis = models.FloatField(null=True, default=0.0)
    euclidean = models.FloatField(null=True, default=0.0)
    weighted = models.FloatField(null=True, default=0.0)
    content = models.FileField(upload_to=_similarity_result_path, max_length=191, blank=True) # change to save additional information only
    created = models.DateTimeField(auto_now_add=True, editable=False, help_text="DB Insertion Time")
    modified = models.DateTimeField(auto_now=True, editable=False, help_text="DB Modification Time")

    def __str__(self):
        return "%s Similarity" % self.document.filename

    def serialize(self):
        return {
            "id": self.id,
            "document_filename": self.document.filename,
            "document": self.document.id.hex,
            "dataset": self.dataset.id.hex,
            "dice": self.dice,
            "jaccard": self.jaccard,
            "cosine": self.cosine,
            "manhattan": self.manhattan,
            "minkowski": self.minkowski,
            "mahalanobis": self.mahalanobis,
            "euclidean": self.euclidean,
            "weighted": self.weighted,
            "created": self.created.isoformat() if self.created else None,
            "modified": self.modified.isoformat() if self.modified else None,
        }

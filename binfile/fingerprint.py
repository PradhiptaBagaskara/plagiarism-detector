#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generates fingerprints of text document.
"""
import string
import sys

__author__ = 'kailash.buki@gmail.com (Kailash Budhathoki)'
__all__ = [
    'WinnowingFingerprint',
    'FingerprintException',
]

guid = lambda x: ord(x)

def _hash(stri):
    hash = 0
    for i, c in enumerate(stri):
        hash += ord(c) * 256 ** (len(stri) - 1 - i)
    hash = hash % 100003
    return hash

from math import *


class FingerprintException(Exception):

    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


class WinnowingFingerprint(object):
    """
    Generates fingerprints of the input text file or plain string. Please consider taking a look at http://theory.stanford.edu/~aiken/publications/papers/sigmod03.pdf for detailed description on how fingerprints are computed.

    Attributes:
        kgram_len (Optional[int]): length of the contiguous substring. Defaults to 50.
        base (Optional[int]): base required for computing the rolling hash function. Defaults to 101.
        modulo (Optional[int]): hash values cannot exceed this value. Defaults to sys.maxint.
        window_len (Optional[len]): length of the windows when computing fingerprints. Defaults to 100.
        kgrams (List(str)): k-grams extracted from the text
        hashes (List(int)): hash values of the k-grams
        fingerprints (List(tuple(int))): selected representative hash values along with their positions.
    """

    def __init__(self, kgram_len=None, base=None, modulo=None, window_len=None):
        self.kgram_len = kgram_len or 7
        self.base = base or 256
        self.modulo = modulo or 100003
        self.window_len = window_len or 5
        self.windows = []

    def get_min_with_pos(self, sequence):
        min_val = sys.maxsize
        min_pos = 0
        for pos, val in enumerate(sequence):
            if val <= min_val:
                min_val = val
                min_pos = pos
        return min_val, min_pos

    def normal_hash(self, text):
      text = text.split(' ')
      p_hash = 0
      modulus_power = 1
      for i in range(len(text)):
          p_hash = (_hash(text[i]) + p_hash * self.base) % self.modulo
          if i == len(text) - 1:
              continue
          modulus_power = (modulus_power * self.base) % self.modulo
      return modulus_power, p_hash 

    def rolling_hash(self, ohash, pre, nex, modulus_power):
        return ((ohash - _hash(pre) * modulus_power) * self.base + _hash(nex)) % self.modulo


    def prepare_storage(self):
        self.kgrams = []
        self.hashes = []
        self.fingerprints = []
        self.str = ""

    def generate_kgrams(self):
        self.str = self.str.split(' ')
        self.kgrams = [self.str[i:i + self.kgram_len]
                       for i in range(len(self.str) - self.kgram_len + 1)]

    def hash_kgrams(self):
        prev_kgram = self.kgrams[0]
        mods, prev_hash = self.normal_hash(' '.join(prev_kgram))
        self.hashes.append(prev_hash)
        # print(prev_hash, prev_kgram)
        for i, cur_kgram in enumerate(self.kgrams[1:]):
            prev_hash = self.rolling_hash(
                prev_hash, prev_kgram[0], cur_kgram[-1], mods)
            self.hashes.append(prev_hash)
            prev_kgram = cur_kgram
            # print(prev_hash, prev_kgram)


    def generate_fingerprints(self):
        self.windows = [self.hashes[i:i + self.window_len]
                   for i in range(len(self.hashes) - self.window_len + 1)]

        cur_min_hash, cur_min_pos = self.get_min_with_pos(self.windows[0])
        self.fingerprints.append((cur_min_hash, cur_min_pos))

        for i, window in enumerate(self.windows[1:]):
            min_hash, min_pos = self.get_min_with_pos(window)
            min_pos += i + 1
            if min_hash != cur_min_hash or min_hash == cur_min_hash and min_pos > cur_min_pos:
                cur_min_hash, cur_min_pos = min_hash, min_pos
                self.fingerprints.append((min_hash, min_pos))

    def validate_config(self):
        if len(self.str) < self.window_len:
            raise FingerprintException(
                "Length of the string is smaller than the length of the window.")

    def sanitize(self, stri): # mod
        sanitized = stri

        import re
        sanitized = sanitized.lower().strip()
        sanitized = re.sub(r'[\'|\"]+', '', sanitized)
        sanitized = re.sub(r'[^\w]', ' ', sanitized)
        sanitized = re.sub(r'[^\x00-\x7F]+',' ', sanitized)
        sanitized = re.sub(r'\n+', ' ', sanitized)
        sanitized = re.sub(r'\r+', ' ', sanitized)
        sanitized = re.sub(r'\s+', ' ', sanitized)
        return sanitized

    def generate(self, str=None, debug=False):
        """generates fingerprints of the input. Either provide `str` to compute fingerprint directly from your string or `fpath` to compute fingerprint from the text of the file. Make sure to have your text decoded in `utf-8` format if you pass the input string.

        Args:
            str (Optional(str)): string whose fingerprint is to be computed.

        Returns:
            List(int): fingerprints of the input.

        Raises:
            FingerprintException: If the input string do not meet the requirements of parameters provided for fingerprinting.
        """

        result = {
            'steps': {
                'sanitize': [],
                'gram': [],
                'hashes': [],
                'windows': [],
            },
            'data': []
        }

        try:
          self.prepare_storage()
          self.str = self.sanitize(str)
          self.validate_config()
          self.generate_kgrams()
          # print(len(self.kgrams))
          self.hash_kgrams()
        #   print(self.hashes[:10])
          self.generate_fingerprints()
        except FingerprintException:
          return result
        

        xipped = [[b, a] for a, b in zip(self.hashes, self.kgrams)]
        wipped = [[['', b] for b in a] for a in self.windows]
        # print(wipped[:10])

        result['steps']['sanitize'] = self.str if debug else []
        result['steps']['gram'] = self.kgrams if debug else []
        result['steps']['hashes'] = xipped if debug else []
        result['steps']['windows'] = wipped if debug else []
        result['data'] = list(map(lambda x: x[0], self.fingerprints))

        return result

    def load_file(self, fpath):
        with open(fpath, 'r') as fp:
            data = fp.read().decode('utf-8')
        return data




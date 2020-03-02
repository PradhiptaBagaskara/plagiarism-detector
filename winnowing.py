def sanitize(text):
  import re
  p = re.compile(r'\w', re.UNICODE)

  def f(c):
    return p.match(c[1]) is not None

  return filter(f, map(lambda x: (x[0], x[1].lower()), text))


def kgrams(text, k=5):
  text = list(text)
  n = len(text)

  if n < k:
    yield text
  else:
    for i in range(n - k + 1):
      yield text[i:i+k]


def winnowing_hash(kgram):
  kgram = zip(*kgram)
  kgram = list(kgram)

  # FIXME: What should we do when kgram is shorter than k?
  text = ''.join(kgram[1]) if len(kgram) > 1 else ''

  hs = hash_function(text)

  # FIXME: What should we do when kgram is shorter than k?
  return (kgram[0][0] if len(kgram) > 1 else -1, hs)


def default_hash(text):
    import hashlib

    hs = hashlib.sha1(text.encode('utf-8'))
    hs = hs.hexdigest()[-4:]
    hs = int(hs, 16)

    return hs

def md5_hash(text):
    import hashlib

    hs = hashlib.md5(text.encode('utf-8'))
    hs = hs.hexdigest()[-4:]
    hs = int(hs, 16)

    return hs

def select_min(window):
    """In each window select the minimum hash value. If there is more than one
    hash with the minimum value, select the rightmost occurrence. Now save all
    selected hashes as the fingerprints of the document.
    :param window: A list of (index, hash) tuples.
    """

    # print(window, min(window, key=lambda x: x[1]))

    return min(window, key=lambda x: x[1])


def winnow(text, k=5):
    n = len(list(text))

    text = zip(range(n), text)
    text = sanitize(text)

    hashes = map(lambda x: winnowing_hash(x), kgrams(text, k))

    windows = kgrams(hashes, 4)

    return set(map(select_min, windows))


# Specified a hash function. You may override this.
hash_function = md5_hash
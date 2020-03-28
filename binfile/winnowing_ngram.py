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
    # print(kgram)
    # FIXME: What should we do when kgram is shorter than k?
    text = ''.join(kgram[1]) if len(kgram) > 1 else ''
    # print(text)
    hs = hash_function(text)

    # FIXME: What should we do when kgram is shorter than k?
    return [kgram[0][0] if len(kgram) > 1 else -1, hs]


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

    return min(window, key=lambda x: x[1])[1]


def winnow(text, k=5, debug=False):
    import copy
    tmp_text = text
    splitlen = 10
    result = {
      'steps' : {
        'sanitize' : '',
        'gram' : '',
        'hashes' : '',
        'windows' : '',
      },
      'data' : ''
    }

    n = len(list(text))

    text = zip(range(n), text)
    text = sanitize(text)
    tx = copy.deepcopy(text)
    
    hashes = [winnowing_hash(a) for a in kgrams(text, k)]
    windows = [a for a in kgrams(hashes, 4)]
    data = list(map(select_min, windows))

    if debug is True:
        tx1 = copy.deepcopy(tx)
        result['steps']['sanitize'] = tmp_text[:200]
        result['steps']['gram'] = ["".join(ai for i,ai in a) for a in list(kgrams(tx, k))][:splitlen]
        result['steps']['hashes'] = hashes[:splitlen]
        result['steps']['windows'] = windows[:splitlen]
    
    result['data'] = data
    # print(windows)

    return result


# Specified a hash function. You may override this.
hash_function = md5_hash
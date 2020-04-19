def sanitize(text):
    import re
    text = text.lower().strip()
    text = re.sub(r'[^\w|\s]', '', text)
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\r+', ' ', text)
    text = text.split(" ")

    return text


def kgrams(text, k=5):
    text = list(text)
    n = len(text)
    
    if n < k:
      yield text
    else:
      # text = text.split(" ")
      # text = [" ".join(text[i:i+k]) for i,b in enumerate(text, start=0)]
      for i in range(n - k + 1):
        yield text[i:i+k]


def winnowing_hash(kgram):
    # kgram = zip(*kgram)
    kgram = list(kgram)
    # print(kgram)
    # FIXME: What should we do when kgram is shorter than k?
    text = ''.join(kgram) if len(kgram) > 1 else ''
    # print(text)
    hs = hash_function(text)
    # print(hs)
    # FIXME: What should we do when kgram is shorter than k?
    res = [''.join(kgram) if len(kgram) > 1 else -1, hs]
    # print(res)
    return res


def default_hash(text):
    import hashlib

    hs = hashlib.sha1(text.encode('utf-8'))
    hs = hs.hexdigest()[-4:]
    hs = int(hs, 16)

    return hs

def md5_hash(text):
    import hashlib

    hs = hashlib.md5(text.encode())
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
    # sanitize
    text = sanitize(text)
    hashes = [winnowing_hash(a) for a in kgrams(text, k)]
    windows = [a for a in kgrams(hashes, 4)]

    if debug is True:
      result['steps']['sanitize'] = ''
      result['steps']['gram'] = [a for a in kgrams(text, k)][:splitlen]
      result['steps']['hashes'] = hashes[:splitlen]
      result['steps']['windows'] = windows[:splitlen]

    data = list(map(select_min, windows))

    result['data'] = list(set(data))
    # print(data)
    
    return result


# Specified a hash function. You may override this.
hash_function = md5_hash
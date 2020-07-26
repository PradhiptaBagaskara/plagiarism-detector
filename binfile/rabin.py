def sanitize(text):
    import re
    text = text.lower().strip()
    text = re.sub(r'[^\w|\s]', '', text)
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\r+', ' ', text)
    text = text.split(" ")

    return text

def sanitize_grams(text):
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
      # text = text.split(" ")
      # text = [" ".join(text[i:i+k]) for i,b in enumerate(text, start=0)]
      for i in range(n - k + 1):
        yield text[i:i+k]


def winnowing_hash(kgram, mode):
    if mode > 1:
        kgram = zip(*kgram)

    kgram = list(kgram)
    # print(kgram)
    # FIXME: What should we do when kgram is shorter than k?
    if mode > 1:
        text = ''.join(kgram[1]) if len(kgram) > 1 else ''
    else:
        text = ''.join(kgram) if len(kgram) > 1 else ''
    # print(text)
    hs = hash_function(text)
    # print(hs)
    # FIXME: What should we do when kgram is shorter than k?
    if mode > 1:
        res = [''.join(kgram[1]) if len(kgram) > 1 else -1, hs]
        
    else:
        res = [''.join(kgram) if len(kgram) > 1 else -1, hs]
    # print(res)
    return res

def free_search(kgram):
    kgram = list(kgram)
    text = ''.join(kgram) if len(kgram) > 1 else ''
    res = [' '.join(kgram) if len(kgram) > 1 else -1]
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


def rabin_word(text, k=5, debug=False, mode=2):  
    import copy
    tmp_txt = text

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

    # print(text)
    hashes = [winnowing_hash(a, mode) for a in kgrams(text, k)]
    windows = [a for a in kgrams(hashes, k)]

    if debug is True:
        # if mode > 1:
        #     tx1 = copy.deepcopy(tx)
        #     result['steps']['sanitize'] = tmp_txt[:200]
        #     result['steps']['gram'] = ["".join(ai for i,ai in a) for a in list(kgrams(tx, k))][:splitlen]
        #     result['steps']['hashes'] = hashes[:splitlen]
        #     # result['steps']['windows'] = ""
        # else:
            result['steps']['sanitize'] = tmp_txt[:20]
            result['steps']['gram'] = [a for a in kgrams(text, k)][:splitlen]
            result['steps']['hashes'] = hashes[:splitlen]
    #   result['steps']['windows'] = windows[:splitlen]

    # data = list(map(select_min, windows))
    data = [a[1] for a in hashes]
    # if mode > 1:
    #     kmp = [a[0] for a in hashes]
    # else:
    #     kmp = [free_search(a) for a in kgrams(text, k)]


    result['data'] = data
    # result['kmp'] = [kmp[index] for index,a in enumerate(kmp)]
    # print(kmp)
    # print(space)
    
    return result




# Specified a hash function. You may override this.
hash_function = md5_hash
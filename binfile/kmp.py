from sklearn.feature_extraction.text import TfidfVectorizer
import nltk,re
from nltk.util import ngrams
from nltk.tokenize import sent_tokenize,word_tokenize
 
def clean_full(string):
    # string = re.sub(r"\'s", "", string)
    # string = re.sub(r"\'ve", "", string)
    # string = re.sub(r"n\'t", "", string)
    # string = re.sub(r"\'re", "", string)
    # string = re.sub(r"\'d", "", string)
    # string = re.sub(r"\'ll", "", string)
    # string = re.sub(r",", "", string)
    # string = re.sub(r"!", " ! ", string)
    # string = re.sub(r"\(", "", string)
    # string = re.sub(r"\)", "", string)
    # string = re.sub(r"\?", "", string)
    string = re.sub(r"'", "", string)
    string = re.sub(r"\`", "", string) 
    string = re.sub(r"\,", "", string)
    string = re.sub(r"\“", "", string)
    string = re.sub(r"\:", "", string)
    string = re.sub(r"\.", "", string)
    # string = re.sub(r"[^A-Za-z]", " ", string)
    # string = re.sub(r"[0-9]\w+|[0-9]","", string)
    # string = re.sub(r"\s{2,}", " ", string)
    return string.strip().lower()

def kgrams(text, k=5):
    n_grams = ngrams(text, k)
    return [''.join(grams) for grams in n_grams]



def extract_ngrams(text, num):
    n_grams = ngrams(nltk.word_tokenize(text), num)
    return [ ' '.join(grams) for grams in n_grams]

def kmp(origin="text ori", referer="text ref", gram=5, mode=1):
    origin = clean_full(origin)
    referer = clean_full(referer)

    if mode == 2:
        tmp_origin = re.sub(r"[\s]", "", origin)
        tmp_referer = re.sub(r"[\s]", "", referer)
        ref_name = kgrams(list(referer), gram)
        origin_name = kgrams(list(origin), gram)
    elif mode == 1:
        origin_name = extract_ngrams(origin, gram)
        ref_name = extract_ngrams(referer, gram)
    else:
        raise Exception("Invalid Mode")
    
    # print(origin_name)

    doc = []
    for i in origin_name:
        if i in ref_name:
            doc.append(i)
    
    kmp = {'origin': '', 'referer':''}
    kmp['origin'] = origin
    kmp['referer'] = referer
    # print(doc)
    for fa in doc:
        print(fa, " 1 ")
        kmp['origin'] = re.sub("({})".format(fa),"<strong style='color: #F08080;'><i>{}</i></strong>".format(fa), origin)
        kmp['referer'] = re.sub("({})".format(fa),"<strong style='color: #F08080;'><i>{}</i></strong>".format(fa), referer)
        origin = kmp['origin']
        referer = kmp['referer']

    # print(kmp)
    return kmp

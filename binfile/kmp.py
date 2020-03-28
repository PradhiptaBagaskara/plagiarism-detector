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

def kmp(origin="text ori", referer="text ref", gram=5):
    origin = clean_full(origin)
    referer = clean_full(referer)

    # tfidf_origin = TfidfVectorizer( ngram_range=(gram, gram))
    # tfidf_ref = TfidfVectorizer(ngram_range=(gram, gram))

    # kmp_origin= tfidf_origin.fit_transform([origin])
    # kmp_referer = tfidf_ref.fit_transform([referer])

    # origin_name = tfidf_origin.get_feature_names()
    # ref_name = tfidf_ref.get_feature_names()

    # word = sent_tokenize(origin)
    origin_name = free_kmp(origin)
    ref_name = free_kmp(referer)
    


    doc = []
    for i in origin_name:
        if i in ref_name:
            doc.append(i)
    
    # print(doc)
    kmp = {'origin': '', 'referer':''}
    import re
    # print(doc)
    for fa in doc:
    # teks = teks
        # print(fa, " 1 ")
        kmp['origin'] = re.sub("({})".format(fa),"<strong style='background-color: #F08080;'><i> {} </i></strong>".format(fa), origin)
        kmp['referer'] = re.sub("({})".format(fa),"<strong style='background-color: #F08080;'><i> {} </i></strong>".format(fa), referer)
    # print(kmp)
    return kmp

def free_kmp(text):
    word = word_tokenize(text)
    # print(word)

    dd = []
    k = 5
    panjang = len(word)
    leng = panjang
    for d in range(panjang - k):

        if panjang < k:
            break
        else:
            pj = leng - panjang
            dowo = pj + k
            panjang = panjang - k
        
        b = []
        b.clear()
        # print(pj, dowo)
        for i in range(pj, dowo):
            # print(word[i])
            if word[i] not in b:
                b.append(word[i])
                
        dd.append(' '.join(b))

    # print(dd)
    return dd
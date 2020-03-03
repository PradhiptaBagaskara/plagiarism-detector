from .winnowing_ngram import winnow as nwinnow
from .winnowing_wordgram import winnow as wwinnow
from .distance_measurement import *

def check(origin, referer, gram, winnow_mode):
    if (winnow_mode == 1):
        t_origin = wwinnow(origin, gram)
        t_referer = wwinnow(referer, gram)
    elif (winnow_mode == 2):
        t_origin = nwinnow(origin, gram)
        t_referer = nwinnow(referer, gram)

    euc = euclidean_similarity(t_origin, t_referer)
    manh = manhattan_similarity(t_origin, t_referer)
    cosi = round(cosine_similarity(t_origin, t_referer) * 100, 2)
    jacc = round(jaccard_similarity(t_origin, t_referer) * 100, 2)
    dice = round(dice_similarity(t_origin, t_referer) * 100, 2)
    mink = minkowski_similarity(t_origin, t_referer, 3)
    weig = weighted_euclidean_similarity(t_origin, t_referer, 3)
    return '''
    <h6>Euclidean : {0}</h6>
    <h6>Manhattan : {1}</h6>
    <h6>Cosine : {2}</h6>
    <h6>Jaccard : {3}</h6>
    <h6>Dice : {4}</h6>
    <h6>Minkowski : {5}</h6>
    <h6>Weighted : {6}</h6>
    '''.format(euc, manh, cosi, jacc, dice, mink, weig)



from sklearn.metrics.pairwise import euclidean_distances, manhattan_distances
from sklearn.preprocessing import normalize
from scipy.spatial import distance

from .winnowing_ngram import winnow as nwinnow
from .winnowing_wordgram import winnow as wwinnow
from .distance_measurement import *
import json
import numpy as np
import array as arr
from .rabin import rabin_word
from .kmp import kmp as kmp_cek



def checks(origin='origin', referer='referer', gram=5, winnow_mode=1, debug=False, plag=1):
    # print(type(debug))
    # print(debug)
    if (winnow_mode == 1):
        if plag == 1:
            d_origin = wwinnow(origin, gram, debug)
            d_referer = wwinnow(referer, gram, debug)
            rabin_word(referer, gram,debug)
        else:
            d_origin = rabin_word(origin, gram, debug)
            d_referer = rabin_word(referer, gram, debug)
    elif (winnow_mode == 2):
        if plag == 1:
            d_origin = nwinnow(origin, gram, debug)
            d_referer = nwinnow(referer, gram, debug)
        else:
            d_origin = rabin_word(origin, gram, debug, 2)
            d_referer = rabin_word(referer, gram, debug, 2)

    t_origin = d_origin['data']
    t_referer = d_referer['data']

    kmp = kmp_cek(origin,referer,gram,winnow_mode)
    # for i in  t_origin:
    #     if i in t_referer:
    #         print("sama: ",i) 


  

    mins = np.min((*t_origin, *t_referer))
    maxs = np.max((*t_origin, *t_referer))
    deflen = 0

    # print(euclidean_distance(t_origin, t_referer))
    if (len(t_origin)>len(t_referer)):
        n_origin = t_origin
        deflen = len(n_origin)
        n_referer = t_referer + [0 for i in range(abs(len(t_origin)-len(t_referer)))]
        # t_origin = t_origin[:len(t_referer)]
    elif (len(t_origin)<len(t_referer)):
        n_referer = t_referer
        deflen = len(n_referer)
        n_origin = t_origin + [0 for i in range(abs(len(t_origin)-len(t_referer)))]
    else:
        n_referer = t_referer
        n_origin = t_origin
        deflen = len(n_referer)
    # print(euclidean_distance(t_origin, t_referer))

    matrix = [[],[]]
    matrix[0] = normalize(np.asarray([n_origin], dtype=np.float), norm="l2", axis=1)
    matrix[1] = normalize(np.asarray([n_referer], dtype=np.float), norm="l2", axis=1)
    matrix[0] = matrix[0][0]
    matrix[1] = matrix[1][0]
    # print(matrix)

    mat = np.array([matrix[0], [a for a in range(deflen)], matrix[1]]).T
    mcov = np.cov(mat)
    icov = np.linalg.inv(mcov)
    # print(t_origin)

    cosine = round(cosine_sim(n_origin, n_referer) * 100, 2)
    jaccard = round(jaccard_similarity(n_origin, n_referer) * 100, 2)
    dice = round(dice_similarity(n_origin, n_referer) * 100, 2)

    euclidean = euclidean_distance(matrix[0], matrix[1])
    manhattan = manhattan_distance(matrix[0], matrix[1])

    
    minkowski = minkowski_distance(matrix[0], matrix[1], 3)
    weighted = weighted_euclidean_distance(matrix[0], matrix[1], 2)
    mahalanobis = distance.mahalanobis(matrix[0], matrix[1], icov)

    result = {
        'origin' : d_origin,
        'referer' : d_referer,
        'kmp' : kmp,
        'measures' : {
            'cosine' : cosine,
            'jaccard' : jaccard,
            'dice' : dice,
            'euclidean' : round(1/(1+euclidean) * 100, 2),
            'manhattan' : round(1/(1+manhattan) * 100, 2),
            'minkowski' : round(1/(1+minkowski) * 100, 2),
            'weighted' : round(1/(1+weighted) * 100, 2),
            'mahalanobis' : round(1/(1+mahalanobis) * 100, 2),
        }
    }
    return result




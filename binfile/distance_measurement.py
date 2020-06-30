import numpy as np
from math import *


def cosine_similarity(a, b):
    # numerator = sum(a*b for a,b in zip(x,y))
    # denominator = square_rooted(x) * square_rooted(y)
    return dot(a, b) / ((dot(a, a) ** .5) * (dot(b, b) ** .5))
    # return round(numerator/float(denominator),3)


def dot(A, B):
    return (sum(a * b for a, b in zip(A, B)))


def cosine_sim(x, y):
    l1 = []
    l2 = []

    X_set = set(x)
    Y_set = set(y)
    # form a set containing keywords of both strings  
    rvector = X_set.union(Y_set)

    for w in rvector:
        l1.append(1) if w in X_set else l1.append(0)  # create a vector
        l2.append(1) if w in Y_set else l2.append(0)

        # cosine formula
    cs = sum(w1 * w2 for w1, w2 in zip(l1, l2))

    cosine = cs / float((sum(l1) * sum(l2)) ** 0.5)
    # print("similarity: ", cosine)
    return cosine


def jaccard_similarity(x, y):
    intersection_cardinality = len(set.intersection(*[set(x), set(y)]))
    union_cardinality = len(set.union(*[set(x), set(y)]))
    return intersection_cardinality / float(union_cardinality)


def dice_similarity(x, y):
    len_x = len(set(x))
    len_y = len(set(y))
    intersection_cardinality = len(set.intersection(*[set(x), set(y)]))
    return (2.0 * intersection_cardinality) / (len_x + len_y)


def euclidean_distance(x, y):
    return sqrt(sum([(a - b) ** 2 for a, b in zip(x, y)]))


def weighted_euclidean_distance(x, y, w):
    return sqrt(sum((1 if a <= 0 else w) * (pow(a - b, 2)) for a, b in zip(x, y)))


def manhattan_distance(x, y):
    return sum(abs(a - b) for a, b in zip(x, y))


def square_rooted(x):
    return round(sqrt(sum([a * a for a in x])), 3)


def nth_root(value, n_root):
    root_value = 1 / float(n_root)
    return round(value ** root_value, 3)


def minkowski_distance(x, y, p_value):
    return nth_root(sum(pow(abs(a - b), p_value) for a, b in zip(x, y)), p_value)


def mahalanobis_distance(x, y):
    x, y = trim_to_min(x, y)
    ax = np.array(x)
    ay = np.array(y)
    delta = ax - ay

    mat = np.array([x, y]).T
    mcov = np.cov(mat)
    try:
        icov = np.linalg.inv(mcov)
    except np.linalg.LinAlgError:
        icov = None

    if icov is not None:
        m = np.dot(np.dot(delta, icov), delta)
        return np.sqrt(m) if m >= 0 else np.sqrt(abs(m))

    return 0.0
    # X = np.vstack([x, y])
    # V = np.cov(X.T)
    # print(V)
    # return 0.0
    # VI = np.linalg.inv(V)
    # print(np.diag(np.sqrt(np.dot(np.dot((x - y), VI), (x - y).T))))


def weighted_euclidean_distances(X, w):
    from itertools import combinations
    res = []

    for xx, yy in combinations(X, 2):
        res.append(weighted_euclidean_distance(xx, yy, w))

    for xx in X:
        res.append(weighted_euclidean_distance(xx, xx, w))

    return res


def trim_to_min(text1 = [], text2 = []):
    text1 = list(set(text1))
    text2 = list(set(text2))

    if len(text1) > len(text2):
        text1 = text1[:len(text2)]
    elif len(text1) < len(text2):
        text2 = text2[:len(text1)]

    return text1, text2
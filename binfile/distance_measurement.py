import numpy as np
from math import *
from decimal import Decimal
 
def euclidean_distance(x,y):
    return sqrt(sum([(a-b)**2 for a, b in zip(x, y)]))

def euclidean_similarity(x,y):
    dist = 1/(1+euclidean_distance(x,y))
    return dist if dist == 1 else dist * 100000
    return '{:.10f}'.format(dist*100)

def weighted_euclidean_distance(x,y, w):
    return sqrt(sum(w*(pow(a-b,2)) for a, b in zip(x, y)))

def weighted_euclidean_similarity(x, y, w):
    dist = 1/(1+weighted_euclidean_distance(x,y, w))
    return dist if dist == 1 else dist * 100000
    return '{:.10f}'.format(dist*100)

def manhattan_distance(x,y):
    return sum(abs(a-b) for a,b in zip(x,y))

def manhattan_similarity(x,y):
    dist = 1/(1+manhattan_distance(x,y))
    return dist if dist == 1 else dist * 100000
    return '{:.10f}'.format(dist*100)

def square_rooted(x):
    return round(sqrt(sum([a*a for a in x])),3)
 
def cosine_similarity(x,y):
    numerator = sum(a*b for a,b in zip(x,y))
    denominator = square_rooted(x) * square_rooted(y)
    return round(numerator/float(denominator),3)

def jaccard_similarity(x,y):
    intersection_cardinality = len(set.intersection(*[set(map(lambda x1: x1, x)), set(map(lambda y1: y1, y))]))
    union_cardinality = len(set.union(*[set(map(lambda x1: x1, x)), set(map(lambda y1: y1, y))]))
    return intersection_cardinality/float(union_cardinality)

def dice_similarity(x,y):
    len_x = len(x)
    len_y = len(y)
    intersection_cardinality = len(set.intersection(*[set(map(lambda x1: x1, x)), set(map(lambda y1: y1, y))]))
    return (2.0*intersection_cardinality)/(len_x+len_y)


def nth_root(value, n_root):
    root_value = 1/float(n_root)
    return round (Decimal(value) ** Decimal(root_value),3)
 
def minkowski_distance(x,y,p_value):
    return nth_root(sum(pow(abs(a-b),p_value) for a,b in zip(x, y)),p_value)

def minkowski_similarity(x, y, z):
    dist = minkowski_distance(x,y,z)
    return dist 
    return '{:.10f}'.format(dist*100)

def mahalanobis_disctance(x, y):

  ax = np.array(*[set(map(lambda x1:x1, x))])
  ay = np.array(*[set(map(lambda y1:y1, y))])
  a_substract = np.subtract(ax, ay)
  print(a_substract)
  try:
    inv = np.linalg.inv(a_substract)
  except np.linalg.LinAlgError:
    pass

  # return a_substract

  return np.matmul(np.matmul(a_substract.transpose(), inv), a_substract)
  

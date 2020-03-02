import numpy as np
from math import *
 
def euclidean_distance(x,y):
    return sqrt(sum(pow(a[1]-b[1],2) for a, b in zip(x, y)))

def weighted_euclidean_distance(x,y):
    return sqrt(sum(2*(pow(a[1]-b[1],2)) for a, b in zip(x, y)))

def manhattan_distance(x,y):
    return sum(abs(a[1]-b[1]) for a,b in zip(x,y))

def square_rooted(x):
    return round(sqrt(sum([a[1]*a[1] for a in x])),3)

def square_rooted_(x):
    return round(sqrt(sum([a*a for a in x])),3)
 
def cosine_similarity(x,y):
    numerator = sum(a[1]*b[1] for a,b in zip(x,y))
    print(square_rooted(x))
    denominator = square_rooted(x) * square_rooted(y)
    print(square_rooted(x))
    return round(numerator/float(denominator),3)

def cosine_similarity_(x,y):
    numerator = sum(a*b for a,b in zip(x,y))
    denominator = square_rooted_(x)*square_rooted_(y)
    return round(numerator/float(denominator),3)

def jaccard_similarity(x,y):
    intersection_cardinality = len(set.intersection(*[set(map(lambda x1: x1[1], x)), set(map(lambda y1: y1[1], y))]))
    union_cardinality = len(set.union(*[set(map(lambda x1: x1[1], x)), set(map(lambda y1: y1[1], y))]))
    return intersection_cardinality/float(union_cardinality)

def dice_similarity(x,y):
    intersection_cardinality = len(set.intersection(*[set(map(lambda x1: x1[1], x)), set(map(lambda y1: y1[1], y))]))
    union_cardinality = len(set.union(*[set(map(lambda x1: x1[1], x)), set(map(lambda y1: y1[1], y))]))
    len_x = len(x)
    len_y = len(y)
    return (2*intersection_cardinality)/float(len_x+len_y)

# Minkowski Distance implementation
#
# See: http://en.wikipedia.org/wiki/Minkowski_distance
#
# Returns the Minkowski distance between two vectors.
# 
# - p : first array
# - q : second array
# - n : distance order
#
# => returns: the distance between p and q.

def minkowski_distance(p, q, n):

    #make sure both array are in the same dimension
    # assert len(p) == len(q)  
    # if len(p) > len(q):
    #   p = p[:len(q)-1]
    # elif len(p) < len(q):
    #   q = q[:len(p)-1]
    # print(len(p))
    # print(len(q))

    return sum([abs(x[1]-y[1])**n for x,y in zip(p,q)])**1/n

def minkowski_distance_procedural(p, q, n):

    #make sure both array are in the same dimension
    # assert len(p) == len(q)  
    # if len(p) > len(q):
    #   p = p[:len(q)-1]
    # elif len(p) < len(q):
    #   q = q[:len(p)-1]
    # print(len(p))
    # print(len(q))

    s = 0  
    for x,y in zip(p,q):
        s += abs(x[1]-y[1])**n
    return s**(1 / n)

def mahalanobis_disctance(x, y):

  ax = np.array(*[set(map(lambda x1:x1[1], x))])
  ay = np.array(*[set(map(lambda y1:y1[1], y))])
  a_substract = np.subtract(ax, ay)
  print(a_substract)
  try:
    inv = np.linalg.inv(a_substract)
  except np.linalg.LinAlgError:
    pass

  # return a_substract

  return np.matmul(np.matmul(a_substract.transpose(), inv), a_substract)
  

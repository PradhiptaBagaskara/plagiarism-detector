from winnowing import *
import distance_measurement as dm

def hash_md5(text):
    import hashlib
    hs = hashlib.md5(text)
    hs = hs.hexdigest()[-14:]
    hs = int(hs, 16)
    return hs
    
# Override the hash function
# winnow.hash_function = hash_md5

te1 = winnow(u'''
Intermediate developers are more competent than the Junior developer, they start to see the flaws in their old codebase, they gain the knowledge but they get trapped into the next chain i.e. messing things up while trying to do them "the right way" e.g. hasty abstractions, overuse or unnecessary usage of Design Patterns -- they may be able to provide solution faster than the Junior developers but the solution might put you into another rabbit-hole in the long run. Without supervision, they might delay the execution while trying to "do things properly". They don't know yours loreman mana mamam asasaas aasas aa
''', 15)
te2 = winnow(u'''
Have respect for the code that was written before you. Be generous when passing judgment on the architecture or the design decisions made in the codebase. Understand that code is often ugly and weird for a reason other than incompetence. Learning to live with and thrive with legacy code is a great skill. Never assume anybody is stupid. Instead, figure out how these intelligent, well-intentioned and experienced people have come to a decision that is stupid now. Approach inheriting legacy code with an "opportunity mindset" rather than a complaining one
''', 15)

# print(te1)
# from scipy.spatial import distance as pairwise

# print("cos tes: ", pairwise.cosine(te1, te2))
# print(winnow(u'''Ketidakjujuran'''))

print(len(te1))
print(len(te2))

euc = round(dm.euclidean_distance(te1, te2), 2) 
manh = round(dm.manhattan_distance(te1, te2), 2)
cosi = round(dm.cosine_similarity(te1, te2) * 100, 2)
jacc = round(dm.jaccard_similarity(te1, te2) * 100, 2)
dice = round(dm.dice_similarity(te1, te2) * 100, 2)
mink = round(dm.minkowski_distance(te1, te2, 1) * 100, 2)
weig = round(dm.weighted_euclidean_distance(te1, te2), 2)
# maha = mahalanobis_disctance(te1, te2) * 100
 
print('''
Euclidean : {0}\r
Manhattan : {1}\r
Cosine : {2}\r
Jaccard : {3}\r
Dice : {4}\r
Minkowski : {5}\r
Weighted : {6}\r
'''.format(euc, manh, cosi, jacc, dice, mink, weig))

# print('Cosine : {}'.format(cosine_similarity_([143373, 157024, 160782, 55720, 144505, 154769, 165263, 134275, 56954, 158099], [155470, 143615, 159694, 160882, 56808, 156473, 169289, 149291, 134275, 56954, 158099])))
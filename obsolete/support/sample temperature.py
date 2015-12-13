import math

def scale(val, src, dst):
    return ((val - src[0]) / (src[1]-src[0])) * (dst[1]-dst[0]) + dst[0]

_min = 1.7
_max = 3.0
for each in range(-35, 36):
    a = scale(each, (0.0, 35.0), (_min, _max))
    print "%3i" % each, "=", "% 2.4f" % a, "% 3i" % int(scale(math.exp(a), (math.exp(_min), math.exp(_max)), (15, 120)))


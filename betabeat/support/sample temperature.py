import math

def scale(val, src, dst):
    return ((val - src[0]) / (src[1]-src[0])) * (dst[1]-dst[0]) + dst[0]

for each in range(-35, 36):
    a = scale(each, (-35.0, 35.0), (0, 10))
    print "@", each, "'C  interval is ", int(scale(math.exp(a), (math.exp(0), math.exp(10)), (10, 360))), " min"


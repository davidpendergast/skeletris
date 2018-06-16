import math
import random

class Utils:
    
    def sub(v1, v2):
        return (v1[0] - v2[0], v1[1] - v2[1])
        
    def mult(v, a):
        return (a*v[0], a*v[1])
        
    def set_length(v, length):
        mag = math.sqrt(v[0]*v[0] + v[1]*v[1])
        if mag == 0:
            return Utils.rand_vec(length)
        else:
            return Utils.mult(v, length / mag)
            
    def mag(v):
        return math.sqrt(v[0]*v[0] + v[1]*v[1])
            
    def rand_vec(length=1):
        angle = 6.2832 * random.random()
        return [length*math.cos(angle), length*math.sin(angle)]
        

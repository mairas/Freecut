#!/usr/bin/env python

import numpy
import pylab
import copy

class Item(object):
    def __init__(self,l,w,x=None,y=None):
        self.l = l
        self.w = w
        self.x = x
        self.y = y

    def __eq__(self,other):
        return self.l==other.l and self.w==other.w and self.x==other.x and self.y==other.y
    
    def __ne__(self,other):
        return not self.__eq__(other)

    def value(self):
        return self.l*self.w

    def overlaps(self,other):
        p1x1 = self.x
        p1x2 = self.x+self.l
        p1y1 = self.y
        p1y2 = self.y+self.w
        
        p2x1 = other.x
        p2x2 = other.x+other.l
        p2y1 = other.y
        p2y2 = other.y+other.w
        
        return ((p1x1<=p2x1 and p1x2>p2x1) or \
                (p1x2>=p2x2 and p1x1<p2x2)) and \
                ((p1y1<=p2y1 and p1y2>p2y1) or \
                     (p1y2>=p2y2 and p1y1<p2y2))

    def rotate(self,b):
        if b==False:
            l = max(self.w,self.l)
            w = min(self.w,self.l)
        else:
            w = max(self.w,self.l)
            l = min(self.w,self.l)
        self.w = w
        self.l = l 

    def rect(self,color,text=None):
        rect(self.x,self.y,self.l,self.w,color,text)

def overlap(items):
    for i in range(len(items)):
        for j in range(i+1,len(items)):
            if items[i].overlaps(items[j]):
                return True
    return False
    

class Region(object):
    def __init__(self,l,w,x,y):
        self.l = l
        self.w = w
        self.x = x
        self.y = y
        
    def value(self):
        return self.l*self.w

    def contains(self,items):
        if type(items)!=list:
            items = [items]
        for item in items:
            if not (self.x<=item.x and self.x+self.l>=item.x+item.l and \
               self.y<=item.y and self.y+self.w>=item.y+item.w):
                return False
        return True
    
    def is_valid_layout(self,items):
        # first, the region has to contain all the items
        if not self.contains(items):
            return False
        # second, the items may not overlap
        if overlap(items):
            return False
        return True
    
    def fill(self,pool,S,Vf,Uf,vmax=0,rotated=False):
        for i in range(len(pool)):
            pool[i].rotate(rotated)
            # check if the item actually fits the region
            if pool[i].w>self.w or pool[i].l>self.l:
                continue
            ub = self.value()
            up = Vf + Uf + ub
#            if ub<=vmax or up<S:
#                continue
            item = pool.pop(i)
            items = [item]
            region_A,region_B = self.split(item)
            VfA = Vf+item.value()
            UfA = Uf+region_B.value()
            itemsA,vA = region_A.layout(pool,S,VfA,UfA)
            items = items + itemsA
            # if every item is placed, just return
            if len(pool)==0: return items,item.value()+vA
            ub = item.value()+vA+region_B.value()
#            if ub<=vmax or up<S:
#                pool.insert(i,item)
#                continue
            VfB = Vf+item.value()+vA
            UfB = Uf
            itemsB,vB = region_B.layout(pool,S,VfB,UfB)
            items = items + itemsB
            v = item.value() + vA + vB
#            if v<=vmax:
#                pool.insert(i,item)
#                continue
            vmax = v
            if len(pool)==0 or vmax+Vf==S: return items,vmax
            pool.insert(i,item)
            # TODO: need to try filling region_B first
        # if we have not returned by now, we have failed to fill the region
        items = []
        return items,vmax
            
    def layout(self,pool,S,Vf=0,Uf=0):
        # nothing will fit in zero space
        if self.value()==0:
            return [],0
        # first place the item as-is
        items,vmax = self.fill(pool,S,Vf,Uf,vmax=0,rotated=False)
        if len(pool)!=0:
            # place the item rotated
            items_r,vmax = self.fill(pool,S,Vf,Uf,vmax,rotated=True)
            items = items + items_r
        return items,vmax
        
            
class Block(Region):
    def split(self,item,rotated=False):
        xA = self.x+item.l
        yA = self.y
        lA = self.l-item.l
        wA = item.w
        
        xB = self.x
        yB = self.y+item.w
        lB = self.l
        wB = self.w-item.w
        
        item.x = self.x
        item.y = self.y
        
        return (Block(lA,wA,xA,yA),Block(lB,wB,xB,yB))
        
class Segment(Region):
    def split(self,item,rotated=False):
        xA = self.x
        yA = self.y+item.w
        lA = item.l
        wA = self.w-item.w
        
        xB = self.x+item.l
        yB = self.y
        lB = self.l-item.l
        wB = self.w
        
        item.x = self.x
        item.y = self.y
        
        return (Block(lA,wA,xA,yA),Segment(lB,wB,xB,yB))


def rect(x,y,l,w,c,text=None):
    pylab.plot([x,x,x+l,x+l,x],[y,y+w,y+w,y,y],c)
    if text!=None:
        pylab.text(x+l/2,y+w/2,text)

def plot_layout(items,L,W):
    colors = ['r','g','b','c','m','y']
    if len(items)>0:
        pylab.clf()
        pylab.axes(aspect='equal')
        rect(0,0,L,W,'k')

        for i,item in enumerate(items):
            item.rect(colors[i%len(colors)],str(i))
        pylab.draw()
    
def optimize_HRBB(I,W,alpha):
    # arrange the items in descending order of their areas
    I.sort(reverse=True,key=lambda x: x.w*x.l)
    N = len(I)

    l_max = max([el.l for el in I])
    w_max = max([el.w for el in I])
    Ls = max(l_max,w_max)

    S = sum([el.value() for el in I])

    L0 = int(numpy.ceil(float(S)/W))
    Lmax = int(alpha*L0)

    a = L0
    b = Lmax
    Items = {}
    while b-a>1:
        c = (a+b)/2
        Vs = S-0.1
        print c
        r = Segment(c,W,0,0)
        pool = copy.copy(I)
        items,vmax = r.layout(pool,S)
        Items[c] = copy.deepcopy(items)
        if len(items)<N:
            a = c
        else:
            b = c
    c = b
    print c
    items = Items[c]
    
    if len(items)==N:
        plot_layout(items,c,W)

if __name__=='__main__':
    I=[
       Item(1540,700),
       Item(650,1502),
#       Item(539,419),
#       Item(539,419),
       Item(301,762),
#       Item(138,138),
#       Item(188,62),
#       Item(188,62),
#        Item(650,74),
#        Item(650,74),
#        Item(650,74),
#        Item(650,74),
#        Item(650,74),
#        Item(100,450),
#        Item(1502,74),
#        Item(1502,74),
#        Item(724,100),
#        Item(724,100),
#        Item(724,100),
#        Item(724,100),
#        Item(1540,100),
#        Item(1540,100),
#        Item(83,80),
#        Item(57,57),
#        Item(57,57),
#        Item(57,57),
#        Item(138,100),
#        Item(100,100),
#        Item(100,212),
#        Item(100,212),
       ]

    pylab.ion()
    optimize_HRBB(I,1830,2.0)
    pylab.show()
    
    for item in I:
        print item.w,item.l,item.x,item.y
    

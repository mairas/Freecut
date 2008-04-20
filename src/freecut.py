#!/usr/bin/env python

import numpy
import pylab
import copy

class Item(object):
    def __init__(self,l,w):
        self.l = max(l,w)
        self.w = min(l,w)
        self.x = None
        self.y = None

    def value(self):
        return self.l*self.w

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

class Region(object):
    def __init__(self,l,w,x,y):
        self.l = l
        self.w = w
        self.x = x
        self.y = y
        
    def value(self):
        return self.l*self.w
        
    def fill(self,pool,rotated=False):
        for i in range(len(pool)):
            pool[i].rotate(rotated)
            # check if the item actually fits the region
            if pool[i].w>self.w or pool[i].l>self.l:
                continue
            item = pool.pop(i)
            items = [item]
            region_A,region_B = self.split(item)
            items = items + region_A.layout(pool)
            # if every item is placed, just return
            if len(pool)==0: return items
            items = items + region_B.layout(pool)
            if len(pool)==0: return items
            pool.insert(i,item)
            # TODO: need to try filling region_B first
        # if we have not returned by now, we have failed to fill the region
        items = []
        return items
            
    def layout(self,pool):
        # nothing will fit in zero space
        if self.value()==0:
            return []
        # first place the item as-is
        items = self.fill(pool,rotated=False)
        if len(pool)!=0:
            # place the item rotated
            items_r = self.fill(pool,rotated=True)
            items = items + items_r
            
        return items
        
            
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
    while b-a>1:
        c = (a+b)/2
        Vs = S-0.1
        print c
        r = Segment(c,W,0,0)
        pool = copy.copy(I)
        items = r.layout(pool)
        if len(items)<N:
            a = c
        else:
            b = c
    c = b
    r = Segment(c,W,0,0)
    items = r.layout(I)
    
    if len(items)==N:
        plot_layout(items,c,W)

if __name__=='__main__':
    I=[
       Item(700,1540),
       Item(650,1502),
       Item(539,419),
       Item(539,419),
       Item(301,762),
       Item(138,138),
       Item(188,62),
       Item(188,62),
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
    

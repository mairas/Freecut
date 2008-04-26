#!/usr/bin/env python

import numpy
import pylab
import copy
import sys
#import psyco
#psyco.full()

def overlap(items):
    for i in range(len(items)):
        for j in range(i+1,len(items)):
            if items[i].overlaps(items[j]):
                return True
    return False
    
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
        if b==True:
            l = max(self.w,self.l)
            w = min(self.w,self.l)
        else:
            w = max(self.w,self.l)
            l = min(self.w,self.l)
        self.w = w
        self.l = l 

    def plot_rect(self,color,text=None):
        plot_rect(self.x,self.y,self.l,self.w,color,text)

    def fits(self,region):
        # check if the item actually fits the region
        return self.w<=region.w and self.l<=region.l


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
    
    def fill(self,pool,item,S,Vf,Uf,vmax=0):
        # step 4.2
        regions = self.split(item) 
        regions.sort(lambda x,y: x.value()-y.value())
        for i,r in enumerate(regions):
            ub = item.value()+sum([reg.value() for reg in regions[i:]]) 
            up = Vf + Uf + ub
            #if ub<=vmax or up<S:
            #    return item.value(),False
            Vfr = Vf+vmax+item.value()
            Ufr = Uf+sum([reg.value() for reg in regions[i+1:]])
            vr,success = r.layout(pool,S,Vfr,Ufr)
            v = item.value()+vmax
            #if v<=vmax:
            #    return item.value(),False
            vmax = v
            if success and len(pool)==0: return vmax,True
        # if we have not returned by now, we have failed to fill the region
        return vmax,True
            
    def layout(self,pool,S,Vf=0,Uf=0):
        # nothing to do
        if len(pool)==0:
            return 0,True
        # nothing will fit in zero space
        if self.value()==0:
            return 0,False
        vmax = 0
        i = 0
        while i<len(pool):
            item = pool.pop(i)
            # first try to place the item as-is
            item.rotate(False)
            if item.fits(self):
                vmax,success = self.fill(pool,item,S,Vf,Uf,vmax)
                if success: return vmax,True
            # place the item rotated
            item.rotate(True)
            if item.fits(self):
                vmax,success = self.fill(pool,item,S,Vf,Uf,vmax)
                if success: return vmax,True
            pool.insert(i,item)
            i += 1
        return vmax,False
        
            
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
        
        return [Block(lA,wA,xA,yA),Block(lB,wB,xB,yB)]
    
        
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
        
        return [Block(lA,wA,xA,yA),Segment(lB,wB,xB,yB)]


def plot_rect(x,y,l,w,c,text=None):
    pylab.plot([x,x,x+l,x+l,x],[y,y+w,y+w,y,y],c)
    if text!=None:
        pylab.text(x+l/2, y+w/2,text, fontsize=8, horizontalalignment='center',
         verticalalignment='center',)

def plot_layout(items,L,W,show=False,draw=False):
    colors = ['r','g','b','c','m','y']
    if len(items)>0:
        pylab.clf()
        pylab.axes(aspect='equal')
        plot_rect(0,0,L,W,'k')

        for i,item in enumerate(items):
            item.plot_rect(colors[i%len(colors)],"%d\n%d" % (item.l,item.w))
        if draw:
            pylab.draw()
        if show:
            pylab.show()
    
def optimize_HRBB(I,W,alpha,verbose=False):
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
        if verbose:
            sys.stderr.write("%d\n" % (c,))
        r = Segment(c,W,0,0)
        pool = copy.copy(I)
        vmax,success = r.layout(pool,S)
        items = copy.copy(I)
        for p in pool:
            items.remove(p)
        Items[c] = copy.deepcopy(items)
        if len(pool)>0:
            a = c
            if verbose:
                sys.stderr.write("> ")
        else:
            b = c
            if verbose:
                sys.stderr.write("< ")
    c = b
    if verbose:
        sys.stderr.write("= %d\n" % (c,))
    #items = Items[c]
    
    #if len(items)==N:
    #    plot_layout(items,c,W)
        
    return c,items

if __name__=='__main__':
    I=[
        Item(650,1502),
        Item(1540,700),
        Item(539,419),
        Item(539,419),
        Item(301,762),
        Item(138,138),
        Item(188,62),
        Item(188,62),
        Item(650,74),
        Item(650,74),
        Item(650,74),
        Item(650,74),
        Item(650,74),
        Item(100,450),
        Item(1502,74),
        Item(1502,74),
        Item(724,100),
        Item(724,100),
        Item(724,100),
        Item(724,100),
        Item(1540,100),
        Item(1540,100),
        Item(83,80),
        Item(57,57),
        Item(57,57),
        Item(57,57),
        Item(138,100),
        Item(100,100),
        Item(100,212),
        Item(100,212),
       ]

    #pylab.ion()
    W = 1830
    L,items = optimize_HRBB(I,W,2.0)
    plot_layout(items,L,W,show=True)
    
    for item in I:
        print item.l,item.w,item.x,item.y
    

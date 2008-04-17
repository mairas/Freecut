#!/usr/bin/env python

import numpy
import pylab

class Item(object):
    def __init__(self,w,l):
        self.w = max(w,l)
        self.l = min(w,l)
        self.x = 0
        self.y = 0

    def value(self):
        return self.l*self.w

    def rotate(self,b):
        if b==False:
            w = max(self.w,self.l)
            l = min(self.w,self.l)
        else:
            l = max(self.w,self.l)
            w = min(self.w,self.l)
        self.w = w
        self.l = l 

    def rect(self,color,text=None):
        rect(self.x,self.y,self.l,self.w,color,text)

def rect(x,y,l,w,c,text=None):
    pylab.plot([x,x,x+l,x+l,x],[y,y+w,y+w,y,y],c)
    if text!=None:
        pylab.text(x+l/2,y+w/2,text)

def plot_layout(I,B,L,W):
    colors = ['r','g','b','c','m','y']
    if any(B):
        pylab.clf()
        pylab.axes(aspect='equal')
        rect(0,0,L,W,'k')

        for i,item in enumerate(I):
            if B[i]==True:
                item.rect(colors[i%len(colors)],str(i))
        
    pylab.draw()
    
def F(x,y):
    '''Value function.'''
    return x*y

def LayoutItem(l,w,x,y,Vf,Uf,B,C,kc,I,i,S,vmax,Vs,segment=False):
    # step 4.1
    if I[i].l>l or I[i].w>w:
        return B,C,kc,vmax,Vs
    if kc==0:
        kc = i

    # step 4.2
    I[i].x = x
    I[i].y = y

    si = I[i].value()

    # after i has been placed, divide remaining L-shaped area into A and B
    
    if segment==False:
        xA = x+I[i].l
        yA = I[i].y
        lA = l-I[i].l
        wA = I[i].w
        segA = False
    
        xB = I[i].x
        yB = I[i].y+I[i].w
        lB = l 
        wB = w-I[i].w
        segB = False
    else:
        xA = I[i].x
        yA = I[i].y+I[i].w
        lA = I[i].l
        wA = w-I[i].w
        segA = False

        xB = I[i].x+I[i].l
        yB = 0
        lB = l-I[i].l
        wB = w
        segB = True

    # always fill the smaller region first
    # FIXME: this evokes a bug!
    if lB*wB<lA*wA:
        xA,yA,lA,wA,segA,xB,yB,lB,wB,segB = xB,yB,lB,wB,segB,xA,yA,lA,wA,segA
        
    ub = F(l,w)
    # upper bound for the whole pattern
    up = Vf + Uf + ub

    if ub<=vmax or up<=Vs:
        return B,C,kc,vmax,Vs

    # step 4.3
    
    B[i] = True
    CA = numpy.zeros(len(B),bool)
    VfA = Vf + si
    UfA = Uf+F(lB,wB)
    vA,B,CA = Layout(lA,wA,xA,yA,VfA,UfA,B,CA,kc,I,S,vmax,Vs,segA)

    # step 4.4
    
    ub = si + vA + F(lB,wB)
    up = Vf + Uf + ub

    if not (ub<=vmax or up<=Vs):
        # step 4.5
        B = B+CA
        CB = numpy.zeros(len(B),bool)
        VfB = Vf + si + vA
        UfB = Uf
        vB,B,CB = Layout(lB,wB,xB,yB,VfB,UfB,B,CB,kc,I,S,vmax,Vs,segB)
        v = si + vA + vB
        if v>vmax:
            # step 4.6
            vmax = v
            C = CA + CB
            C[i] = True
            if Vf+vmax>Vs:
                # step 4.7
                Vs = Vf+vmax
                if Vs==S:
                    return B,C,kc,vmax,Vs
        # step 4.8
        B = B-CA
    # step 4.9
    B[i] = False
    return B,C,kc,vmax,Vs

def Layout(l,w,x,y,Vf,Uf,B,C,k,I,S,vmax=0,Vs=0,segment=False):
    '''
    Block layout optimizer.
    
    Arguments:
    l    block length (x-wise dim)
    w    block width (y-wise dim)
    x    block x location
    y    block y location
    Vf   value of items that have already been placed on the plate
    Uf   the upper bound of the unoccupied regions
    B    a boolean array of items in the father pattern
    C    a boolean array of items in the current block
    k    minimum item index
    I    list of all items
    vmax best value of block x y so far
    Vs   (V*) value of the best pattern obtained so far
    Returns:
    value of the found region
    '''
    # step 1
    #pdb.set_trace()
    if F(l,w)==0:
        return 0,B,C
    else:
        vmax = 0
        kc = 0

    # steps 2,3,6
    for i in range(k,len(I)):
        if B[i]==True: continue  # item already placed

        # step 4
        I[i].rotate(False)
        B,C,kc,vmax,Vs = LayoutItem(l,w,x,y,Vf,Uf,B,C,kc,I,i,S,vmax,Vs,segment)
        if Vs==S:
            return vmax,B,C
        # step 4.9
        if vmax!=l*w and B[i]==False and C[i]==False: # two latter conditions missing from the algorithm description
            # step 5
            
            I[i].rotate(True)
            B,C,kc,vmax,Vs = LayoutItem(l,w,x,y,Vf,Uf,B,C,kc,I,i,S,vmax,Vs,segment)
            # if the item was not placed, rotate it back
            if B[i]==False and C[i]==False:
                I[i].rotate(False)
        
            if Vs==S:
                return vmax,B,C
    return vmax,B,C

  

def optimize_HRBB(I,W,alpha):
    # arrange the items in descending order of their areas
    I.sort(reverse=True,key=lambda x: x.w*x.l)

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
        B = numpy.zeros(len(I),bool)
        C = numpy.zeros(len(I),bool)
        Vs = S-0.1
        print c
        V,Bl,Cl = Layout(c,W,0,0,0,0,B,C,0,I,S,0,Vs,True)
        if V<S:
            a = c
        else:
            b = c
    c = b
    # get the optimal layout once more
    B = numpy.zeros(len(I),bool)
    C = numpy.zeros(len(I),bool)
    Vs = S-0.1
    V,Bl,Cl = Layout(c,W,0,0,0,0,B,C,0,I,S,0,Vs,True)
    plot_layout(I,Bl,c,W)

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
        Item(650,74),
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
    optimize_HRBB(I,1830,5.0)
    pylab.show()
    
    for item in I:
        print item.w,item.l,item.x,item.y
    

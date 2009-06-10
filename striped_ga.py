#! /usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import division
import sys
import math
import pygena
import copy
import random
import pickle


class ItemType(object):
    def __init__(self, width, length, text="", rotatable=False):
        self.w = width
        self.l = length
        self.rotatable = rotatable
        self.text = text

    def __repr__(self):
        return "ItemType(%d,%d,'%s')" % (self.w,self.l,self.text)

    # do not make deep copies of the types
    def __deepcopy__(self,memo):
        memo[id(self)] = self
        return self

class Item(tuple):
    def __new__(cls,typ,rotated=False):
        return tuple.__new__(cls,(typ,rotated))

    def rotate(self):
        if self.rotatable:
            l = list(self)
            l[3] = not l[3]
        return type(self)(*l)

    type = property(lambda self: self[0])
    rotated = property(lambda self: self[1])
    
    l = property(lambda self: (self.type.l,self.type.w)[self.rotated])
    w = property(lambda self: (self.type.w,self.type.l)[self.rotated])
    text = property(lambda self: self.type.text)
    rotatable = property(lambda self: self.type.rotatable)

    def area(self):
        return self.w*self.l

    def covered_area(self):
        return self.area()


class Strip(list):
    """
    Strip is a horizontal or vertical line of items and other strips.
    """

    def area(self):
        return self.l * self.w
        
    def covered_area(self):
        A = 0
        for item in self:
            A += item.covered_area()
        return A
    
    def fillrate(self):
        return self.covered_area() / self.area()
   
    def populate(self,items):
        for e in self[::-1]:
            if type(e)!=Item:
                e.populate(items)
        if items:
            for e in items[:]:
                if e.w<self.W and e.l<self.L:
                    self.place(items,e)
                else:
                    e.rotate()
                    if e.w<self.W and e.l<self.L:
                        self.place(items,e)

    def update_dimensions(self,W,L,recurse=True):
        """Update the subitem dimensions."""
        W0 = W
        L0 = L
        w = 0
        l = 0
        for e in self:
            if type(e)==Item:
                w,l = self.dim_inc(w,l,e.w,e.l)
            else:
                if recurse:
                    ew,el = e.update_dimensions(W,L)
                else:
                    # trust that the subitem dimensions are correct
                    ew,el = e.w,e.l
                w,l = self.dim_inc(w,l,ew,el)
            W = W0-w
            L = L0-l

        self.w = w
        self.l = l
        self.W = W
        self.L = L

        return w,l


class HStrip(Strip):
    "A horizontal strip of items and other strips"

    def dim_inc(self,w,l,ew,el):
        """Increase current strip dimensions according to the element size."""
        w = max(w,ew)
        l = l+el
        return w,l


    def place(self,items,item):
        self.append(item)
        items.remove(item)
        W0 = self.W + self.w
        L0 = self.L + self.l
        self.w = max(self.w,item.w)
        self.l = self.l+item.l
        self.W = W0 - self.w
        self.L = L0 - self.l


    
    def repair(self):
        """Repair the layout

        Drop any items not fitting in the layout.
        Recurse depth first, then loop through the strips
        in reverse order, dropping any items that don't fit in
        the layout. Also drop empty substrips and merge substrips
        with the same orientation."""

        dropped = []

        for i in range (len(self)-1,-1,-1):
            e = self[i]
            if type(e)!=Item:
                dropped += e.repair()
                if len(e)==0:
                    # remove empty strips
                    self.pop(i)
                # merge substrips with same orientation
                elif type(e)==HStrip:
                    self[i:i+1] = self[i]
                    # no need to update dimensions
            else:
                if self.L<0 or (self.W<0 and self.w==e.w):
                    d = self.pop(i)
                    dropped.append(d)
                    if self.w==d.w:
                        self.update_dimensions(self.W+self.w,
                                               self.L+self.l,
                                               recurse=False)
                    else:
                        self.L += d.l
                        self.l -= d.l
        return dropped

class VStrip(Strip):
    "A vertical strip of items and other strips"
    
    def dim_inc(self,w,l,ew,el):
        """Increase current strip dimensions according to the element size."""
        w = w+ew
        l = max(l,el)
        return w,l

    def place(self,items,item):
        self.append(item)
        items.remove(item)
        W0 = self.W + self.w
        L0 = self.L + self.l
        self.l = max(self.l,item.l)
        self.w = self.w+item.w
        self.W = W0 - self.w
        self.L = L0 - self.l

    def repair(self):
        """Repair the layout

        Drop any items not fitting in the layout.
        Recurse depth first, then loop through the strips
        in reverse order, dropping any items that don't fit in
        the layout. Also drop empty substrips and merge substrips
        with the same orientation."""

        dropped = []

        for i in range (len(self)-1,-1,-1):
            e = self[i]
            if type(e)!=Item:
                dropped += e.repair()
                if len(e)==0:
                    # remove empty strips
                    self.pop(i)
                # merge substrips with same orientation
                elif type(e)==VStrip:
                    self[i:i+1] = self[i]
                    # no need to update dimensions
            else:
                if self.W<0 or (self.L<0 and self.l==e.l):
                    d = self.pop(i)
                    dropped.append(d)
                    if self.l==d.l:
                        self.update_dimensions(self.W+self.w,
                                               self.L+self.l,
                                               recurse=False)
                    else:
                        self.W += d.w
                        self.w -= d.w
        return dropped



class StripChromosome(pygena.BaseChromosome):
    items = []
    W = 0
    L = 0
    random_order = False
    item_min_dim = 0
    optimization = pygena.MINIMIZE
    def __init__(self):
        pygena.BaseChromosome.__init__(self)
        self.items = copy.deepcopy(StripChromosome.items)
        self.strip = None
        self.randomize()
        self.repair()
        
    def _random_rotate_items(self):
        for item in self.items:
            if item.rotatable and random.randint(0,1):
                item.rotate()  

    def randomize(self):
        self.strip = HStrip()
        for i in range(len(self.items)):
            self.strip.append(VStrip())
        self.strip.update_dimensions()
        #self._random_rotate_items()
        if self.random_order:
            random.shuffle(self.items)
        self.strip.populate(self.items)
        # force changes in the chromosome
        #self.mutate(100.0)

    def crossover(self,other):
        """
        perform crossover operation on two region trees.
        return two copies after the operation without repairing them.
        """

        valid = False

        self.items = self.region.get_items()
        other.items = other.region.get_items()
        while not valid:
        
            # get crossover points
            c1 = random.randint(0,len(self.items)-1)
            c2 = random.randint(0,len(other.items)-1)
        
            # crossover needs to be performed on copied objects
            sc = copy.deepcopy(self)
            oc = copy.deepcopy(other)
            #sc = self
            #oc = other

            reg_1 = sc.region.find(sc.items[c1])
            reg_2 = oc.region.find(oc.items[c2])
        
            # swap the object contents
            reg_2.__dict__, reg_2.__class__, \
                reg_1.__dict__, reg_1.__class__ = \
                reg_1.__dict__, reg_1.__class__, \
                reg_2.__dict__, reg_2.__class__

            if not isinstance(sc.region,Block) \
                    and not isinstance(oc.region,Block):
                valid = True

        # repair the offspring
        sc.repair()
        oc.repair()
        
        # return the object copies
        return (sc,oc)
        
    def mutate(self,mutation_rate):
        mutated = False
        items = self.region.get_items()
        for item in items:
            if random.random() < mutation_rate/len(items):
                r2 = random.random()
                if r2 < 1./3:
                    self.region.find(item).transpose()
                elif r2 < 2./3 and item.rotatable:
                    item.rotate()
                else:
                    self.region.find(item).drop_item()
                mutated = True
        if mutated:
            self.repair()

    def repair(self):
        self.region.fix_layout(self.items,self.W,self.L,self.item_min_dim)
        #print self.region.num_items(),len(self.items)
        assert(self.region.num_items()==len(self.items)) # must have all items in the layout
        self.evaluate()

    def evaluate(self):
        self.score = self.region.l/self.region.fillrate()
        #self.score = self.region.l

    def asString(self):
        return 'items=%d, w=%d, l=%d, fillrate=%f' % (self.region.num_items(), self.region.w, self.region.l, self.region.fillrate())
        

def optimize(items,W,generations=30,verbose=False,randomize=False):
    items.sort(key=lambda x: x.area(), reverse=True)
    RegionChromosome.items = items
    RegionChromosome.W = W
    RegionChromosome.L = 1e6 # any large value should do
    RegionChromosome.optimization = pygena.MINIMIZE
    RegionChromosome.random_order = randomize

    RegionChromosome.item_min_dim = \
        min([i.w for i in items]+[i.l for i in items])
    
    env = pygena.Population(RegionChromosome, maxgenerations=generations,
                            optimum=0,
                            tournament=pygena.roulette_tournament,
                            size=100,
                            crossover_rate=0.7, mutation_rate=0.2)
    best = env.run()
    #best.region.sort()
    pickle.dump(best,open("segmented_ga.pickle","w"))
    best.region.calculate_item_coordinates()
    output_items = best.region.get_items()

    print "output_items:", len(output_items)

    #best.region.dump()
    
    return best.region.l,output_items

#! /usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import division
import sys
import math
import itertools
import weakref
import pygena
import copy
import random
import pickle

def indent(s, numSpaces):
    s = s.split("\n")
    s = [(numSpaces * ' ') + line for line in s]
    s = "\n".join(s)
    return s

class ItemType(object):
    instances = weakref.WeakValueDictionary()
    def __new__(cls,*args,**kw):
        a = args + tuple(kw.items())
        if a in cls.instances:
            return cls.instances[a]
        else:
            newcls = super(ItemType,cls).__new__(cls)
            cls.instances[a] = newcls
            return newcls

    def __init__(self, width, height, text="", rotatable=True):
        if hasattr(self,'h'): return
        self.h = height
        self.w = width
        self.rotatable = rotatable
        self.text = text

    def __str__(self):
        return "IT(id%d,w%s,h%s,r%s,txt'%s')" % \
            (id(self),self.w,self.h,('F','T')[self.rotatable],self.text)

    def __repr__(self):
        return "ItemType(%d,%d,'%s',%s)" % \
                (self.w,self.h,self.text,self.rotatable)

    # do not make deep copies of the types
    def __deepcopy__(self,memo):
        memo[id(self)] = self
        return self

class Item(object):
    def __init__(self,type_,rotated=False,x=None,y=None,id_=None):
        self.type = type_
        self.rotated = rotated
        # create a unique identifier for later matching of duplicates
        if id_ is not None:
            self.id = id_
        else:
            self.id = id(self)
        self.x = x
        self.y = y

    def __str__(self):
        return "I(id%d,w%s,h%s,x%s,y%s,r%s,t%s,txt'%s')" % \
                (self.id,self.w,self.h,self.x,self.y, \
                 ('F','T')[self.rotated],id(self.type),self.text)

    def __repr__(self):
        return "Item(%r,rotated=%r,x=%r,y=%r)" % \
                (self.type,self.rotated,self.x,self.y)

    def rotate(self):
        self.rotated = not self.rotated

    w = property(lambda self: (self.type.w,self.type.h)[self.rotated])
    h = property(lambda self: (self.type.h,self.type.w)[self.rotated])
    text = property(lambda self: self.type.text)
    rotatable = property(lambda self: self.type.rotatable)

    def area(self):
        return self.h*self.w

    def covered_area(self):
        return self.area()

    def fillrate(self):
        return 1

    def fill_score(self):
        return 0

    def get_items(self):
        return [self]

    def overlaps(self,other):
        """
        Return true if the items overlap
        """

        x_min = max(self.x,other.x)
        y_min = max(self.y,other.y)
        x_max = min(self.x+self.w,other.x+other.w)
        y_max = min(self.y+self.h,other.y+other.h)

        return x_min<x_max and y_min<y_max



class Strip(list):
    """
    Strip is a horizontal or vertical line of items and other strips.
    """

    min_item_height = 0
    min_item_width = 0

    def __init__(self,w=None,h=None,W=None,H=None,x=None,y=None,list_=[]):
        super(Strip,self).__init__()
        self.w = w
        self.h = h
        self.W = W
        self.H = H
        self.x = x
        self.y = y
        self += list_

    def __repr__(self):
        r = [repr(p) for p in self]
        s = ",\n".join(r)
        s_i = "[\n" + indent(s,2) + "\n]"
        return "%s(%r,%r,%r,%r,%r,%r,%s)" % \
                (type(self).__name__,self.w,self.h,self.W,self.H,self.x,self.y,s_i)


    def area(self):
        return self.w * self.h
        
    def available_area(self):
        return self.W * self.H

    def covered_area(self):
        A = 0
        for item in self:
            A += item.covered_area()
        return A
    
    def fillrate(self):
        return self.covered_area() / self.area()

    def fill_score(self):
        score = self.available_area()/self.covered_area()-1
        for item in self:
            score += item.fill_score()
        return score

    def get_items(self):
        items = []
        for item in self:
            if isinstance(item,Item):
                items.append(item)
            else:
                # another strip
                items += item.get_items()
        return items


    def get_strips(self):
        """Recursively get substrips of a strip."""
        strips = []
        for item in self:
            if not isinstance(item,Item):
                strips += item.get_strips()
        strips.append(self)
        return strips


    def sort_recursive(self):
        "recursively sort the subitems according to item breadth"
        # first sort substrips
        for s in [s for s in self if isinstance(s,Strip)]:
            s.sort_recursive()
        # then sort the current strip
        #self.sort(key=lambda s: -s.covered_area()/len(s.get_items()))
        self.sort(key=lambda s:
                  -self.breadth(s))


    def fits(self,item):
        """
        Test if the item fits the strip

        Return true if the item actually fits the strip.
        """
        f = item.x+item.w<=self.x+self.W and item.y+item.h<=self.y+self.H
        return f

    def populate(self,items):
        """
        place all items in the strip

        removes elements from the items list
        """

        for item in items[:]:
        #    self.find_place(items,item)
            strip,rotated = self.find_best_place(item)
            if rotated:
                item.rotate()
            strip.place(items,item)


    def find_place(self,items,item):
        """
        find a place for an item (depth-first)
        """
        for strip_item in self:
            if isinstance(strip_item,Strip):
                strip_item.find_place(items,item)
        if item in items:
            # item not yet placed
            av_width,av_height = self.get_available_space()
            if item.h<=av_height and item.w<=av_width:
                self.place(items,item)
            elif item.type.rotatable:
                item.rotate()
                if item.h<=av_height and item.w<=av_width:
                    self.place(items,item)


    def place(self,items,item):
        s = self.ortho()
        s.append(item)
        self.append(s)
        items.remove(item)
        self.update_dimensions(self.W,self.H)

    def find_best_place(self,item):
        """
        find a place for an item with the smallest fill_score increase
        """
        strips = self.get_strips()
        best_score = 1e308
        best_pos = ()
        for strip in strips:
            av_width,av_height = strip.get_available_space()
            if item.h<=av_height and item.w<=av_width:
                strip.append(item)
                score = strip.fill_score()
                strip.pop()
                if score<best_score:
                    best_score = score
                    best_pos = (strip,False)
            # also try rotated
            if item.w<=av_height and item.h<=av_width:
                item.rotate()
                strip.append(item)
                score = strip.fill_score()
                strip.pop()
                if score<best_score:
                    best_score = score
                    best_pos = (strip,True)
                # rotate the item to its original orientation
                item.rotate()
        return best_pos

    def remove_duplicates(self,seen):
        """
        Remove duplicate items from the layout.

        Returns the amount of items removed.
        """
        num_removed = 0
        for i in range(len(self)-1,-1,-1):
            item = self[i]
            if isinstance(item,Item):
                if item.id in seen:
                    self.pop(i)
                    num_removed += 1
                else:
                    seen[item.id] = True
            else:
                num_removed += item.remove_duplicates(seen)
        
        return num_removed
   

    def fix_layout(self,items,W,H):
        """
        Fix the layout after crossover and mutation operations.
        """
        def pdebug(self,s):
            if 0:
                print s,"-"*20
                print repr(self)
        pdebug(self,"here 1")
        nd = self.remove_duplicates({})
        self.update_dimensions(W,H)

        pdebug(self,"here 2")
        nr = self.repair()

        self.update_dimensions(W,H)

        pdebug(self,"here 3")
        # get a list of unplaced items

        unplaced = {}
        for e in items[:]: unplaced[e.id] = e
        placed = self.get_items()
        for p in placed:
            try: del unplaced[p.id]
            except: pass
        unplaced = unplaced.values()
        random.shuffle(unplaced)
         
        self.populate(unplaced)

        self.update_dimensions(W,H,check=True)

        self.sort_recursive()

        self.update_dimensions(W,H,check=True)

        pdebug(self,"here 4")

        assert(len(unplaced)==0)

        if self.h>H or self.w>W:
            print "dims after fix_layout:",self.w,self.h,self.W,self.H

        assert(self.h<=H)
        assert(self.w<=W)

    def update_dimensions(self,W,H,check=False):
        self.update_sizes(W,H,check=check)
        self.update_available_space(W,H)

    def update_sizes(self,W,H,check=False,x=0,y=0):
        """Update the minimum sizes required to accommodate each subitem."""
        h = 0
        w = 0

        self.x = x
        self.y = y

        for item in self:
            if isinstance(item,Item):
                w,h = self.dim_inc(w,h,item.w,item.h)
                item.x = x
                item.y = y
            else:
                ew,eh = item.update_sizes(W,H,check=check,x=x,y=y)
                w,h = self.dim_inc(w,h,ew,eh)

            x,y = self.update_sizes_inc_coord(x,y,item)

        self.h = h
        self.w = w

        if check:
            assert(self.w+self.x<=W)
            assert(self.h+self.y<=H)

        return w,h

    def repair_strip(self,i,item):
        """
        Perform specific repair operations on a substrip.
        """
        if len(item)==0:
            # remove empty strips
            self.pop(i)
        # merge substrips with same orientation
        elif isinstance(item,type(self)):
            self[i:i+1] = self[i]
            # no need to update dimensions
        # unwrap substrips
        elif isinstance(item,self.ortho) and \
             len(item)==1 and \
            isinstance(item[0],type(self)):
            self[i:i+1] = item[0]

    def repair(self):
        """
        Repair the layout

        Drop any items not fitting in the layout.
        Recurse depth first, then loop through the strips
        in reverse order, dropping any items that don't fit in
        the layout. Also drop empty substrips and merge substrips
        with the same orientation.
        """
        dropped = []

        for i in range(len(self)-1,-1,-1):
            item = self[i]
            if isinstance(item,Strip):
                dropped += item.repair()
                self.repair_strip(i,item)
            else:
                if not self.fits(item):
                    d = self.pop(i)
                    dropped.append(d)
                elif self.breadth(item)<self.B:
                    # only wrap items if their breadth is less than
                    # the available breadth
                    s = self.ortho()
                    s.append(item)
                    self[i] = s
        return dropped



class HStrip(Strip):
    "A horizontal strip of items and other strips"

    def __init__(self,*args,**kw):
        self.ortho = VStrip
        super(HStrip,self).__init__(*args,**kw)

    def __str__(self):
        return "H(%s,%s,%s,%s)" % (self.w,self.h,self.W,self.H)

    def length(self):
        return self.w

    def breadth(self,s):
        return s.h

    L = property(lambda self: self.W)
    B = property(lambda self: self.H)

    def dim_inc(self,w,h,ew,eh):
        """Increase current strip dimensions according to the element size."""
        h = max(h,eh)
        w = w+ew
        return w,h

    def get_available_space(self):
        av_width = self.W-self.w
        av_height = self.H
        return av_width,av_height

    def update_available_space(self,W,H):
        """
        Update the space available for the strip
        """
        self.W = W
        self.H = H

        for item in self:
            w = min(item.w,W)
            W -= w
            if isinstance(item,Strip):
                item.update_available_space(w,H)

    def update_sizes_inc_coord(self,x,y,item):
        x = x+item.w
        return x,y

    def populate_inc_dims(self,item,dw,dh):
        self.w += dw
        self.h = max(self.h,item.h)

class VStrip(Strip):
    "A vertical strip of items and other strips"
    
    def __init__(self,*args,**kw):
        self.ortho = HStrip
        super(VStrip,self).__init__(*args,**kw)

    def __str__(self):
        return "V(%s,%s,%s,%s)" % (self.w,self.h,self.W,self.H)

    def length(self):
        return self.h

    def breadth(self,s):
        return s.w

    L = property(lambda self: self.H)
    B = property(lambda self: self.W)

    def dim_inc(self,w,h,ew,eh):
        """Increase current strip dimensions according to the element size."""
        h = h+eh
        w = max(w,ew)
        return w,h

    def get_available_space(self):
        av_width = self.W
        av_height = self.H-self.h
        return av_width,av_height

    def update_available_space(self,W,H):
        """
        Update the space available for the strip
        """
        self.W = W
        self.H = H

        for item in self:
            h = min(item.h,H)
            H -= h
            if isinstance(item,Strip):
                item.update_available_space(W,h)

    def update_sizes_inc_coord(self,x,y,item):
        y = y+item.h
        return x,y

    def populate_inc_dims(self,item,dw,dh):
        self.h += dh
        self.w = max(self.w,item.w)




class StripChromosome(pygena.BaseChromosome):
    items = []
    H = 0
    W = 0
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
        items = self.items[:]
        # TODO: randomize between HStrip and VStrip
        self.strip = HStrip()
        self.strip.update_dimensions(self.W,self.H)
        #self._random_rotate_items()
        if self.random_order:
            random.shuffle(items)
        self.strip.populate(items)
        self.strip.update_dimensions(self.W,self.H)
        self.strip.sort_recursive()
        # force changes in the chromosome
        #self.mutate(100.0)

    def crossover(self,other):
        """
        perform crossover operation on two strip trees.
        return two copies after the operation without repairing them.
        """

        valid = False

        sc = copy.deepcopy(self)
        oc = copy.deepcopy(other)

        sc_strips = sc.strip.get_strips()
        oc_strips = oc.strip.get_strips()

        c1 = random.randint(0,len(sc_strips)-1)
        c2 = random.randint(0,len(oc_strips)-1)

        c1i = random.randint(0,len(sc_strips[c1]))
        c2i = random.randint(0,len(oc_strips[c2]))

        sc_strips[c1][c1i:], oc_strips[c2][c2i:] = \
                oc_strips[c2][c2i:], sc_strips[c1][c1i:]

        # repair the offspring
        sc.repair()
        oc.repair()
        
        # return the object copies
        return (sc,oc)
        
    def mutate(self,mutation_rate):
        mutated = False
        items = self.strip.get_items()
        strips = self.strip.get_strips()
        for item in items:
            if random.random() < mutation_rate/len(items):
                r2 = random.random()
                #if r2 < 1./3:
                #    self.strip.find(item).transpose()
                if r2 < 0.5 and item.rotatable:
                    item.rotate()
                else:
                    # drop the item
                    for s in strips:
                        if item in s:
                            s.remove(item)
                            break
                mutated = True
        if mutated:
            self.repair()

    def repair(self):
        self.strip.fix_layout(self.items,self.W,self.H)
        # must have all items in the layout
        assert(len(self.strip.get_items())==len(self.items)) 
        self.evaluate()

    def evaluate(self):
        #self.score = self.strip.w/math.sqrt(self.strip.fillrate())
        self.score = self.strip.w + self.strip.fill_score()/self.strip.w

    def asString(self):
        return 'w=%s, h=%s, fill_score=%s' % \
                (self.strip.w,
                 self.strip.h, self.strip.fill_score())


def optimize(items,H,generations=200,plateau=20,pop_size=100,verbose=False,randomize=False):
    items.sort(key=lambda x: x.area(), reverse=True)
    StripChromosome.items = items
    StripChromosome.H = H
    StripChromosome.W = 1e6 # any large value should do
    StripChromosome.optimization = pygena.MINIMIZE
    StripChromosome.random_order = randomize

    StripChromosome.item_min_dim = \
        min([i.h for i in items]+[i.w for i in items])
    
    env = pygena.Population(StripChromosome, maxgenerations=generations,
                            maxplateau=plateau,
                            optimum=0,
                            tournament=pygena.roulette_tournament,
                            size=pop_size,
                            crossover_rate=0.7, mutation_rate=0.3)
    best = env.run()
    best.strip.update_dimensions(StripChromosome.W,StripChromosome.H)
    pickle.dump(best,open("striped_ga.pickle","w"))
    output_items = best.strip.get_items()

    print "output_items:", len(output_items)

    #best.strip.dump()
    
    return best.strip.w,output_items

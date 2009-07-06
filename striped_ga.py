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
        return "ItemType(%d,%d,'%s')" % (self.l,self.w,self.text)

    # do not make deep copies of the types
    def __deepcopy__(self,memo):
        memo[id(self)] = self
        return self

class Item(object):
    def __init__(self,type_,rotated=False):
        self.type = type_
        self.rotated = rotated
	    # create a unique identifier for later matching of duplicates
        self.id = id(self)

    def dump(self,indent=""):
        print indent+str(self)

    def rotate(self):
        self.rotated = not self.rotated

    l = property(lambda self: (self.type.l,self.type.w)[self.rotated])
    w = property(lambda self: (self.type.w,self.type.l)[self.rotated])
    text = property(lambda self: self.type.text)
    rotatable = property(lambda self: self.type.rotatable)

    def area(self):
        return self.w*self.l

    def covered_area(self):
        return self.area()

    def update_locations(self,x,y):
        self.x = x
        self.y = y

    def __repr__(self):
        return "Item(type_=%r,rotated=%s)" % (self.type,('False','True')[self.rotated])
    
    def __str__(self):
        return "Item (%d,%d,%s) of type %r" % (self.l,self.w,('F','T')[self.rotated],self.type)



class Strip(list):
    """
    Strip is a horizontal or vertical line of items and other strips.
    """

    min_item_width = 0
    min_item_length = 0

    # note: this is a class method!
    def update_item_min_dims(self,items):
        Strip.min_item_width = 1e308
        Strip.min_item_length = 1e308
        for item in items:
            Strip.min_item_width = min(Strip.min_item_width,item.w)
            Strip.min_item_length = min(Strip.min_item_length,item.l)
            if not item.rotatable:
                Strip.min_item_length = min(Strip.min_item_width,item.w)
                Strip.min_item_width = min(Strip.min_item_length,item.l)

    def area(self):
        return self.l * self.w
        

    def covered_area(self):
        A = 0
        for item in self:
            A += item.covered_area()
        return A
    

    def fillrate(self):
        return self.covered_area() / self.area()


    def get_items(self):
        items = []
        for item in self:
            if isinstance(item,Item):
                items.append(item)
            else:
                items += item.get_items()
        return items


    def get_strips(self):
        strips = [self]
        for item in self:
            if not isinstance(item,Item):
                strips += item.get_strips()
        return strips

    def sort_recursive(self):
        for item in self:
            if isinstance(item,Strip):
                item.sort_recursive()
        self.sort(key=lambda x: (-(x.area()-x.covered_area()),-x.covered_area()))

    def update_sizes(self,recurse=True):
        """Update the minimum sizes required to accommodate each subitem."""
        w = 0
        l = 0
        for item in self:
            if isinstance(item,Item):
                w,l = self.dim_inc(w,l,item.w,item.l)
            else:
                # FIXME
                #if recurse:
                ew,el = item.update_sizes()
                #else:
                #    ew,el = item.w,item.l
                w,l = self.dim_inc(w,l,ew,el)
        self.w = w
        self.l = l

        return w,l


    def update_dimensions(self,W=None,L=None):
        self.update_sizes()
        self.update_available_space(W,L)


    def remove_duplicates(self,seen):
        """
        Remove duplicate items from the layout.

        Returns the amount of items removed.
        """
        num_removed = 0
        # print "seen: ", sorted(seen.keys())
        for i in range(len(self)-1,-1,-1):
            item = self[i]
            if isinstance(item,Item):
                if seen.has_key(item.id):
                    #print "dropped in remove_duplicates:", item.id
                    self.pop(i)
                    num_removed += 1
                else:
                    seen[item.id] = True
            else:
                num_removed += item.remove_duplicates(seen)
        
        return num_removed
   

    def fix_layout(self,items,W,L):
        """
        Fix the layout after crossover and mutation operations.
        """
        # FIXME: this is currently terribly complex and convoluted
        nd = self.remove_duplicates({})
        self.update_dimensions(W,L)
        nr = self.repair()
        self.update_dimensions(W,L)

        # get a dict of unplaced items

        unplaced = {}
        for e in items[:]:
            unplaced[e.id] = e
        placed = self.get_items()
        for p in placed:
            try: del unplaced[p.id]
            except: pass
        unplaced = unplaced.values()

        self.populate(unplaced)
        assert(len(unplaced)==0)

        self.update_dimensions(W,L)
        nr = self.repair()
        self.update_dimensions(W,L)
        # TODO: no items should ever be removed here
        assert(len(nr)==0)

        if self.w>W or self.l>L:
            print "dims after fix_layout:",self.l,self.w,self.L,self.W,L,W

        assert(self.w<=W)
        assert(self.l<=L)

        self.sort_recursive()


    def populate(self,items):
        """Populate a strip with items, depth-first."""
        restart = True
        while restart:
            restart = False

            # at this point, always update the item dimensions before a
            # populating attempt
            self.update_dimensions()

            for item in self:
                if isinstance(item,Strip):
                    num_items_before = len(items)
                    item.populate(items)
                    if len(items)<num_items_before:
                        self.update_dimensions()
            
            for item in items[:]:
                av_width,av_length = self.available_dimensions()
                if item.w<av_width and item.l<av_length:
                    self.place(items,item,av_width,av_length)
                    restart = True
                    break
                else:
                    item.rotate()
                    if item.w<av_width and item.l<av_length:
                        self.place(items,item,av_width,av_length)
                        restart = True
                        break


class HStrip(Strip):
    "A horizontal strip of items and other strips"

    def __init__(self):
        self.ortho = VStrip
        self.w = None
        self.l = None
        self.W = None
        self.L = None
        super(HStrip,self).__init__(self)

    def __repr__(self):
        return "H["+", ".join([repr(s) for s in self])+"]"

    def dump(self,indent=""):
        print indent + "H(",self.l,self.w,self.L,self.W,")["
        new_indent = indent + " "
        for item in self:
            item.dump(new_indent)
        print indent + "]"

    def dim_inc(self,w,l,ew,el):
        """Increase current strip dimensions according to the element size."""
        w = max(w,ew)
        l = l+el
        return w,l

    def place(self,items,item,av_width,av_length):
        if av_width>self.min_item_width:
            s = VStrip()
            s.append(item)
            self.append(s)
        else:
            self.append(item)
        items.remove(item)
        self.w = max(self.w,item.w)
        self.l = self.l+item.l

    def available_dimensions(self):
        return (self.W,self.L-self.l)

    def update_available_space(self,W=None,L=None):
        """
        Update the space available for the item.
        W: available width.
        L: available length.
        """
        if W is not None and L is not None:
            self.W = W
            self.L = L
        else:
            W = self.W
            L = self.L
        for i,item in enumerate(self):
            if i < len(self)-1:
                # not the last item
                if isinstance(item,Strip):
                    item.update_available_space(W,min(L,item.l))
                L = max(L-item.l,0)
            else:
                if isinstance(item,Strip):
                    item.update_available_space(W,L)

    def update_locations(self,x,y):
        """
        Update the strip subitem locations.
        """
        self.x = x
        self.y = y

        for item in self:
            item.update_locations(x,y)
            x += item.l

    def tidy_strip(self,i,item):
        """
        Perform specific cleanup operations on a substrip.
        """
        if len(item)==0:
            # remove empty strips
            self.pop(i)
        # merge substrips with same orientation
        elif isinstance(item,HStrip):
            self[i:i+1] = self[i]
            # no need to update dimensions
        # unwrap items
        elif isinstance(item,VStrip) and \
             len(item)==1 and \
             isinstance(item[0],Item) and \
             item[0].l+self.min_item_length >= item.L:
            self[i] = item[0]
        # unwrap substrips
        elif isinstance(item,VStrip) and \
             len(item)==1 and \
            isinstance(item[0],HStrip):
            self[i:i+1] = item[0]


    def repair(self):
        """Repair the layout

        Drop any items not fitting in the layout.
        Recurse depth first, then loop through the strips
        in reverse order, dropping any items that don't fit in
        the layout. Also drop empty substrips and merge substrips
        with the same orientation."""

        dropped = []

        for i in range(len(self)-1,-1,-1):
            item = self[i]
            if isinstance(item,Strip):
                dropped += item.repair()
                self.tidy_strip(i,item)
            else:
                # dealing with Item instance
                # guard for nasty floating point comparison errors
                if self.L+1e-9<self.l or self.W+1e-9<item.w:
                    d = self.pop(i)
                    dropped.append(d)
                    if self.w==d.w:
                        self.update_sizes(recurse=False)
                    else:
                        self.l -= d.l
                else:
                    # wrap small items
                    if item.w+self.min_item_width<=self.W:
                        s = VStrip()
                        s.append(item)
                        self[i] = s
        return dropped

class VStrip(Strip):
    "A vertical strip of items and other strips"
    
    def __init__(self):
        self.ortho = HStrip
        self.w = None
        self.l = None
        self.W = None
        self.L = None
        super(VStrip,self).__init__(self)

    def __repr__(self):
        return "V["+", ".join([repr(s) for s in self])+"]"

    def dump(self,indent=""):
        print indent + "V(",self.l,self.w,self.L,self.W,")["
        new_indent = indent + " "
        for item in self:
            item.dump(new_indent)
        print indent + "]"

    def dim_inc(self,w,l,ew,el):
        """Increase current strip dimensions according to the element size."""
        w = w+ew
        l = max(l,el)
        return w,l

    def place(self,items,item,av_width,av_length):
        if av_length>self.min_item_length:
            s = HStrip()
            s.append(item)
            self.append(s)
        else:
            self.append(item)
        items.remove(item)
        self.l = max(self.l,item.l)
        self.w = self.w+item.w

    def available_dimensions(self):
        return (self.W-self.w,self.L)


    def update_available_space(self,W,L):
        """
        Update the space available for the item.
        W: available width.
        L: available length.
        """
        if W is not None and L is not None:
            self.W = W
            self.L = L
        else:
            W = self.W
            L = self.L
        for i,item in enumerate(self):
            if i < len(self)-1:
                # not the last item
                if isinstance(item,Strip):
                    item.update_available_space(min(W,item.w),L)
                W = max(W-item.w,0)
            else:
                if isinstance(item,Strip):
                    item.update_available_space(W,L)

    def update_locations(self,x,y):
        """
        Update the strip subitem locations.
        """
        self.x = x
        self.y = y

        for item in self:
            item.update_locations(x,y)
            y += item.w

    def tidy_strip(self,i,item):
        """
        Perform specific cleanup operations on a substrip.
        """
        if len(item)==0:
            # remove empty strips
            self.pop(i)
        # merge substrips with same orientation
        elif isinstance(item,VStrip):
            self[i:i+1] = self[i]
            # no need to update dimensions
        # unwrap items
        elif isinstance(item,Strip) and \
             len(item)==1 and \
             isinstance(item[0],Item) and \
             item[0].l+self.min_item_length >= item.L:
            self[i] = item[0]
        # unwrap substrips
        elif isinstance(item,HStrip) and \
             len(item)==1 and \
            isinstance(item[0],VStrip):
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
                self.tidy_strip(i,item)
            else:
                # dealing with Item instance
                # guard for nasty floating point comparison errors
                if self.W+1e-9<self.w or self.L+1e-9<item.l:
                    d = self.pop(i)
                    dropped.append(d)
                    if self.l==d.l:
                        self.update_sizes(recurse=False)
                    else:
                        self.w -= d.w
                else:
                    # wrap small items
                    if item.l+self.min_item_length<=self.L:
                        s = HStrip()
                        s.append(item)
                        self[i] = s
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
        items = self.items[:]
        # TODO: randomize between HStrip and VStrip
        self.strip = HStrip()
        self.strip.update_dimensions(self.W,self.L)
        #self._random_rotate_items()
        if self.random_order:
            random.shuffle(items)
        self.strip.populate(items)
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
        self.strip.fix_layout(copy.deepcopy(self.items),self.W,self.L)
        # must have all items in the layout
        assert(len(self.strip.get_items())==len(self.items)) 
        self.evaluate()

    def evaluate(self):
        self.score = self.strip.l/self.strip.fillrate()
        #self.score = self.strip.l

    def asString(self):
        return 'items=%d, w=%d, l=%d, fillrate=%f' % \
                (len(self.strip.get_items()), self.strip.w,
                 self.strip.l, self.strip.fillrate())


def optimize(items,W,generations=30,verbose=False,randomize=False):
    items.sort(key=lambda x: x.area(), reverse=True)
    Strip().update_item_min_dims(items)
    StripChromosome.items = items
    StripChromosome.W = W
    StripChromosome.L = 1e6 # any large value should do
    StripChromosome.optimization = pygena.MINIMIZE
    StripChromosome.random_order = randomize

    StripChromosome.item_min_dim = \
        min([i.w for i in items]+[i.l for i in items])
    
    env = pygena.Population(StripChromosome, maxgenerations=generations,
                            optimum=0,
                            tournament=pygena.roulette_tournament,
                            size=100,
                            crossover_rate=0.7, mutation_rate=0.2)
    best = env.run()
    #best.strip.sort()
    pickle.dump(best,open("striped_ga.pickle","w"))
    best.strip.update_locations(0,0)
    output_items = best.strip.get_items()

    print "output_items:", len(output_items)

    best.strip.dump()
    
    return best.strip.l,output_items

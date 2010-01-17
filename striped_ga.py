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
    def __init__(self, height, length, text="", rotatable=False):
        self.h = height
        self.w = length
        self.rotatable = rotatable
        self.text = text

    def __repr__(self):
        return "ItemType(%d,%d,'%s')" % (self.w,self.h,self.text)

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
        self.x = -1
        self.y = -1

    def dump(self,indent=""):
        print indent+str(self)

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

    def update_strip_space(self,H,W):
        """
        Nothing to update for an Item
        """
        return H,W

    def overlaps(self,other):
        """
        Return true if the items overlap
        """

        x_min = max(self.x,other.x)
        y_min = max(self.y,other.y)
        x_max = min(self.x+self.w,other.x+other.w)
        y_max = min(self.y+self.h,other.y+other.h)

        return x_min<x_max and y_min<y_max

    def __str__(self):
        return "I(id%d,w%s,h%s,x%s,y%s,r%s,t%s,txt'%s')" % \
                (self.id,self.w,self.h,self.x,self.y,('F','T')[self.rotated],id(self.type),self.text)



class Strip(list):
    """
    Strip is a horizontal or vertical line of items and other strips.
    """

    min_item_height = 0
    min_item_width = 0

    # note: this is a class method!
    def update_item_min_dims(self,items):
        """Find out the dimensions of the smallest items.
        Unallocated dimensions smaller than those found can be
        ignored in the future."""
        Strip.min_item_height = 1e308
        Strip.min_item_width = 1e308
        for item in items:
            Strip.min_item_height = min(Strip.min_item_height,item.h)
            Strip.min_item_width = min(Strip.min_item_width,item.w)
            if not item.rotatable:
                Strip.min_item_width = min(Strip.min_item_height,item.h)
                Strip.min_item_height = min(Strip.min_item_width,item.w)

    def area(self):
        return self.w * self.h
        

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
                # another strip
                items += item.get_items()
        return items


    def get_strips(self):
        """Recursively get substrips of a strip."""
        strips = [self]
        for item in self:
            if not isinstance(item,Item):
                strips += item.get_strips()
        return strips

    def fits(self,item):
        """
        Test if the item fits the strip

        Return true if the item actually fits the strip.
        """
        f = item.x+item.w<=self.x+self.W and item.y+item.h<=self.y+self.H
        if self.W<=0 or self.H<=0:
            print "should not fit:",item.x,item.y,item.w,item.h,self.W,self.H,f
        # if not f:
        #     print "no fit:",item.x,item.l,self.x,self.W,item.y,item.w,self.y,self.H
        return f


    def populate(self,items):
        # first populate substrips
        for item in self:
            if not isinstance(item,Item):
                item.populate(items)
        for item in items[:]:
            # available width and height
            av_height = self.H-self.h
            av_width = self.W-self.w
            if item.h<av_height and item.w<av_width:
                self.place(items,item,av_height,av_width)
            elif item.type.rotatable:
                item.rotate()
                if item.h<av_height and item.w<av_width:
                    self.place(items,item,av_height,av_width)

    def place(self,items,item,av_height,av_width):
        if av_width>self.min_item_width:
            s = self.ortho()
            s.append(item)
            self.append(s)
        else:
            self.append(item)
        items.remove(item)
        self.h,self.w = self.dim_inc(self.h,self.w,item.h,item.w)

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
   

    def fix_layout(self,items,H,W):
        """
        Fix the layout after crossover and mutation operations.
        """
        print "here 1: # items:", len(self.get_items())
        self.update_dimensions(H,W)
        self.dump()
        print "here 2: # items:", len(self.get_items())
        nr = self.repair()
        self.update_dimensions(H,W)
        print "here 3: # items:", len(self.get_items())
        nd = self.remove_duplicates({})
        self.update_dimensions(H,W)
        print "here 4: # items:", len(self.get_items())

        # get a dict of unplaced items

        unplaced = {}
        for e in items[:]:
            unplaced[e.id] = e
        placed = self.get_items()
        for p in placed:
            try: del unplaced[p.id]
            except: pass
        unplaced = unplaced.values()
         
        self.update_dimensions(H,W)
        print "here 5: # items:", len(self.get_items())
        nr = self.repair()
        print "here 6: # items:", len(self.get_items())
        self.update_dimensions(H,W)
        print "here 7: # items:", len(self.get_items())
        self.populate(unplaced)
        print "here 8: # items:", len(self.get_items())

        self.update_dimensions(H,W)
        print "here 9: # items:", len(self.get_items())

        self.dump()

        assert(len(unplaced)==0)

        self.update_dimensions(H,W)

        if self.h>H or self.w>W:
            print "dims after fix_layout:",self.h,self.w,self.H,self.W,H,W

        assert(self.h<=H)
        assert(self.w<=W)

    def update_dimensions(self,H,W):
        self.update_sizes()
        self.update_available_space(H,W)
        pairs = self.check_for_overlap()
        if pairs:
            print "Overlapping pairs:"
            for p in pairs:
                print p
            self.dump()
            assert(0)

    def update_sizes(self,x=0,y=0):
        """Update the minimum sizes required to accommodate each subitem."""
        h = 0
        w = 0

        self.x = x
        self.y = y

        for item in self:
            if isinstance(item,Item):
                h,w = self.dim_inc(h,w,item.h,item.w)
                item.x = x
                item.y = y
            else:
                eh,ew = item.update_sizes(x,y)
                h,w = self.dim_inc(h,w,eh,ew)

            x,y = self.inc_coord(x,y,item)

        self.h = h
        self.w = w

        return h,w

    def update_available_space(self,H,W):
        """
        Update the space available for the item.
        H: available width.
        W: available length.
        """
        self.H = H
        self.W = W
        for i,item in enumerate(self):
            if i < len(self)-1:
                # not the last item
                H,W = item.update_strip_space(H,W)
                if H<item.h or W<item.w:
                    print "W, H:",W,H
            else:
                # last item
                if not isinstance(item,Item):
                    item.update_available_space(H,W)

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
        # unwrap items
        elif isinstance(item,self.ortho) and \
             len(item)==1 and \
             isinstance(item[0],Item) and \
             not item.is_wrappable(item[0]):
            self[i] = item[0]
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
            if not isinstance(item,Item):
                dropped += item.repair()
                self.repair_strip(i,item)
            else:
                print "repair, seen:",item,self.W,self.H
                if not self.fits(item):
                    print "dropping item",item,"from", type(self)
                    d = self.pop(i)
                    dropped.append(d)
                    #if self.same_width(d):
                    #    self.update_sizes()
                    #else:
                    #    self.reduce_length(d)
                else:
                    # wrap small items
                    if self.is_wrappable(item):
                        s = self.ortho()
                        s.append(item)
                        self[i] = s
        return dropped


    def check_for_overlap(self):
        """
        check whether any items in the strip overlap
        """

        pairs = []

        items = self.get_items()

        for i in range(0,len(items)-1):
            item1 = items[i]
            for j in range(i+1,len(items)):
                item2 = items[j]
                if item1.overlaps(item2):
                    pairs.append((item1,item2))

        return pairs


class HStrip(Strip):
    "A horizontal strip of items and other strips"

    def __init__(self):
        self.ortho = VStrip
        super(HStrip,self).__init__(self)

    def __repr__(self):
        return "H["+", ".join([repr(s) for s in self])+"]"

    def dump(self,indent=""):
        print indent + "H(%d,%d,%d,%d)[" % (self.w,self.h,self.W,self.H)
        new_indent = indent + " "
        for item in self:
            item.dump(new_indent)
        print indent + "]"

    def dim_inc(self,h,w,eh,ew):
        """Increase current strip dimensions according to the element size."""
        h = max(h,eh)
        w = w+ew
        return h,w


    def update_strip_space(self,H,W):
        """
        Update available strip space in an orientation-specific manner
        """
        self.update_available_space(H,self.w)
        W -= self.w
        return H,W

    def is_wrappable(self,item):
        return item.h+self.min_item_height<=self.H

    def inc_coord(self,x,y,item):
        x = x+item.w
        return x,y


class VStrip(Strip):
    "A vertical strip of items and other strips"
    
    def __init__(self):
        self.ortho = HStrip
        super(VStrip,self).__init__(self)

    def __repr__(self):
        return "V["+", ".join([repr(s) for s in self])+"]"

    def dump(self,indent=""):
        print indent + "V(%d,%d,%d,%d)[" % (self.w,self.h,self.W,self.H)
        new_indent = indent + " "
        for item in self:
            item.dump(new_indent)
        print indent + "]"

    def dim_inc(self,h,w,eh,ew):
        """Increase current strip dimensions according to the element size."""
        h = h+eh
        w = max(w,ew)
        return h,w

    def update_strip_space(self,H,W):
        """
        Update available strip space in an orientation-specific manner
        """
        self.update_available_space(self.h,W)
        H -= self.h
        return H,W

    def is_wrappable(self,item):
        return item.w+self.min_item_width<=self.W

    def inc_coord(self,x,y,item):
        y = y+item.h
        return x,y




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
        self.strip.update_dimensions(self.H,self.W)
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
        #print "repair: items in strip before fix:",len(self.strip.get_items())
        self.strip.fix_layout(self.items,self.H,self.W)
        # must have all items in the layout
        #print "repair: items in strip after fix:",len(self.strip.get_items())
        #print "repair: items total:",len(self.items)
        if len(self.strip.get_items())!=len(self.items):
            print "Danger, Will Robinson!"
            self.strip.dump()
        assert(len(self.strip.get_items())==len(self.items)) 
        self.evaluate()

    def evaluate(self):
        self.score = self.strip.w/self.strip.fillrate()
        #self.score = self.strip.l

    def asString(self):
        return 'items=%d, h=%d, w=%d, fillrate=%f' % \
                (len(self.strip.get_items()), self.strip.h,
                 self.strip.w, self.strip.fillrate())


def optimize(items,H,generations=30,verbose=False,randomize=False):
    items.sort(key=lambda x: x.area(), reverse=True)
    Strip().update_item_min_dims(items)
    StripChromosome.items = items
    StripChromosome.H = H
    StripChromosome.W = 1e6 # any large value should do
    StripChromosome.optimization = pygena.MINIMIZE
    StripChromosome.random_order = randomize

    StripChromosome.item_min_dim = \
        min([i.h for i in items]+[i.w for i in items])
    
    env = pygena.Population(StripChromosome, maxgenerations=generations,
                            optimum=0,
                            tournament=pygena.roulette_tournament,
                            size=100,
                            crossover_rate=0.7, mutation_rate=0.2)
    best = env.run()
    #best.strip.sort()
    pickle.dump(best,open("striped_ga.pickle","w"))
    output_items = best.strip.get_items()

    print "output_items:", len(output_items)

    #best.strip.dump()
    
    return best.strip.w,output_items

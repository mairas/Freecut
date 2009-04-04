#! /usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import division
import sys
import math
import pygena
import copy
import random


class ItemType(object):
    def __init__(self, width, length, description="", rotatable=False):
        self.w = width
        self.l = length
        self.rotatable = rotatable
        self.description = description

    def __repr__(self):
        return "ItemType(%d,%d,'%s')" % (self.w,self.l,self.description)


class Item(object):
    def __init__(self,type_,rotated=False):
        self.type = type_
        self.rotated = rotated
        # location within the region tree
        self.location = None
        self.x = None
        self.y = None
	# create a unique identifier for later matching of duplicates
	self.id = id(self)

    def rotate(self):
        self.rotated = not self.rotated

    l = property(lambda self: (self.type.l,self.type.w)[self.rotated])
    w = property(lambda self: (self.type.w,self.type.l)[self.rotated])

    def area(self):
        return self.w*self.l

    def __repr__(self):
        return "Item(type_=%r,rotated=%d)" % (self.type,self.rotated)
    
    def __str__(self):
        return "Item (%d,%d,%s) of type %r" % (self.w,self.l,('F','T')[self.rotated],self.type)

    
class Region(object):
    """
    Region is any rectangular area on a plane.
    A Region may contain an item, in which case the remaining area is divided
    into two subregions.
    """
    def __init__(self,w,l):
        self.w = w
        self.l = l
        self.item = None
        self.regions = []

    def _walk_regions(self,d):
        if self.item:
            # make sure that the item knows its location
            self.item.location = self

            d[self.item] = True
        for r in self.regions:
            r._walk_regions(d)
        
    def get_items(self):
        d = {}
        self._walk_regions(d)
        return d.keys()
        
    def dump(self,indent=""):
        print indent + str(self)
        indent = indent + "  "
        if self.item:
            print indent + str(self.item)
        for sr in self.regions:
            sr.dump(indent)
        
    def area(self):
        return self.l * self.w

    def num_items(self):
        n = 0
        if self.item:
            n += 1
        for r in self.regions:
            n += r.num_items()
        return n

    
    def covered_area(self):
        A = 0
        if self.item:
            A += self.item.w * self.item.l
        for r in self.regions:
            A += r.covered_area()

        return A

    def fillrate(self):
        return self.covered_area() / self.area()

    
    def fits(self,item):
	return (item.w<=self.w and item.l<=self.l)

    def populate(self,items,item_min_dim=0):
	"""
	Populate a region using a list of items.
	Take a list of items and fill the region with items.
	No optimization is performed.
	Returns a list of items not fitted to the region.
	"""

	# only place the item if the region is empty
	if self.item == None and not self.regions:
	    for item in items:
		if self.fits(item):
		    self.split(item)
		    items.remove(item)
		    break
	if items:
            regs = [r for r in self.regions \
                           if r.w>=item_min_dim and r.l>=item_min_dim]
	    for sr in regs:
		items = sr.populate(items,item_min_dim)
		if not items: break

	return items

    def clear_region(self):
	self.item = None
	self.regions = []

    def verify_item_size(self,w,l):
	"""
	Verify that that item will fit the region and if not,
	remove the item.
	"""
        if self.item:
            if self.item.l>l or self.item.w>w:
                self.drop_item()
                return False
        return True

    def fix_layout(self,items,w,l,item_min_dim=0):
	"""
	Fix the layout after crossover and mutation operations.
	"""
	# FIXME: it's a bit silly to first fill the layout with duplicates
	#   	 and then remove them again... Should first remove the genuine
	#	 duplicates and get a list of placed items

	nr = self.repair(w,l)
        self.expand(w,l)
	unplaced = self.populate(items[:],item_min_dim)
        assert(len(unplaced)==0) # every piece should fit now
	self.remove_duplicates({})
        nr = self.repair(w,l)

    def remove_duplicates(self,seen):
        """
        Remove duplicate items from the layout.

        Returns the amount of items removed.
        """
        num_removed = 0
        if self.item:
            if seen.has_key(self.item.id):
                self.drop_item()
                num_removed += 1
            else:
                seen[self.item.id] = True
	for sr in self.regions:
	    num_removed += sr.remove_duplicates(seen)

        return num_removed

    def evaluate(self):
        """
        Evaluate the region.

        Evaluate the region minimum width and length as well as used area
        and fillrate.
        """
        wI = 0
        lI = 0
        aI = 0

        if self.item:
            wI = self.item.w
            lI = self.item.l
            aI = wI*lI

        wA=lA=aA=frA=wB=lB=aB=frB=0
        if self.regions:
            wA,lA,aA,frA = self.regions[0].evaluate()
            wB,lB,aB,frB = self.regions[1].evaluate()

        minw,minl = self.min_dims(wI,lI,wA,lA,wB,lB)
        area = aI + aA + aB

        if minw==0 or minl==0:
            fillrate = 0
        else:
            fillrate = area/(minw*minl)

        return (minw,minl,area,fillrate)

    
class Block(Region):
    """
    Block is a region divided as follows:
    +-------+
    |   B   |
    +---+---+
    | I | A |
    +---+---+
    """
    
    def __repr__(self):
        return "Block(%d,%d)" % (self.w,self.l)

    def calculate_item_coordinates(self,x=0,y=0):
        wI = lI = 0
        if self.regions:
            srA = self.regions[0]
            srB = self.regions[1]
            
            if self.item:
                wI = self.item.w
                lI = self.item.l
            
                self.item.x = x
                self.item.y = y
            else:
                wI = srA.w
                lI = 0

            self.regions[0].calculate_item_coordinates(x+lI,y)
            self.regions[1].calculate_item_coordinates(x,y+wI)
        
    def split(self,item):
        lA = self.l-item.l
        wA = item.w
        
        lB = self.l
        wB = self.w-item.w

        item.location = self
        self.item = item

	self.regions = [Block(wA,lA),Block(wB,lB)]

    def transpose(self):
        """
        recursively transpose the current Block into Segment.
        """

        # gotta love Python
        
        self.__class__ = Segment
        if self.item: self.item.rotate()
        for r in self.regions:
            r.transpose()
        
    def drop_item(self):
	"""
	Remove the item from the current region.
	Subregion A is grown to occupy the freed space.
	"""
	self.item = None
	self.regions[0].l = self.l

    def repair(self,w,l):
	"""
	Walk through the region tree and reset the region sizes according
        to the required space.

        w,l    maximum dimensions of the region

        Returns the amount of removed regions (not including subregions).
	"""
        num_removed = 0
        wI = lI = 0

        # the item must fit within the maximum dimensions
	if not self.verify_item_size(w,l):
            num_removed += 1

        if self.regions:
            srA = self.regions[0]
            srB = self.regions[1]

            if self.item:
                wI = self.item.w
                lI = self.item.l
                # item defines the region split
                new_wA = wI
                new_lA = l-lI
                new_wB = w-wI
                new_lB = l

                num_removed += srA.repair(new_wA,new_lA)
                num_removed += srB.repair(new_wB,new_lB)

            else:
                wI = lI = 0
                num_removed += srA.repair(w,l)
                wB = w-srA.w
                lB = l
                num_removed += srB.repair(wB,lB)

                # if both subregions are empty, clear the region
                if not srA.item and not srA.regions and \
                   not srB.item and not srB.regions:
                    self.clear_region()

                # more cleanup
                if not srA.item and not srB.item:
                    if not srA.regions and isinstance(srB,Block):
                        self.regions = srB.regions
                    elif not srB.regions and isinstance(srA,Block):
                        self.regions = srA.regions

        # finally, trim the current region size
                    
        if self.regions:
            wA = srA.w
            wB = srB.w
            lA = srA.l
            lB = srB.l
        else:
            wA = wB = lA = lB = 0
                
        self.w = max(wI,wA)+wB
        self.l = max(lI+lA,lB)
                
        return num_removed

    def expand(self,w,l):
        "Expand the region to consume the given width and length"
        
        self.w = w
        self.l = l

        if self.regions:
            srA = self.regions[0]
            srB = self.regions[1]
            
            if self.item:
                wI = self.item.w
                lI = self.item.l
            else:
                wI = srA.w
                lI = 0
            srA.expand(wI,l-lI)
            srB.expand(w-wI,l)
        
    def min_dims(self,wI,lI,wA,wB,lA,lB):
        "Return minimal dimensions enclosing the item and the subregions."
        minw = wI + wB
        minl = max(lB,lI+lA)
        return minw,minl


        
class Segment(Region):
    """
    Segment is a region divided as follows:
    +---+---+
    | A |   |
    +---+ B |
    | I |   |
    +---+---+
    """

    def __repr__(self):
        return "Segment(%d,%d)" % (self.w,self.l)

    def calculate_item_coordinates(self,x=0,y=0):
        wI = lI = 0
        if self.regions:
            srA = self.regions[0]
            srB = self.regions[1]

            if self.item:
                wI = self.item.w
                lI = self.item.l
            
                self.item.x = x
                self.item.y = y
            else:
                wI = 0
                lI = srA.l
                
            self.regions[0].calculate_item_coordinates(x,y+wI)
            self.regions[1].calculate_item_coordinates(x+lI,y)
        
    def split(self,item):
        lA = item.l
        wA = self.w-item.w
        
        lB = self.l-item.l
        wB = self.w

        item.location = self
        self.item = item
        
        self.regions = [Block(wA,lA),Segment(wB,lB)]

    def transpose(self):
        """
        recursively transpose the current Block into Segment.
        """

        # gotta love Python
        
        self.__class__ = Segment
        if self.item: self.item.rotate()
        for r in self.regions:
            r.transpose()

            
    def drop_item(self):
	"""
	Remove the item from the current region.
	Subregion A is grown to occupy the freed space.
	"""
	self.item = None
	self.regions[0].w = self.w

    def repair(self,w,l):
	"""
	Walk through the region tree and reset the region sizes according
        to the required space. Also, fix dead-end Segments (Segments
        with only Blocks as subregions).

        w,l    maximum dimensions of the region

        Returns the amount of removed regions (not including subregions).
        """
        num_removed = 0
        wI = lI = 0
        
        # the item must fit within the maximum dimensions
        if not self.verify_item_size(w,l):
            num_removed += 1

        if self.regions:
            srA = self.regions[0]
            srB = self.regions[1]

            # wrap dead-ends to segments
            if isinstance(srB,Block):
                s = Segment(srB.w,srB.l)
                s.regions = [srB, Segment(0,0)]
                srB = self.regions[1] = s
                
            if self.item:
                wI = self.item.w
                lI = self.item.l
                # item defines the region split
                new_wA = w-wI
                new_lA = lI
                new_wB = w
                new_lB = l-lI
                
                num_removed += srA.repair(new_wA,new_lA)
                num_removed += srB.repair(new_wB,new_lB)

            else:
                wI = lI = 0
                num_removed += srA.repair(w,l)
                wB = w
                lB = l-srA.l
                num_removed += srB.repair(wB,lB)

                # if both subregions are empty, clear the region
                if not srA.item and not srA.regions and \
                   not srB.item and not srB.regions:
                    self.clear_region()

                # more cleanup
                if not srA.item and not srB.item:
                    if not srA.regions:
                        self.regions = srB.regions

        # finally, trim the current region size
                    
        if self.regions:
            wA = srA.w
            wB = srB.w
            lA = srA.l
            lB = srB.l
        else:
            wA = wB = lA = lB = 0
        self.w = max(wI+wA,wB)
        self.l = max(lI,lA)+lB

        return num_removed

    def expand(self,w,l):
        "Expand the region to consume the given width and length"
        
        self.w = w
        self.l = l

        if self.regions:
            srA = self.regions[0]
            srB = self.regions[1]
            
            if self.item:
                wI = self.item.w
                lI = self.item.l
            else:
                wI = 0
                lI = srA.l
            srA.expand(w-wI,lI)
            srB.expand(w,l-lI)


    def min_dims(self,wI,lI,wA,wB,lA,lB):
        "Return minimal dimensions enclosing the item and the subregions."
        minl = lI + lB
        minw = max(wB,wI+wA)
        return minw,minl


class RegionChromosome(pygena.BaseChromosome):
    items = []
    W = 0
    L = 0
    item_min_dim = 0
    optimization = pygena.MINIMIZE
    def __init__(self):
        pygena.BaseChromosome.__init__(self)
        self.items = copy.deepcopy(RegionChromosome.items)
        self.region = None
        self.randomize()
        self.repair()
        

    def _random_rotate_items(self):
        for item in self.items:
            if random.randint(0,1):
                item.rotate()
        
    def randomize(self):
        self.region = Segment(self.W,self.L)
        s = Segment(self.W,self.L)
        self._random_rotate_items()
        # uncomment this to test the GA performance more efficiently
        #random.shuffle(self.items)
        s.populate(self.items[:])
        self.region.regions = [Segment(0,0),s]

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

            reg_1 = sc.items[c1].location
            reg_2 = oc.items[c2].location
        
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
                    item.location.transpose()
                elif r2 < 2./3:
                    item.rotate()
                else:
                    item.location.drop_item()
                mutated = True
        if mutated:
            self.repair()

    def repair(self):
        self.region.fix_layout(self.items,self.W,self.L,self.item_min_dim)
        assert(self.region.num_items()==len(self.items)) # must have all items in the layout
        self.evaluate()

    def evaluate(self):
        self.score = self.region.l/self.region.fillrate()

    def asString(self):
        return 'items=%d, w=%d, l=%d, fillrate=%f' % (self.region.num_items(), self.region.w, self.region.l, self.region.fillrate())
        

def optimize(items,W,verbose=False):
    items.sort(key=lambda x: x.area(), reverse=True)
    RegionChromosome.items = items
    RegionChromosome.W = W
    RegionChromosome.L = 1e6 # any large value should do
    RegionChromosome.optimization = pygena.MINIMIZE

    RegionChromosome.item_min_dim = \
        min([i.w for i in items]+[i.l for i in items])
    
    env = pygena.Population(RegionChromosome, maxgenerations=50, optimum=0,
                            tournament=pygena.roulette_tournament,
                            size=100,
                            crossover_rate=0.7, mutation_rate=0.3)
    best = env.run()
    best.region.calculate_item_coordinates()
    output_items = best.region.get_items()

    print "output_items:", len(output_items)

    #best.region.dump()
    
    return best.region.l,output_items

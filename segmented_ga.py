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
	# create a unique identifier for later matching of duplicates
	self.id = id(self)

    def rotate(self):
        self.rotated = not self.rotated

    l = property(lambda self: self.type.l)
    w = property(lambda self: self.type.w)

    def area(self):
        return self.w*self.l

    def __repr__(self):
        return "Item(type_=%r,rotated=%d)" % (self.type,self.rotated)
    
    def __str__(self):
        return "Item (%d,%d) of type %r" % (self.w,self.l,self.type)

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

        #FIXME: only iterate through the regions if they're larger than
        # the minimum piece dimensions
        
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
        print "1",self.num_items(),len(items),self.w,self.l
	self.repair_sizes(w,l)
        print "2",self.num_items(),len(items),self.w,self.l
	l = self.populate(items[:],item_min_dim)
        print l
        assert(len(l)==0) # every piece should fit now
        print "3",self.num_items(),len(items),self.w,self.l
	self.remove_duplicates({})
        print "4",self.num_items(),len(items),self.w,self.l
        self.trim_length()
        print "------"
        assert(self.l>1000)

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


    def trim_length(self):
        """
        Trim region lengths.
        """
        w = self.w
        self.trim()
        self.w = w

    
class Block(Region):
    """
    Block is a region divided as follows:
    +-------+
    |   B   |
    +---+---+
    | I | A |
    +---+---+
    """
    def split(self,item):
        lA = self.l-item.l
        wA = item.w
        
        lB = self.l
        wB = self.w-item.w

        item.location = self
        self.item = item

	self.regions = [Block(wA,lA),Block(wB,lB)]

    def drop_item(self):
	"""
	Remove the item from the current region.
	Subregion A is grown to occupy the freed space.
	"""
	self.item = None
	self.regions[0].l = self.l

    def repair_sizes(self,w,l):
	"""
	Walk through the region tree and reset the region sizes according
        to available region size. 

        Returns the amount of removed regions (not including subregions).
	"""
        num_removed = 0

        self.w = w
        self.l = l
	if not self.verify_item_size(w,l):
            num_removed += 1

        if self.regions:
            srA = self.regions[0]
            srB = self.regions[1]

            if self.item:
                new_wA = w
                new_lA = l-self.item.l
                new_wB = w-self.item.w
                new_lB = l

                num_removed += srA.repair_sizes(new_wA,new_lA)
                num_removed += srB.repair_sizes(new_wB,new_lB)
            else:
                num_removed += srA.repair_sizes(w,l)
                wB = w-srA.w
                lB = l
                num_removed += srB.repair_sizes(wB,lB)

        return num_removed

    def trim(self):
        """
        Trim the region sizes.

        Trim walks through the region tree and reduces the region sizes
        to a minimum being able to hold the item and the subregions.
        """
        for sr in self.regions:
            sr.trim()

        if self.item:
            wI = self.item.w
            lI = self.item.l
        else:
            wI = 0
            lI = 0

        if self.regions:
            wA = self.regions[0].w
            wB = self.regions[1].w
            lA = self.regions[0].l
            lB = self.regions[1].l
        else:
            wA = wB = lA = lB = 0

        self.w = max(wI,wA)+wB
        self.l = max(lI+lA,lB)

        
class Segment(Region):
    """
    Segment is a region divided as follows:
    +---+---+
    | A |   |
    +---+ B |
    | I |   |
    +---+---+
    """
    def split(self,item):
        lA = item.l
        wA = self.w-item.w
        
        lB = self.l-item.l
        wB = self.w

        item.location = self
        self.item = item
        
        self.regions = [Block(wA,lA),Segment(wB,lB)]

    def drop_item(self):
	"""
	Remove the item from the current region.
	Subregion A is grown to occupy the freed space.
	"""
	self.item = None
	self.regions[0].w = self.w

    def repair_sizes(self,w,l):
	"""
	Walk through the region tree and make sure all regions fit
	the available space.

        Returns the amount of removed regions (not including subregions).
        """
        num_removed = 0

        if not self.verify_item_size(w,l):
            num_removed += 1

        if self.regions:
            srA = self.regions[0]
            srB = self.regions[1]

            if self.item:
                new_wA = w-self.item.w
                new_lA = self.item.l
                new_wB = w
                new_lB = l-self.item.l
                
                num_removed += srA.repair_sizes(new_wA,new_lA)
                num_removed += srB.repair_sizes(new_wB,new_lB)
            else:
                num_removed += srA.repair_sizes(w,l)
                wB = w
                lB = l-srA.l
                num_removed += srB.repair_sizes(wB,lB)

        return num_removed

    
    def trim(self):
        """
        Trim the region sizes.

        Trim walks through the region tree and reduces the region sizes
        to a minimum being able to hold the item and the subregions.
        """
        for sr in self.regions:
            sr.trim()

        if self.item:
            wI = self.item.w
            lI = self.item.l
        else:
            wI = 0
            lI = 0

        if self.regions:
            wA = self.regions[0].w
            wB = self.regions[1].w
            lA = self.regions[0].l
            lB = self.regions[1].l
        else:
            wA = wB = lA = lB = 0

        self.w = max(wI+wA,wB)
        self.l = max(lI,lA)+lB

class RegionChromosome(pygena.BaseChromosome):
    items = []
    W = 0
    L = 0
    item_min_dim = 0
    optimization = pygena.MINIMIZE
    def __init__(self):
        pygena.BaseChromosome.__init__(self)
        self.items = copy.deepcopy(RegionChromosome.items)
        self.randomize()
        self.region.trim_length()
        self.evaluate()
        

    def _random_rotate_items(self):
        for item in self.items:
            item.rotated = random.randint(0,1)==1
        
    def randomize(self):
        self.region = Segment(self.W,self.L)
        self._random_rotate_items()
        random.shuffle(self.items)
        self.region.populate(self.items[:])
        self.region.trim_length()

    def crossover(self,other):
        """
        perform crossover operation on two region trees.
        return two copies after the operation without repairing them.
        """
        
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

        # repair the offspring
        sc.repair()
        oc.repair()
        
        # return the object copies
        return (sc,oc)
        
    def mutate(self,mutationRate):
        mutated = False
        for item in self.items:
            if random.random() < mutationRate/len(self.items):
                item.rotate()
                mutated = True
        if mutated:
            self.repair()

    def repair(self):
        self.region.fix_layout(self.items,self.W,self.L,self.item_min_dim)
        self.evaluate()

    def evaluate(self):
        self.score = self.region.l

    def asString(self):
        return 'l=%d, fillrate=%f' % (self.region.l, self.region.fillrate())
        
        
def optimize(items,W,verbose=False):
    RegionChromosome.items = items
    RegionChromosome.W = W
    RegionChromosome.L = 1e6 # any large value should do
    RegionChromosome.item_min_dim = \
        min([i.w for i in items]+[i.l for i in items])
    env = pygena.Population(RegionChromosome, maxgenerations=1000, optimum=0,
                            crossover_rate=0.7, mutation_rate=0.01)
    env.run()

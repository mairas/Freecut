#! /usr/bin/python
# -*- coding: utf-8 -*-

import pygena
import sys
import math

class ItemType(object):
    def __init__(self, width, length, description=""):
        self.w = w
        self.l = l
        self.description = description

class Item(object):
    def __init__(self,type_,rotated):
        self.type = type_
        self.rotated = rotated
        # location within the region tree
        self.location = None
	# create a unique identifier for later matching of duplicates
	self.id = id(self)

    def rotate(self):
        self.rotated = not self.rotated



class Region(object):
    """
    Region is any rectangular area on a plane.
    A Region may contain an item, in which case the remaining area is divided
    into two subregions.
    """
    def __init__(self,l,w):
        self.l = l
        self.w = w
        self.item = None
        self.subregions = []

    def area(self):
        return self.l*self.w

    def fits(self,item):
	return (item.w<self.w and item.l<self.l)

    def populate(self,items):
	"""
	Populate a region using a list of items.
	Take a list of items and fill the region with items.
	No optimization is performed.
	Returns a list of items not fitted to the region.
	"""

	# only place the item if the region is empty
	if self.item == None and not self.subregions:
	    for item in items:
		if self.fits(item):
		    self.split(item)
		    items.remove(item)
		    break
	if items:
	    for sr in self.subregions:
		items = sr.populate(items)
		if not items: break
		
	return items

    def clear_region(self):
	self.item = None
	self.subregions = []

    def verify_item_size(self):
	"""
	Verify that that item will fit the region and if not,
	remove the item.
	"""
	if self.item.l>l or self.item.w>w:
	    self.drop_item()

    def fix_layout(self,items,w,l):
	"""
	Fix the layout after crossover and mutation operations.
	"""
	# FIXME: it's a bit silly to first fill the layout with duplicates
	#   	 and then remove them again... Should first remove the genuine
	#	 duplicates and get a list of placed items
	self.populate(items)
	self.remove_duplicates()
	self.repair_sizes(w,l)

    def remove_duplicates(self,seen={}):
	if seen.has_key(self.item.id):
	    self.drop_item()
	else:
	    seen[self.id] = True
	for sr in self.subregions:
	    sr.remove_duplicates(seen)


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

	self.subregions = [Block(lA,wA),Block(lB,wB)]

    def drop_item(self):
	"""
	Remove the item from the current region.
	Subregion A is grown to occupy the freed space.
	"""
	self.item = None
	self.subregions[0].l = self.l

    def repair_sizes(self,w,l):
	"""
	Walk through the region tree and make sure all regions fit
	the available space.
	"""
	self.verify_item_size(w,l)

	srA = self.subregions[0]
	srB = self.subregions[1]

	if item:
	    new_wA = w
	    new_lA = l-self.item.l
	    new_wB = w-self.item.w
	    new_lB = l

	    srA.repair_sizes(new_wA,new_lA)
	    srB.repair_sizes(new_wB,new_lB)
	else:
	    srA.repair_sizes(w,l)
	    wB = w-srA.w
	    lB = l
	    srB.repair_sizes(wB,lB)
	    

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
        lA = self.l-item.l
        wA = item.w
        
        lB = self.l
        wB = self.w-item.w

        item.location = self
        
        return [Block(lA,wA),Segment(lB,wB)]

    def drop_item(self):
	"""
	Remove the item from the current region.
	Subregion A is grown to occupy the freed space.
	"""
	self.item = None
	self.subregions[0].w = self.w

    def repair_sizes(self,w,l):
	"""
	Walk through the region tree and make sure all regions fit
	the available space.
	"""
	self.verify_item_size(w,l)

	srA = self.subregions[0]
	srB = self.subregions[1]

	if item:
	    new_wA = w-self.item.w
	    new_lA = self.item.l
	    new_wB = w
	    new_lB = l-self.item.l

	    srA.repair_sizes(new_wA,new_lA)
	    srB.repair_sizes(new_wB,new_lB)
	else:
	    srA.repair_sizes(w,l)
	    wB = w
	    lB = l-srA.l
	    srB.repair_sizes(wB,lB)


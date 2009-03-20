#! /usr/bin/python
# -*- coding: utf-8 -*-

import pygena
import sys
import math

class Type(object):
    def __init__(self, width, height, description=""):
        self.w = w
        self.h = h
        self.description = description

class Item(object):
    def __init__(self,type_,rotated):
        self.type = type_
        self.rotated = rotated
        # location within the region tree
        self.location = None

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
               
        return [Block(lA,wA),Block(lB,wB)]


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
        
        return [Block(lA,wA),Block(lB,wB)]


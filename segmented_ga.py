#! /usr/bin/python

import pygena
import sys
import math

class Type(object):
    def __init__(self, width, height, description=""):
        self.w = w
        self.h = h
        self.description = description

class Piece(object):
    def __init__(self,type_,rotated):
        self.type = type_
        self.rotated = rotated

    def rotate(self):
        self.rotated = not self.rotated

        

class Region(object):
    def __init__(self,l,w):
        self.l = l
        self.w = w

    def area(self):
        return self.l*self.w

    

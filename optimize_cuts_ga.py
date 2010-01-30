#!/usr/bin/env python

import sys
import striped_ga as optalg
#import segmented_ga as optalg
from optparse import OptionParser
from pyparsing import *
from itemplot import *

def parse_input(f):
    # define the grammar
    ParserElement.setDefaultWhitespaceChars(" \t")
    intnum = Word(nums)
    floatnum = Combine(Word(nums) + "." + Word(nums) +
                       Optional('e'+oneOf("+ -")+Word(nums)))
    number = (intnum^floatnum).setParseAction( lambda s,l,t: [ float(t[0]) ] )
    #number = (intnum).setParseAction( lambda s,l,t: [ int(t[0]) ] )
    comma = Literal(",").suppress()
    nl = Literal("\n").suppress()
    amount = Optional((comma + number).setParseAction( lambda s,l,t: [ int(t[0]) ]),default=1)
    rotatable = Optional(comma + Literal("N"),default="Y").setParseAction( lambda s,l,t: [ t[0]=='Y' ] )
    data = number + comma + number + Optional(amount + Optional(rotatable))
    row = Group(data + restOfLine.setParseAction( lambda s,l,t: [ t[0].strip() ]))
    rows = ZeroOrMore(pythonStyleComment.suppress() ^ row ^ nl.suppress())

    return rows.parseFile(f)

def input_items(filename):
    lines = parse_input(filename)

    items = []
    
    for line in lines:
        w,h,n,r,s = line
        typ = optalg.ItemType(w, h, s, r)
        for i in range(n):
            items.append(optalg.Item(typ))
                
    return items

def types(items):
    types = {}
    for item in items:
        types[item.type] = True

    for typ in types.keys():
        yield typ

def add_trim(items,trim):
    for typ in types(items):
        typ.w += trim
        typ.h += trim

def remove_trim(items,trim):
    for typ in types(items):
        typ.w -= trim
        typ.h -= trim

if __name__=='__main__':
    parser = OptionParser()
    parser.set_defaults(pairs=[])
    #parser.add_option("-o","--output",dest="output",
    #                  help="the output file name")
    parser.add_option("-t","--trim",dest="trim",type="int",
                      help="the trim amount", default=0.)
    parser.add_option("-H","--height",dest="height",type="int",
                      help="the plate height")
    
    (options,args) = parser.parse_args()
    H = options.height
    trim = options.trim

    items = input_items(args[0])

    add_trim(items,trim)
    
    W,items = optalg.optimize(items,H+trim,verbose=True)

    # remove the trim from the pieces
    W -= trim
    remove_trim(items,trim)
    
    plot_layout(items,W,H,show=True)
    
    for item in items:
        print item.w,item.h,item.x,item.y
    

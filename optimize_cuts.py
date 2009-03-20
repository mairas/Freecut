#!/usr/bin/env python

import sys
from hrbb import Item,optimize_HRBB,plot_layout
import re
from optparse import OptionParser
from pyparsing import *

def parse_input(f):
    # define the grammar
    ParserElement.setDefaultWhitespaceChars(" \t")
    floatnum = Combine(Word(nums) + "." + Word(nums) +
                       Optional('e'+oneOf("+ -")+Word(nums)))
    number = (Word(nums)^floatnum).setParseAction( lambda s,l,t: [ float(t[0]) ] )
    comma = Literal(",").suppress()
    nl = Literal("\n").suppress()
    amount = Optional((comma + number).setParseAction( lambda s,l,t: [ int(t[0]) ]),default=1)
    rotatable = Optional(comma + Literal("N"),default="Y").setParseAction( lambda s,l,t: [ t[0]=='Y' ] )
    data = number + comma + number + Optional(amount + Optional(rotatable))
    row = Group(data + restOfLine.setParseAction( lambda s,l,t: [ t[0].strip() ]))
    rows = ZeroOrMore(pythonStyleComment.suppress() ^ row ^ nl.suppress())

    return rows.parseFile(f)

def input_items(filename,trim):
    lines = parse_input(filename)

    items = []
    
    for line in lines:
        l,w,n,r,s = line
        l += trim
        w += trim
        if n>1:
            for i in range(n):
                if len(s)>0:
                    s_i = "%s #%d" % (s,i+1)
                else:
                    s_i = ""
                items.append(Item(l,w,rotatable=r,s=s_i))
        else:
            items.append(Item(l,w,rotatable=r,s=s))
                
    return items

if __name__=='__main__':
    parser = OptionParser()
    parser.set_defaults(pairs=[])
    #parser.add_option("-o","--output",dest="output",
    #                  help="the output file name")
    parser.add_option("-t","--trim",dest="trim",type="int",
                      help="the trim amount")
    parser.add_option("-W","--width",dest="width",type="int",
                      help="the plate width")
    parser.add_option("-s", "--segments", action="store_true",
                      dest="segments", default=False,
                      help="cut all regions into segments only")
    parser.add_option("--alpha",dest="alpha",type="float",
                      help="maximum plate length as "
                      "a multiple of minimum surface area",
                      default=2.0)
    
    (options,args) = parser.parse_args()
    W = options.width
    alpha = options.alpha
    trim = options.trim
    seg = options.segments

    items = input_items(args[0],options.trim)
    L,items = optimize_HRBB(items,W+trim,alpha,verbose=True,
                            segments_only=seg)

    # remove the trim from the pieces
    L -= trim
    
    for item in items:
        item.l -= trim
        item.w -= trim
    
    plot_layout(items,L,W,show=True)
    
    for item in items:
        print item.l,item.w,item.x,item.y
    

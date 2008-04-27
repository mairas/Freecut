#!/usr/bin/env python

import sys
from freecut import Item,optimize_HRBB,plot_layout
import re
from optparse import OptionParser

def input_items(filename,trim):
    lines = open(filename,'r').readlines()

    # remove empty lines
    el = re.compile('^\s*$')
    # remove comments
    cl = re.compile('^\s*#')
    
    clean = []
    for line in lines:
        if el.match(line)==None and cl.match(line)==None:
            clean.append(line)
    
    items = []
    
    for l in clean:
        ns = l.split()
        n = [int(n)+trim for n in ns]
        items.append(Item(n[0],n[1]))
    
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
    
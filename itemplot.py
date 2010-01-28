#! /usr/bin/python

"""
Plot item layouts when given area length, width, and item objects
(having w,l,x,y attributes).
"""

import pylab

def plot_item(item,c,text=None):
    x,y,w,h = item.x,item.y,item.w,item.h
    pylab.plot([x,x,x+w,x+w,x],[y,y+h,y+h,y,y],c)
    if text!=None:
        pylab.text(x+w/2,y,str(w), fontsize=8,
                   horizontalalignment='center',
                   verticalalignment='bottom',)
        pylab.text(x+w,y+h/2,str(h), fontsize=8,
                   horizontalalignment='right',
                   verticalalignment='center',)
        if h>w:
            pylab.text(x+w/3, y+h/2,text, fontsize=8,
                       horizontalalignment='center',
                       verticalalignment='center',
                       rotation=90)
        else:
            pylab.text(x+w/2, y+h*2./3,text, fontsize=8,
                       horizontalalignment='center',
                       verticalalignment='center',)

def plot_layout(items,W,H,show=False,draw=False):
    colors = ['r','g','b','c','m','y','k']
    if len(items)>0:
        pylab.clf()
        pylab.axes(aspect='equal')
        # plot the board borders
        pylab.plot([0,0,0+W,0+W,0],[0,0+H,0+H,0,0],'k')

        for i,item in enumerate(items):
            plot_item(item,colors[i%len(colors)])
        if draw:
            pylab.draw()
        if show:
            pylab.show()

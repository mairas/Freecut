#! /usr/bin/python

"""
Plot item layouts when given area length, width, and item objects
(having w,l,x,y attributes).
"""

import pylab

def plot_item(item,c,text=None):
    x,y,l,w = item.x,item.y,item.l,item.w
    pylab.plot([x,x,x+l,x+l,x],[y,y+w,y+w,y,y],c)
    if text!=None:
        pylab.text(x+l/2,y,str(l), fontsize=8,
                   horizontalalignment='center',
                   verticalalignment='bottom',)
        pylab.text(x+l,y+w/2,str(w), fontsize=8,
                   horizontalalignment='right',
                   verticalalignment='center',)
        if w>l:
            pylab.text(x+l/3, y+w/2,text, fontsize=8,
                       horizontalalignment='center',
                       verticalalignment='center',
                       rotation=90)
        else:
            pylab.text(x+l/2, y+w*2./3,text, fontsize=8,
                       horizontalalignment='center',
                       verticalalignment='center',)

def plot_layout(items,L,W,show=False,draw=False):
    colors = ['r','g','b','c','m','y','k']
    if len(items)>0:
        pylab.clf()
        pylab.axes(aspect='equal')
        plot_rect(0,0,L,W,'k')

        for i,item in enumerate(items):
            plot_item(item,colors[i%len(colors)])
        if draw:
            pylab.draw()
        if show:
            pylab.show()

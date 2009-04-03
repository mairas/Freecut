#!/usr/bin/python

import unittest
from segmented_ga import *

t1 = ItemType(100,1500)
t2 = ItemType(300,300)
t3 = ItemType(400,400)

i1 = Item(t1)
i1r = Item(t1,rotated=True)
i2 = Item(t1)
i3 = Item(t2)
i4 = Item(t3)

items = [i1,i2,i3,i4]

class TestSequenceFunctions(unittest.TestCase):
    def test_segment_split(self):
        s = Segment(2000,2000)
        s.split(i1)
        self.assertEqual(s.item.l,1500)
        self.assertEqual(s.item.type,t1)
        self.assertEqual(s.regions[0].w,1900)
        self.assertEqual(s.regions[0].l,1500)
        self.assertEqual(s.regions[1].w,2000)
        self.assertEqual(s.regions[1].l,500)

    def test_block_split(self):
        b = Block(2000,2000)
        b.split(i1)
        self.assertEqual(b.item.l,1500)
        self.assertEqual(b.item.type,t1)
        self.assertEqual(b.regions[0].w,100)
        self.assertEqual(b.regions[0].l,500)
        self.assertEqual(b.regions[1].w,1900)
        self.assertEqual(b.regions[1].l,2000)

    def test_populate_succeed(self):
        s = Segment(2000,4000)
        l = s.populate([i1,i2,i3,i4])
        self.assertEqual(l,[])

    def test_populate_fail(self):
        s = Segment(200,2000)
        l = s.populate([i1,i2,i3])
        self.assertEqual(len(l),1)

    def test_remove_duplicates_0(self):
        s = Segment(2000,4000)
        l = s.populate([i1,i2,i3,i4])
        self.assertEqual(l,[])
        self.assertEqual(s.remove_duplicates({}),0)

    def test_remove_duplicates_1(self):
        s = Segment(2000,4000)
        l = s.populate([i1,i2,i3,i4,i3])
        self.assertEqual(l,[])
        nr = s.remove_duplicates({})
        self.assertEqual(nr,1)

    def test_remove_duplicates_2(self):
        s = Segment(2000,4000)
        l = s.populate([i1,i2,i3,i4,i3,i2])
        self.assertEqual(l,[])
        self.assertEqual(s.remove_duplicates({}),2)

    def test_repair_sizes(self):
        s = Segment(2000,4000)
        s.populate([i3,i2,i4])
        s.item=i1
        n = s.repair_sizes(2000,4000)
        #self.assertEqual(n,1)

    def test_chromosome_init(self):
        RegionChromosome.items = items
        RegionChromosome.W = 2000
        RegionChromosome.L = 10000

        itemarea = sum([it.area() for it in items])

        rc = RegionChromosome()
        self.assertEqual(rc.region.covered_area(),itemarea)

    def test_chromosome_mutate(self):
        RegionChromosome.items = items
        RegionChromosome.W = 2000
        RegionChromosome.L = 10000

        itemarea = sum([it.area() for it in items])

        rc = RegionChromosome()

        rc.mutate(1.)
        rc.repair()
        self.assertEqual(rc.region.covered_area(),itemarea)


    def test_chromosome_crossover(self):
        RegionChromosome.items = items
        RegionChromosome.W = 2000
        RegionChromosome.L = 10000

        itemarea = sum([it.area() for it in items])

        rc1 = RegionChromosome()
        rc2 = RegionChromosome()

        self.assertEqual(rc1.region.covered_area(),itemarea)
        self.assertEqual(rc2.region.covered_area(),itemarea)

        
        co1,co2 = rc1.crossover(rc2)
        
        self.assert_(co1.region.covered_area()>0)
        self.assert_(co2.region.covered_area()>0)

        
if __name__ == '__main__':
    unittest.main()


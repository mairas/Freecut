#!/usr/bin/env python

import unittest
from hrbb import *

i1 = Item(100,2000)
i2 = Item(100,2000)
i3 = Item(300,300)
i4 = Item(400,400)

class TestSequenceFunctions(unittest.TestCase):
    def test_one(self):
        pool = [i1]
        N = len(pool)
        W = 1000
        L = 3000
        S = sum([s.value() for s in pool])
        r = Segment(L,W,0,0)
        items = copy.copy(pool)
        vmax,success = r.layout(pool, S, 0, 0)
        for p in pool:
            items.remove(p)
        self.assertEqual(N,len(items))
        self.assertTrue(r.contains(items))
        
    def test_fail(self):
        pool = [i1]
        N = len(pool)
        W = 1000
        L = 1000
        S = sum([s.value() for s in pool])
        r = Segment(L,W,0,0)
        items = copy.copy(pool)
        vmax,success = r.layout(pool, S, 0, 0)
        for p in pool:
            items.remove(p)
        self.assertNotEqual(N,len(items))
        self.assertFalse(success)
        
        
    def test_normal(self):
        pool = [i1,i2]
        N = len(pool)
        W = 1000
        L = 3000
        S = sum([s.value() for s in pool])
        r = Segment(L,W,0,0)
        items = copy.copy(pool)
        vmax,success = r.layout(pool, S, 0, 0)
        for p in pool:
            items.remove(p)
        self.assertEqual(N,len(items))
        self.assertTrue(r.contains(items))
        self.assertFalse(overlap(items))
        
    def test_rotated(self):
        pool = [i1,i2]
        N = len(pool)
        W = 3000
        L = 1000
        S = sum([s.value() for s in pool])
        r = Segment(L,W,0,0)
        items = copy.copy(pool)
        vmax,success = r.layout(pool, S, 0, 0)
        for p in pool:
            items.remove(p)
        self.assertEqual(N,len(items))
        self.assertTrue(r.contains(items))
        self.assertFalse(overlap(items))
        
    def test_three(self):
        # a test case which asserts a bug
        pool = [Item(1540,700),Item(650,1502),Item(301,762),]
        N = len(pool)
        W = 1830
        L = 1540
        S = sum([s.value() for s in pool])
        r = Segment(L,W,0,0)
        items = copy.copy(pool)
        vmax,success = r.layout(pool, S, 0, 0)
        for p in pool:
            items.remove(p)
        self.assertEqual(N,len(items))
        self.assertTrue(r.contains(items))
        self.assertFalse(overlap(items))
                
if __name__ == '__main__':
    unittest.main()

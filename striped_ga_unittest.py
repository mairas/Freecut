#!/usr/bin/python

import unittest
from striped_ga import *
import pdb
import copy

t1 = ItemType(1500, 100)
t2 = ItemType(300, 300)
t3 = ItemType(400, 400)

i1 = Item(t1)
i1r = Item(t1,rotated=True)
i2 = Item(t1)
i3 = Item(t2)
i4 = Item(t3)

items = [i1,i2,i3,i4]

class TestSequenceFunctions(unittest.TestCase):
    def test_basic_layout(self):
        s = HStrip()
        s.append(i1)
        v = VStrip()
        v.append(i2)
        v.append(i3)
        s.append(v)
        s.append(i4)

        s.update_dimensions(2000,4000)

        self.assertEqual(v.area(),400*1500)
        
    def test_populate(self):
        s = HStrip()
        for i in range(10):
            s.append(VStrip())

        litems = copy.deepcopy(items)

        areas = sum([i.area() for i in litems])

        s.update_dimensions(2000,4000)

        s.populate(litems)

        s.update_dimensions(2000,4000)
        
        self.assertEqual(len(litems),0)
        self.assertEqual(s.covered_area(),areas)

    def test_repair_h_fit(self):
        s = HStrip()
        s.append(i1)
        v = VStrip()
        v.append(i3)
        v.append(i4)
        s.append(v)
        s.append(i2)

        s.update_dimensions(2000,2000)

        areas = sum([i.area() for i in [i1,i3,i4]])

        dropped = s.repair()

        dropped_areas = sum([i.area() for i in dropped])

        self.assertEqual(s.covered_area(),areas)
        self.assertEqual(dropped_areas,i2.area())
        
    def test_repair_v_fit(self):
        s = HStrip()
        v = VStrip()
        v.append(i1r)
        v.append(i3)
        v.append(i4)
        s.append(v)
        s.append(i1)

        s.update_dimensions(2000,2000)

        areas = sum([i.area() for i in [i1r,i3,i1]])

        dropped = s.repair()

        dropped_areas = sum([i.area() for i in dropped])

        self.assertEqual(s.covered_area(),areas)
        self.assertEqual(dropped_areas,i4.area())

    def test_repair_h_remove_empty(self):
        s = HStrip()
        s.append(i1)
        s.append(VStrip())
        s.append(i3)

        s.update_dimensions(2000,2000)
        s.repair()

        self.assertEqual(len(s),2)

    def test_repair_h_merge_substrips(self):
        s = HStrip()
        s.append(i1)
        s2 = HStrip()
        s2.append(i1r)
        s2.append(i2)
        s.append(s2)
        
        s.update_dimensions(2000,4000)
        s.repair()

        self.assertEqual(len(s),3)
        
    def test_repair_h_unwrap_items(self):
        s = HStrip()
        s.append(i1)
        v = VStrip()
        v.append(i3)
        s.append(v)

        s.update_item_min_dims(items)

        s.update_dimensions(350,2000)
        s.repair()

        self.assertEqual(len(s),2)

    def test_repair_h_unwrap_substrips(self):
        s = HStrip()
        s.append(i1)
        v = VStrip()
        h = HStrip()
        h.append(i3)
        v.append(h)
        s.append(v)

        s.update_item_min_dims(items)

        s.update_dimensions(2000,2000)
        s.repair()

        self.assertEqual(len(s),2)

    def test_repair_h_wrap_small_items(self):
        s = HStrip()
        v = VStrip()
        v.append(i4)
        s.append(v)
        s.append(i3)

        s.update_item_min_dims([i3,i4])

        s.update_dimensions(600,2000)

        s.repair()

        self.assertEqual(type(s[1]),VStrip)

    def test_remove_duplicates(self):
        s = HStrip()
        s.append(i1)
        s.append(i1)

        s.remove_duplicates({})

        self.assertEqual(len(s),1)

if __name__ == '__main__':
    unittest.main()


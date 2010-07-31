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
i2r = Item(t1,rotated=True)
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

        s.update_dimensions(4000,2000)

        self.assertEqual(v.area(),400*1500)
        
    def test_populate(self):
        s = HStrip()
        for i in range(10):
            s.append(VStrip())

        litems = copy.deepcopy(items)

        areas = sum([i.area() for i in litems])

        s.update_dimensions(4000,2000)

        s.populate(litems)

        s.update_dimensions(4000,2000)
        
        self.assertEqual(len(litems),0)
        self.assertEqual(s.covered_area(),areas)

    def test_populate_2(self):
        "must be able to place the item"
        unplaced = [Item(ItemType(400,400,'piece 2',True),rotated=False,x=900,y=0)]
        s = HStrip(900,800,1000000,1000,0,0,[
              Item(ItemType(300,600,'piece 1',True),rotated=True,x=0,y=0),
              VStrip(300,800,999400,1000,600,0,[
                HStrip(200,200,999400,200,600,0,[
                  Item(ItemType(200,200,'piece 3',True),rotated=False,x=600,y=0)
                ]),
                Item(ItemType(300,600,'piece 1',True),rotated=False,x=600,y=200)
              ])
            ])

        s.populate(unplaced)

        n = len(s.get_items())

        self.assertEqual(n,4)

    def test_populate_3(self):
        """
        do not utilize available space twice
        """
        s = HStrip()
        v1 = VStrip()
        s.append(v1)
        v2 = VStrip()
        v1.append(v2)
        v2.append(Item(ItemType(1500,100)))

        unplaced = [Item(ItemType(1500,100)),Item(ItemType(1500,100))]

        s.update_dimensions(1000000,200)
        s.populate(unplaced)
        s.update_dimensions(1000000,200)

        self.assert_(s.h<=s.H)

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

    def test_update_dimensions_1(self):
        """
        Test update_dimensions with a simple one-item case
        """
        s = HStrip()
        v = VStrip()
        v.append(i1r)
        s.append(v)

        s.update_dimensions(2000,2000)

        self.assertEqual(s.W,2000)
        self.assertEqual(s.H,2000)
        self.assertEqual(v.W,100)
        self.assertEqual(v.H,2000)

    def test_update_dimensions_2(self):
        """
        Test update_dimensions with two items
        """
        s = HStrip()
        v = VStrip()
        v.append(i1r)
        v.append(i2r)
        s.append(v)

        s.update_dimensions(2000,2000)

        self.assertEqual(s.W,2000)
        self.assertEqual(s.H,2000)
        self.assertEqual(v.W,i1r.w)
        self.assertEqual(v.H,2000)

    def test_update_dimensions_3(self):
        """
        Test update_dimensions with three items that overflow the region
        """
        s = HStrip()
        v = VStrip()
        v.append(i1r)
        v.append(i2r)
        s.append(v)
        s.append(i4)

        s.update_dimensions(2000,2000)

        self.assertEqual(s.W,2000)
        self.assertEqual(s.H,2000)
        self.assertEqual(v.W,i1r.w)
        self.assertEqual(v.H,2000)

    def test_update_dimensions_4(self):
        """
        Test whether available width and length get updated
        """
        s = HStrip()
        v1 = VStrip()
        v2 = VStrip()
        v1.append(i1r)
        v2.append(i2r)
        s.append(v1)
        s.append(v2)

        s.update_dimensions(2000,2000)

        self.assertEqual(s[0].W,i1r.w)
        self.assertEqual(s[0].H,2000)
        self.assertEqual(s[1].W,i1r.w)
        self.assertEqual(s[1].H,2000)


    def test_repair_v_fit_simple(self):
        """
        Test a layout with 1500+1500 height items, fit to
        a strip of 2000 high. i2r should be too much.
        """
        s = HStrip()
        v = VStrip()
        v.append(i1r)
        v.append(i2r)
        s.append(v)

        s.update_dimensions(2000,2000)

        # area that should remain
        areas = i1r.area()

        dropped = s.repair()

        dropped_areas = sum([i.area() for i in dropped])

        # the remaining covered area
        self.assertEqual(s.covered_area(),areas)
        # the dropped area should equal to that of i2r
        self.assertEqual(dropped_areas,i2r.area())

        
    def test_repair_v_fit(self):
        """
        Test a layout with 1500+1500 height items on top
        of each other and try to fit it in a 2000 high strip.
        i2r should be too much.
        """
        s = HStrip()
        v = VStrip()
        v.append(i1r)
        v.append(i2r)
        s.append(v)
        s.append(i4)

        s.update_dimensions(2000,2000)

        # areas of items that should remain
        areas = sum([i.area() for i in [i1r,i4]])

        dropped = s.repair()

        # areas of dropped items
        dropped_areas = sum([i.area() for i in dropped])

        # the remaining covered area
        self.assertEqual(s.covered_area(),areas)
        # the dropped area should equal to that of i2r
        self.assertEqual(dropped_areas,i2r.area())


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
        
        s.update_dimensions(4000,2000)
        s.repair()
        self.assertEqual(len(s),3)
        
    def test_repair_h_unwrap_items(self):
        s = HStrip()
        s.append(i1)
        v = VStrip()
        v.append(i3)
        s.append(v)

        s.update_dimensions(2000,350)
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

        s.update_dimensions(2000,2000)
        s.repair()

        self.assertEqual(len(s),2)

    def test_repair_h_wrap_small_items(self):
        """
        small lone items should be wrapped into a strip

        i3 should get wrapped
        """
        s = HStrip()
        v = VStrip()
        v.append(i4)
        s.append(v)
        s.append(i3)

        s.update_dimensions(2000,600)

        s.repair()

        self.assertEqual(type(s[1]),VStrip)

    def test_repair_wrap_2(self):
        """
        only items with available space should be wrapped
        
        currently, the first item gets wrapped and the
        second one unwrapped, which is totally wrong
        """

        s = HStrip(400,400,10000,1000,0,0,[
              VStrip(400,900,400,1000,0,0,[
                Item(ItemType(400,400,'piece 2',True),rotated=False,x=0,y=0),
                HStrip(300,500,400,500,0,400,[
                  Item(ItemType(300,500,'piece 1',True),rotated=False,x=0,y=400)
                ])
              ])
            ])
        print repr(s)
        s.repair()
        print repr(s)
        self.assertEqual(type(s[0][0]),Item)
        self.assertEqual(type(s[0][1]),HStrip)

    def test_remove_duplicates_2(self):
        """
        this layout has one duplicate item that should be removed
        """
        s = HStrip(1800,900,1000000,1000,0,0,[
          VStrip(600,900,1000000,900,0,0,[
            Item(ItemType(300,600,'piece 1',True),rotated=False,x=0,y=0,id_=44702928),
            Item(ItemType(300,600,'piece 1',True),rotated=True,x=0,y=600,id_=44703440)
          ]),
          VStrip(600,300,1000000,100,600,0,[
            Item(ItemType(300,600,'piece 1',True),rotated=True,x=600,y=0,id_=44703440)
          ]),
          VStrip(200,200,1000000,0,1200,0,[
            Item(ItemType(200,200,'piece 3',True),rotated=False,x=1200,y=0,id_=44703184)
          ]),
          #VStrip(400,400,1000000,0,1400,0,[
          #  Item(ItemType(400,400,'piece 2',True),rotated=False,x=1400,y=0,id_=44699984)
          #])
        ])

        s.remove_duplicates({})

        self.assertEqual(len(s.get_items()),3)


    def test_remove_duplicates(self):
        s = HStrip()
        s.append(i1)
        s.append(i1)

        s.remove_duplicates({})

        self.assertEqual(len(s),1)

    def test_populate(self):
        """
        simplest test of populate that could be made to fail
        """
        items = [Item(ItemType(400,400,'piece 2',True),
                      rotated=False,x=None,y=None),
                 Item(ItemType(300,500,'piece 1',True),
                      rotated=False,x=None,y=None),
                ]

        strip = HStrip()
        strip.update_dimensions(10000,1000)
        #pdb.set_trace()
        strip.populate(items)
        # all items must be placed after populate
        self.assertEqual(len(items),0)
        # items ought to have their locations set
        # items should be within a VStrip within the HStrip
        print repr(strip)
        self.assertEqual(strip[0][0].x,0)
        self.assertEqual(strip[0][0].y,0)
        self.assertEqual(strip[0][1].x,0)
        self.assertEqual(strip[0][1].y,400)

    def test_fill_score_1(self):
        """naive case of fill_score calculation"""
        strip = VStrip()
        strip.append(i4)
        strip.update_dimensions(1000,1000)
        strip.repair()
        strip.update_dimensions(1000,1000)
        score = strip.fill_score()
        self.assertEqual(score,1000.*1000/(400*400)-1+1000.*400/(400*400)-1)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSequenceFunctions)
    unittest.TextTestRunner(verbosity=2).run(suite)

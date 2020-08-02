# -*- coding: utf-8 -*-
import unittest
from .. import main


class TestInvoiceInfo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.params = [
            ({'goufang_mingcheng': '珠海市教育局',
             'goufang_shuihao': 1.0,
             'goufang_yinhangzhanghao': None,
             'goufang_dizhidianhua': '香洲人民东路112号   2121155',
             'beizhu': '测试1',
             'fuheren': '张三',
             'shoukuanren': '李四',
             'shangpinbianmabanbenhao': 33.0,
             'hanshuibiaoji': 1},
             [('Gfmc', '珠海市教育局'),
              ('Gfsh', '1.0'),
              ('Gfyhzh', None),
              ('Gfdzdh', '香洲人民东路112号   2121155'),
              ('Bz', '测试1'),
              ('Fhr', '张三'),
              ('Skr', '李四'),
              ('Spbmbbh', '33.0'),
              ('Hsbz', '1')])
        ]

    def test_object_init(self):
        for sample, expect in self.params:
            with self.subTest():
                obj = main.InvoiceItemInfo(0, **sample)
                result = obj.to_xml_format_list()
                self.assertEqual(result, expect, 'result not hit expect')


if __name__ == '__main__':
    unittest.main()

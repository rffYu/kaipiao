# -*- coding: utf-8 -*-
import unittest
from xml.etree import ElementTree as ET


class TestConstructSph(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.params = [
            # obj_pickle, expect_xml_output
        ]

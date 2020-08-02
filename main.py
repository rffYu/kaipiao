# -*- coding: utf-8 -*-
"""
用于将符合模板要求的Excel转换为开票软件XML格式
"""
import collections
from xml.etree import ElementTree as ET
import numpy as np
import pandas as pd

INTERFACE_VERSION = '2.0'
PRICE_NDIGITS = 8

def transform_nan_to_none(x):
    # transform nan to None
    if isinstance(x, float):
        if np.isnan(x) == True:  # must use ==, not is
            return None
    return x


"""
Object for invoice
"""
class InvoiceItemInfo(object):
    """
    根据LABEL_MAP中键名从kwargs中提取数据, 键名需一一对应
    """
    LABEL_MAP = {
        'goufang_mingcheng': 'Gfmc',
        'goufang_shuihao': 'Gfsh',
        'goufang_yinhangzhanghao': 'Gfyhzh',
        'goufang_dizhidianhua': 'Gfdzdh',
        'beizhu': 'Bz',
        'fuheren': 'Fhr',
        'shoukuanren': 'Skr',
        'shangpinbianmabanbenhao': 'Spbmbbh',  # eg: 33
        'hanshuibiaoji': 'Hsbz'  # 0: 不含税
    }

    # 必须提供的键名
    REQUIRED_KEYS = [
        'goufang_mingcheng',
        'goufang_shuihao',
        'shangpinbianmabanbenhao',
        'hanshuibiaoji'
    ]

    TYPE_MAP = {
        'guofang_shuihao': str,
    }

    def __init__(self, invoice_number, **kwargs):
        self.invoice_number = invoice_number
        for k in self.LABEL_MAP:
            setattr(self, k, kwargs.get(k, None))

        # verify required value is not empty
        for k in self.REQUIRED_KEYS:
            if getattr(self, k) is None:
                raise ValueError('InvoiceItemInfo {} {} 键值 {} 是必填项, 但是该项为空值'.format(
                    self.invoice_number, getattr(self, 'goufang_mingcheng', 'Empty client_name'), k))

        self._transform_init_value_type()

    def _transform_init_value_type(self):
        for k, v in self.TYPE_MAP.items():
            input_value = getattr(self, k, None)
            if input_value is not None:
                setattr(self, k, v(input_value))

    def to_xml_format_list(self):
        result = []
        for k, transformed_key in self.LABEL_MAP.items():
            value = getattr(self, k, None)
            if value is not None:
                result.append((transformed_key, str(value)))
            else:
                result.append((transformed_key, None))

        return result


class InvoiceItemGoodDetail(object):
    """
    sph node
    """
    LABEL_MAP = {
        'xuhao': 'Xh',
        'shangpin_mingcheng': 'Spmc',
        'guigexinghao': 'Ggxh',
        'jiliangdanwei': 'Jldw',
        'shangpin_bianma': 'Spbm',
        'shuliang': 'Sl',
        'danjia': 'Dj',
        'shuilv': 'Slv',  # 税率 eg: 0.05
        'kouchue': 'Kce',
        'qiye_shangpinbianma': 'Qyspbm',
        'syyhzcbz': 'Syyhzcbz',
        'lingshuilvbiaozhi': 'Lslbz',
        'youhuizhengceshuoming': 'Yhzcsm'
    }

    # 必须提供的键名
    REQUIRED_KEYS = [
        'xuhao',
        'shangpin_mingcheng',
        'shangpin_bianma',
        'shuliang',
        'danjia',
    ]

    CALCULATED_KEYS = {
        'jine': 'Je',
    }

    TYPE_MAP = {
        'shuliang': float,
        'danjia': float,
    }

    def __init__(self, is_contain_tax,**kwargs):
        for k in self.LABEL_MAP:
            setattr(self, k, kwargs.get(k, None))

        # verify required value is not empty
        for k in self.REQUIRED_KEYS:
            if getattr(self, k) is None:
                raise ValueError('商品信息数据错误： {} 键名 <{}> 是必填项, 但是空值'.format(
                    getattr(self, 'shangpin_mingcheng', 'Empty client_name'), COL_NAME_MAP[k]))

        # transform init value type
        self._transform_init_value_type()

        # init jine
        self.jine = None

        # call calculate
        self.calculate(is_contain_tax)

    def _transform_init_value_type(self):
        for k, v in self.TYPE_MAP.items():
            input_value = getattr(self, k, None)
            if input_value is not None:
                setattr(self, k, v(input_value))

    def calculate(self, is_contain_tax):
        """
        Returns:
            float
        """
        # adjust danjia
        if is_contain_tax == 1:
            self.danjia = round(self.danjia / (1 + self.shuilv), PRICE_NDIGITS)

        # calculate total price
        self.jine = self.shuliang * self.danjia

    def to_xml_format_list(self):
        result = []
        for k, transformed_key in dict(collections.ChainMap(self.LABEL_MAP, self.CALCULATED_KEYS)).items():
            value = getattr(self, k, None)

            # parse shangpin_bianma to 19 digits
            if k == 'shangpin_bianma':
                value = int(str(value).ljust(19, '0'))

            if value is not None:
                result.append((transformed_key, str(value)))
            else:
                result.append((transformed_key, None))

        return result


class InvoiceItem(object):
    def __init__(self, invoice_number, invoice_info_object, invoice_good_objects):
        """
        Args:
            invoice_info_object:
            invoice_good_objects (list):
        """
        self.invoice_number = invoice_number
        self.invoice_info_object = invoice_info_object
        self.invoice_good_objects = invoice_good_objects


def create_invoice_item_info(data):
    """
    data 只包含一张单据的信息， 第一行行为购方信息
    Args:
        data (pd.DataFrame):

    Returns:
    """
    invoice_item_info_data = {k: transform_nan_to_none(pd.unique(data[COL_NAME_MAP[k]])[0]) for k in
                              InvoiceItemInfo.LABEL_MAP.keys()}
    return InvoiceItemInfo(get_danjuhao(data), **invoice_item_info_data)


def create_invoice_item_good_detail(data):
    """
    data 只包含一张单据的信息
    Args:
        data (pd.DataFrame):

    Returns:
    """
    result = []
    is_contain_tax = get_hanshuibiaoji(data)
    for i, row in data.iterrows():
        good_detail_data = {k: transform_nan_to_none(row[COL_NAME_MAP[k]]) for k in
                            InvoiceItemGoodDetail.LABEL_MAP.keys()}
        result.append(InvoiceItemGoodDetail(is_contain_tax, **good_detail_data))
    return result


def create_invoice_object(data):
    """
    data 只包含一张单据的信息
    Args:
        data (pd.DataFrame):

    Returns:
    """
    return InvoiceItem(
        invoice_number=get_danjuhao(data),
        invoice_info_object=create_invoice_item_info(data),
        invoice_good_objects=create_invoice_item_good_detail(data)
    )


"""
construct xml tree function
"""
def set_xml_node_text(node, value):
    node.text = value


def construct_sph(invoice_object, parent_node):
    """
    parent node: Fp

    Args:
        invoice_object (InvoiceItem):
        parent_node:

    Returns:

    """
    _Spxx = ET.SubElement(parent_node, 'Spxx')
    for good_obj in invoice_object.invoice_good_objects:
        _sph = ET.SubElement(_Spxx, 'Sph')
        [set_xml_node_text(ET.SubElement(_sph, key), value) for key, value in good_obj.to_xml_format_list()]


def construct_fp(object_list, parent_node):
    """
    parent node: Fpsj
    Args:
        object_list:
        parent_node:

    Returns:

    """
    for i in range(len(object_list)):
        obj = object_list[i]

        _info = obj.invoice_info_object
        _fp_node = ET.SubElement(parent_node, 'Fp')

        # write Djh node
        ET.SubElement(_fp_node, 'Djh').text = str(i + 1)

        # construct invoice info part
        [set_xml_node_text(ET.SubElement(_fp_node, key), value) for key, value in _info.to_xml_format_list()]

        # constuct invoice good part
        construct_sph(obj, _fp_node)


def construct_xml_tree(object_list):
    root_kp = ET.Element('Kp')
    ET.SubElement(root_kp, 'Version').text = INTERFACE_VERSION  # version info
    n_fpxx = ET.SubElement(root_kp, 'Fpxx')
    ET.SubElement(n_fpxx, 'Zsl').text = str(len(object_list))  # total number of invoice
    n_fpsj = ET.SubElement(n_fpxx, 'Fpsj')

    # XML item Fp
    construct_fp(object_list, n_fpsj)
    return root_kp


"""
excel template defination
"""
COL_NAME_MAP = {
    'danjuhao': '单据号',
    'goufang_mingcheng': '购方名称',
    'goufang_shuihao': '购方税号',
    'goufang_dizhidianhua': '购方地址电话',
    'goufang_yinhangzhanghao': '购方银行账号',
    'beizhu': '备注',
    'fuheren': '复核人',
    'shoukuanren': '收款人',
    'shangpinbianmabanbenhao': '商品编码版本号',
    'hanshuibiaoji': '含税标志',
    'xuhao': '序号',
    'shangpin_mingcheng': '商品名称',
    'guigexinghao': '规格型号',
    'jiliangdanwei': '计量单位',
    'shangpin_bianma': '商品编码',
    'shuliang': '数量',
    'danjia': '单价',
    'jine': '金额',
    'shuilv': '税率',
    # 'shuie': '税额', # 结果中不是没有出现吗？？？
    'kouchue': '扣除额',
    'qiye_shangpinbianma': '企业商品自编码',
    'syyhzcbz': '优惠政策标识',
    'lingshuilvbiaozhi': '零税率标识',
    'youhuizhengceshuoming': '优惠政策说明',
}


"""
excel data handler function
"""
def groupby_invoice_id(data):
    """

    Args:
        data (pd.DataFrame):

    Returns:

    """
    invoice_id_col_name = COL_NAME_MAP['danjuhao']
    gb = data.groupby(invoice_id_col_name)
    return [gb.get_group(x) for x in gb.groups]

def transform_human_readable_mark(data):
    transform_map = {
        'hanshuibiaoji': {'含税': 1, '不含税': 0, '差额税': 2},
        'syyhzcbz': {'不使用': 0, '使用': 1},
        'lingshuilvbiaozhi': {},  # TODO
    }

    for col, tmap in transform_map.items():
        data[COL_NAME_MAP[col]].replace(tmap, inplace=True)

    return data


def transform_client_info(data):
    """
    使用单据中信息非空值补全同一单据中所有行的信息
    Args:
        data:

    Returns:

    """
    pass


def verify_client_info_unique(data):
    """
    输入数据应属于同一单据
    Args:
        data (pd.DataFrame):

    Returns:

    """
    def _verify(data, col_name):
        s = pd.unique(data[COL_NAME_MAP[col_name]])
        s = s[pd.notnull(s)]
        assert len(s) == 1, \
            '单据号{}数据错误: 列 {} 数值不唯一(或缺少数据) 共有{}个数据'.format(get_danjuhao(data), COL_NAME_MAP[col_name], len(s))

    [_verify(data, i) for i in [
        'goufang_mingcheng',
        'goufang_shuihao',
        # 'goufang_dizhidianhua',
        # 'goufang_yinhangzhanghao',
        # 'beizhu',
        # 'fuheren',
        # 'shoukuanren',
        'shangpinbianmabanbenhao',
        'hanshuibiaoji'
    ]]

def get_danjuhao(data):
    """
    输入数据应属于同一单据
    Args:
        data (pd.DataFrame):

    Returns:
    """
    return data[COL_NAME_MAP['danjuhao']].values[0]

# def get_goufang_mingcheng(data):
#     """
#     输入数据应属于同一单据
#     Args:
#         data (pd.DataFrame):
#
#     Returns:
#     """
#     return data[COL_NAME_MAP['goufang_mingcheng']].values[0]
#
# def get_goufang_shuihao(data):
#     """
#     输入数据应属于同一单据
#     Args:
#         data (pd.DataFrame):
#
#     Returns:
#     """
#     return data[COL_NAME_MAP['goufang_shuihao']].values[0]
#
# def get_goufang_dizhidianhua(data):
#     """
#     输入数据应属于同一单据
#     Args:
#         data (pd.DataFrame):
#
#     Returns:
#     """
#     return data[COL_NAME_MAP['goufang_dizhidianhua']].values[0]
#
# def get_goufang_yinhangzhanghao(data):
#     """
#     输入数据应属于同一单据
#     Args:
#         data (pd.DataFrame):
#
#     Returns:
#     """
#     return data[COL_NAME_MAP['goufang_yinhangzhanghao']].values[0]
#
# def get_beizhu(data):
#     """
#     输入数据应属于同一单据
#     Args:
#         data (pd.DataFrame):
#
#     Returns:
#     """
#     return data[COL_NAME_MAP['beizhu']].values[0]
#
# def get_fuheren(data):
#     """
#     输入数据应属于同一单据
#     Args:
#         data (pd.DataFrame):
#
#     Returns:
#     """
#     return data[COL_NAME_MAP['fuheren']].values[0]
#
# def get_shoukuanren(data):
#     """
#     输入数据应属于同一单据
#     Args:
#         data (pd.DataFrame):
#
#     Returns:
#     """
#     return data[COL_NAME_MAP['shoukuanren']].values[0]
#
# def get_shangpinbianma(data):
#     """
#     输入数据应属于同一单据
#     Args:
#         data (pd.DataFrame):
#
#     Returns:
#     """
#     return data[COL_NAME_MAP['shangpinmianmabanbenhao']].values[0]
#
def get_hanshuibiaoji(data):
    """
    输入数据应属于同一单据
    Args:
        data (pd.DataFrame):

    Returns:
    """
    return data[COL_NAME_MAP['hanshuibiaoji']].values[0]
"""
output function
"""



"""
top level function
"""
def read_excel(file_name):
    df = pd.read_excel(file_name)

    # transform value
    df = transform_human_readable_mark(df)
    return df

def slice_data_by_invoice_id(data):
    sliced_data = groupby_invoice_id(data)
    return sliced_data

def main(input_file_name, output_file_name, verify_input=True):
    df = read_excel(input_file_name)
    sliced_data = slice_data_by_invoice_id(df)
    # verify data
    if verify_input is True:
        [verify_client_info_unique(x) for x in sliced_data]
    object_list = [create_invoice_object(d) for d in sliced_data]
    xml_root = construct_xml_tree(object_list)
    with open(output_file_name, 'wb') as fp:
        fp.write(ET.tostring(xml_root, 'gbk'))

"""
shell helper function
"""

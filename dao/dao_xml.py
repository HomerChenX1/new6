""" Support XML access
"""

#import python libraries
from typing import List
import xml.etree.ElementTree as ET
from xml.dom import minidom

#import third party libraries

#import yourself libraries
from bases.def_etf import EtfConf
from dao.dao_file import DaoFile

#constant definition
# global_variable


class DaoXml(DaoFile):
    """For XML operation
    """
    def __init__(self,
                 fname: str,
                 enc_str: str = "cp950",
                 mod_str: str = 'r+') -> None:
        super().__init__(fname, enc_str, mod_str)
        self.tree: ET.ElementTree  #type ignore
        self.root: ET.Element  #type ignore

    def read_file(self) -> None:
        """Read a XML file
        """
        with open(self.fname, "r", encoding=self.enc_str) as xmlfile:
            self.root = ET.fromstring(xmlfile.read())

    def write_file(self, pretty: bool = True) -> None:
        """Write XML file from self.root

        :param pretty: is pretty print, defaults to True
        :type pretty: bool, optional
        """
        if pretty:
            xmlstr = minidom.parseString(ET.tostring(self.root)).toprettyxml(
                indent="    ", newl="\r\n", encoding=self.enc_str)
            with open(self.fname, "wb") as f_handle:
                f_handle.write(xmlstr)
        else:
            self.tree = ET.ElementTree(self.root)
            self.tree.write(self.fname,
                            encoding=self.enc_str,
                            xml_declaration=True)

    def setup_root(self,
                   etf_list: List[EtfConf],
                   root_tag: str = "config") -> None:
        """Setup a root element for tree (self.root) from etf_dict

        :param etf_dict: data of etfs in config file
        :type etf_dict: Dict[str, EtfConf]
        :param root_tag: _description_, defaults to "config"
        :type root_tag: str, optional
        """
        self.root = ET.Element(root_tag)
        for etf in etf_list:
            etf_element = ET.SubElement(self.root, "etf")
            etf_element.attrib["symbol"] = etf.symbol
            etf_element.attrib["type"] = etf.etf_type
            etf_element.attrib["name"] = etf.cname

    def set_etfs(self, etf_list: List[EtfConf]) -> None:
        """Fill etf_dict from self.root

        :param etf_dict: a dictionary within etf conf data
        :type etf_dict: Dict[str, EtfConf]
        """
        for child in self.root:
            if child.tag == "etf":
                etf_list.append(EtfConf(
                    child.attrib["type"], child.attrib["symbol"],
                    child.attrib["name"],
                    bool(child.attrib.get("disabled", False)),
                    child.attrib.get("notes", "")))
        # for debug
        # for etf in etf_dict.keys():
        #     print(etf_dict[etf])


#main function  將最高層的function以兩個空白行分隔
if __name__ == '__main__':
    # for Windows system
    etf_test = EtfConf("B", "AGG", "美洲美國債券_1L", True, "good")
    print(etf_test)

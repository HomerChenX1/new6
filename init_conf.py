"""Process the config.xml or config.csv file
"""

#import python libraries
from typing import List, Dict, Optional
from typing_extensions import Self

#import third party libraries

#import yourself libraries
from bases.conf import Cf
from bases.def_etf import EtfConf
from bases.intf_method import IMethod
from dao.dao_csv import DaoCsv
from dao.dao_xml import DaoXml

#constant definition
# global_variable


class InitConf(IMethod):
    """Process the config.xml or config.csv file

    :param DaoXml: process the XML file
    :type DaoXml: DaoXML
    """
    all_etfs: List[EtfConf] = []  #type ignore
    etf_symbol_list: List[str] = []  #type ignore

    def __init__(self, cf: Cf) -> None:
        super().__init__("InitConf", cf, None)# type: ignore
        self.csv_fname: str = "config.csv"
        self.xml_fname: str = "config.xml"
        self.csv_symbol_fname: str = "symbols.txt"
        self.csv_ex_types: List[str] = ["L", "R", "C", "I", "F"]
        self.csv_ex_dict: Dict[str, list] = {}
        self.need_write_xml: bool = False

    def __write_xml(self) -> None:
        """write all_etfs to XML file
        """
        dao_xml = DaoXml(self.xml_fname)
        dao_xml.setup_root(self.all_etfs)
        dao_xml.write_file()

    def __check_unique(self, etfs: List[EtfConf]) -> None:
        # check symbol/cname unique
        duplicate_list: List[str] = []
        checked_list: List[str] = []
        # unique_etfs: List[EtfConf]=[]

        for etf in etfs:
            if (etf.symbol not in checked_list) and (etf.cname
                                                     not in checked_list):
                # make etf to all_etfs
                # self.all_etfs.append(etf)
                # unique_etfs.append(etf)
                checked_list += [etf.symbol, etf.cname]
            else:
                duplicate_list.append(etf.symbol + "/" + etf.cname)
        if len(duplicate_list) != 0:
            self.print_msg("重複的 symbol 或 cname: " + ", ".join(duplicate_list),
                           False, "error")
            raise NotImplementedError

    def __parse_csv(self) -> None:
        rows = DaoCsv(self.csv_fname).read_all()
        self.csv_ex_dict.update({
            a_type: [row for row in rows if row[0] == a_type]
            for a_type in self.csv_ex_types
        })
        etfs = [
            EtfConf(row[0], row[2], row[1], False, "") for row in rows
            if row[0] not in self.csv_ex_types
        ]
        self.all_etfs += etfs

    def __parse_xml(self, dao_xml: DaoXml) -> None:
        dao_xml.read_file()
        dao_xml.set_etfs(self.all_etfs)

    def post_init_load(self,
                       o_etf: Optional[EtfConf] = None) -> Optional[Self]:
        if super().post_init_load(o_etf) is None:  #type: ignore
            return None
        dao_xml = DaoXml(self.xml_fname)
        if dao_xml.is_exist():
            #test OK
            self.__parse_xml(dao_xml)
            return self

        dao_csv = DaoCsv(self.csv_fname)
        if dao_csv.is_exist():
            self.__parse_csv()
            self.need_write_xml = True
        else:
            #test OK
            self.print_msg(self.csv_fname + " 檔案不存在。", False, "error")
            raise NotImplementedError
        return self

    def calc(self) -> Optional[Self]:
        if super().calc() is None:
            return None
        self.__check_unique(self.all_etfs)
        return self

    def store(self) -> Optional[Self]:
        if super().store() is None:
            return None
        if self.need_write_xml:
            self.__write_xml()
        # create symbol.txt
        self.etf_symbol_list += [
            etf.symbol for etf in self.all_etfs if not etf.disabled
        ]
        DaoCsv("symbols.txt").write_symbols(self.etf_symbol_list)
        return self

    def proc_all(self) -> Optional[Self]:
        return self.post_init_load().calc().store()  #type: ignore


if __name__ == '__main__':
    # setup Cf
    cf_main = Cf()
    cf_main.post_init_only_main()
    cf_main.logger.log_info("InitConf test!!")
    init_configure: InitConf = InitConf(cf_main)
    init_configure.proc_all()
    for etf_item in init_configure.all_etfs:
        print(etf_item)

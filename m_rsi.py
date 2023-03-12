"""For the method LT
"""
#import python libraries
from typing import Optional
from typing_extensions import Self

#import third party libraries

#import yourself libraries
from bases.conf import Cf
from bases.def_etf import EtfCalc
from bases.intf_method import IMethod
from dao.dao_sql import DaoDb
from m_etf_load import EtfLoad
#constant definition
#global_variable

#main function  將最高層的function以兩個空白行分隔

class Rsi(IMethod):
    """For long term calculation. Used for long term trendency
    """
    def __init__(self, cf: Cf, dao_db:DaoDb) -> None:
        super().__init__("Rsi", cf, dao_db)

    def post_init_load(self, o_etf: Optional[EtfCalc] = None) -> Optional[Self]:
        if super().post_init_load(o_etf) is None:
            return None

        return self


if __name__ == '__main__':
    # setup Cf for logger
    cf_main = Cf()
    cf_main.post_init_only_main()
    cf_main.logger.log_info("InitConf test!!")
    #setup EtfLoad
    etf_load = EtfLoad(cf_main)
    obj_etf = EtfCalc()
    etf_load.post_init_load(obj_etf)
    if etf_load.csv_data[0][0] != '2009/03/17':
        print("the last date is incorrect!")
    if len(etf_load.csv_data) != 12385:
        print("the len of data file is incorrect!")
    etf_load.calc()
    if len(etf_load.csv_data) != 12377:
        print("the len2 of data file is incorrect!")
    etf_load.store()
    m_lt = Rsi(cf_main, etf_load.dao_db)
    #TODO: test LT here
    m_lt.post_init_load(obj_etf)

    etf_load.on_destroy()

"""For the method LT
"""
#import python libraries
from typing import Optional
from typing_extensions import Self

#import third party libraries

#import yourself libraries
from bases.conf import Cf
from bases.conf_func import _chk_almost
from bases.def_etf import EtfCalc
from bases.intf_method import RsiSave
from dao.dao_sql import DaoDb
from m_etf_load import EtfLoad
from m_lt import Lt
#constant definition
#global_variable


class Rsi(Lt, RsiSave ):
    """For long term calculation. Used for long term trendency
    """
    def __init__(self, cf: Cf, dao_db: DaoDb) -> None:
        Lt.__init__(self, cf, dao_db)
        self.alias = 'Rsi'
        RsiSave.__init__(self)
        print(vars(self))

    def post_init_load(self,
                       o_etf: Optional[EtfCalc] = None) -> Optional[Self]:
        Lt.post_init_load(self, o_etf)
        return self

    def prepare_calc(self) -> Self:
        return super().prepare_calc()

    def _calc(self) -> Optional[Self]:
        return super()._calc()

    def mix_lt_indicator(self):
        return super().mix_lt_indicator()


def test_rsi(obj_cf: Cf, dao_db: DaoDb, etf: EtfCalc) -> None:
    """Test Rsi module

    :param obj_cf: common configuration
    :type obj_cf: Cf
    :param dao_db: Database
    :type dao_db: DaoDb
    :param etf: Accmulated result data
    :type etf: EtfCalc
    """
    m_rsi = Rsi(obj_cf, dao_db)
    m_rsi.post_init_load(etf)
    print(m_rsi)
    # m_rsi.training_flag = True
    # m_rsi.prepare_training().training()
    m_rsi.training_flag = False
    m_rsi.calc()
    # m_rsi.store()  # store m_eval
    return


#main function  將最高層的function以兩個空白行分隔
if __name__ == '__main__':
    # setup Cf for logger
    cf_main = Cf()
    cf_main.post_init_only_main()
    cf_main.logger.log_info("InitConf test!!")
    #setup EtfLoad
    etf_load = EtfLoad(cf_main)
    obj_etf = EtfCalc()
    etf_load.dao_db.row_add_to_dbconf(obj_etf)
    etf_load.post_init_load(obj_etf)
    if etf_load.csv_data[0][0] != '2009/03/17':
        print("the last date is incorrect!")
    if len(etf_load.csv_data) != 12385:
        print("the len of data file is incorrect!")
    etf_load.calc()
    if len(etf_load.csv_data) != 12377:
        print("the len2 of data file is incorrect!")
    etf_load.store()

    m_lt = Lt(cf_main, etf_load.dao_db)
    m_lt.post_init_load(obj_etf)
    m_lt.training_flag = False
    m_lt.calc()
    test_result = [
        m_lt.filt_long == 259, m_lt.filt_short == 30, m_lt.only_buy == 1
    ]
    assert all(test_result), "training fail 3"
    if not _chk_almost(m_lt.o_eval.avg_profit_yr, 0.0907279, 0.0001):
        print("training fail 4!")
    # store self.only_buy and filter parameter to LtSave if training
    # LT_DRAW=False
    # m_lt.store()  # store m_eval

    # test_rsi(cf_main, etf_load.dao_db, obj_etf)
    # last call to write SQL
    etf_load.on_destroy()

""" Definitions of Etf classes
Reference:
    dataclass :
        https://www.maxlist.xyz/2022/04/30/python-dataclasses/
    numpy typing :
        https://numpy.org/doc/stable/reference/typing.html?highlight=data%20type%20api
"""

#import python libraries
#from typing import Optional
#from typing_extensions import Self

#import third party libraries
import numpy as np
import numpy.typing as ntp

#import yourself libraries
#constant definition
# global_variable


class EtfConf():
    """ Used for basic config.xml data
    """
    def __init__(self, etf_type: str, symbol: str, cname: str, disabled: bool,
                 notes: str) -> None:
        """Items from config.xml

        :param etf_type: stock/bond/currency
        :type etf_type: str
        :param symbol: ticket name for Yahoo Finance
        :type symbol: str
        :param cname: chinese name for symbol which I named
        :type cname: str
        """
        self.symbol: str = symbol  # 符號, ok
        self.etf_type: str = etf_type  # ok
        self.cname: str = cname  # 中文名稱, ok
        self.hash_id: int = 0  # major key, read-only
        self.notes: str = notes  # 附註
        # in XML file "XXX" mean True, "" mean False
        self.disabled: bool = disabled  # the ticket is enabled

    def __repr__(self) -> str:
        return "Etf symbol:" + self.symbol + ", cname:" + self.cname + \
            ", type:" + self.etf_type + ", dis:"+ str(self.disabled) + ", notes:" + self.notes


class EtfView():
    """items in EtfInfoRow , need to change to data class

    :param EtfConf: 繼承 for config.csv or config.xml
    :type EtfConf: _type_
    """
    def __init__(self) -> None:
        self.nav: float = 0  # 輸出報表用
        self.nav_chg: float = 0  # 輸出報表用
        self.nav_date: str = ""  # 輸出報表用
        self.sell_price: float = 0  # 賣價
        self.buy_price: float = 0  # 買價
        self.max_shares: int = -1  # 買賣最多股數, 和流動性有關 and error_no
        self.atr: float = 0  # ATR
        self.op_ratio: float = 0  # # 建議買賣最多股數
        self.rank: float = 0  # 短期 排名
        self.issued: str = ""


class MthdView():
    """Store the result of methods' calculation
    """
    def __init__(self) -> None:
        self.m_rank: float = -1
        #self.curr_mrkt: int = 1
        self.day_ago: int = -1
        self.day_ago_dec: int = -2
        self.day_ago_nav: float = -1
        self.hold_day_avg: float =-1
        self.odd: float = -1
        self.cnt_profit: int = -1
        self.kelly: float = -1
        self.avg_profit_yr: float = -1
        self.loan: bool = True
        self.track: bool = False
        self.min_shares: int = 0
        self.op_ratio: float = -1
        self.tot_profit: float = -1
        self.sharpe: float = -1


class EtfCsv():
    """ ETF data reading from CSV
    """
    def __init__(self) -> None:  # class中的function用一個空白行分隔
        self.date: ntp.ArrayLike = np.array(['2001/05/08'], dtype=str)  # ok
        self.open: ntp.ArrayLike = np.array([0, 1, 2], dtype=float)  # ok
        self.high: ntp.ArrayLike = np.array([0, 1, 2], dtype=float)  # ok
        self.low: ntp.ArrayLike = np.array([0, 1, 2], dtype=float)  # ok
        self.close: ntp.ArrayLike = np.array([0, 1, 2], dtype=float)  # ok
        self.volume: ntp.ArrayLike = np.array([0, 1, 2], dtype=float)  # ok


class EtfCalc(EtfConf, EtfView, EtfCsv):
    """Used for caiculation
    """

    # for RSI MACD KD used
    lt_indicator = np.array([0, 1, 2], dtype=int)
    lt_hold_day_avg:float = 0

    def __init__(self) -> None:
        #copy initializer for EtfConf
        EtfConf.__init__(self, "X", "^GSPC_tst", "S&P500tst_idx", False,
                         "Test")
        EtfView.__init__(self)
        EtfCsv.__init__(self)
        self.hash_id = 246
        self.training_flag: bool = True

    def copy_from(self, o_etf: EtfConf, reverse: bool = False):
        """Copy items of o_etf to current items

        :param o_etf: input data
        :type o_etf: EtfConf
        :param reverse: copy_from or copy_to
        :type reverse: bool, optional
        """
        if reverse:
            # copy to
            _ = [
                setattr(o_etf, x_name, getattr(self, x_name))
                for x_name in vars(self)
            ]
        else:
            #copy from
            _ = [
                setattr(self, x_name, getattr(o_etf, x_name))
                for x_name in vars(o_etf)
            ]

    def __repr__(self) -> str:
        return "EtfCalc symbol:" + self.symbol + ", cname:" + self.cname + ", id:" + str(
            self.hash_id) + ", type:" + self.etf_type + ", dis:" + str(
                self.disabled) + ", notes:" + self.notes


if __name__ == '__main__':
    dao = EtfCalc()
    print(dao)
    obj_etf = EtfConf("X", "^TYX", "美30年債殖利率_idx", False, "")
    obj_etf.hash_id = 256
    dao.copy_from(obj_etf, True)
    print(obj_etf)

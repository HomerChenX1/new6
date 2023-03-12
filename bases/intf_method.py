"""Interface of the methods
"""

#import python libraries
from typing import Optional, List
from typing_extensions import Self

#import third party libraries

#import yourself libraries
from bases.conf import Cf, ConfErrorNo
from bases.def_etf import EtfCalc
from dao.dao_sql import DaoDb

#constant definition
FILT_LONG: int = 276
FILT_SHORT: int = 27
# global_variable

class IMethod():
    """Interface used in the debugging of the __main__
    """
    def __init__(self, alias: str, cf: Cf, dao_db:DaoDb) -> None:
        # self.o_cf is singleton
        self.o_cf: Cf = cf  #type: ignore
        self.alias: str = alias
        self.err_no: int = ConfErrorNo.NO_ERR
        self.err_msg: str = ""
        # self.o_etf is singleton
        self.o_etf: Optional[EtfCalc] = None
        self.dao_db:DaoDb=dao_db

    def post_init_load(self,
                       o_etf: Optional[EtfCalc] = None) -> Optional[Self]:
        """ post init, execute the following things:
        1. pre-condition stage 1 : check parameters from __init__
        2. load the necessary data
        3. pre-condition stage 2 : check the loaded data

        :return: self for success, None for failure.
        :rtype: Optional[Self]
        """
        if (self.o_etf is None) and (o_etf is not None):
            self.o_etf = o_etf
        return self

    def calc(self) -> Optional[Self]:
        """processing all data

        :return: self for success, None for failure.
        :rtype: Optional[Self]
        """
        # raise NotImplementedError
        return self

    def store(self) -> Optional[Self]:
        """Store all results

        :return: self for success, None for failure.
        :rtype: Optional[Self]
        """
        #raise NotImplementedError
        return self

    def on_destroy(self) -> Optional[Self]:
        """destructor

        :return: self for success, None for failure.
        :rtype: Optional[Self]
        """
        #raise NotImplementedError
        return self

    def proc_all(self) -> Optional[Self]:
        """processing all data

        :return: self for success, None for failure.
        :rtype: Optional[Self]
        """
        # raise NotImplementedError
        return self.post_init_load().calc().store().on_destroy()  #type: ignore

    def set_err_no(self,
                   err_no: int = ConfErrorNo.NO_ERR,
                   err_msg: str = "") -> Self:
        """error setter

        :param err_no: error number in ConfErrorNo
        :type err_no: int
        """
        self.err_no = err_no
        self.err_msg = err_msg
        return self

    def print_error(self, msg: str, is_html: bool = False) -> None:
        """program suger for print_msg, default is error

        :param msg: text of message
        :type msg: str
        :param is_html: Is the style of msg HTML, defaults to False
        :type is_html: bool, optional
        """
        self.print_msg(msg, is_html, "error")

    def print_msg(self,
                  msg: str,
                  is_html: bool = False,
                  log_type: str = "info") -> None:
        """log error message
        log format : alias:err_no:err_msg
        log method format:symbol:alias:err_no:err_msg

        :param msg: text of message
        :type msg: str
        :param is_html: Is the style of msg HTML, defaults to False
        :type is_html: bool, optional
        :param log_type: the type of log in conf_log.py, defaults to "info"
        :type log_type: str, optional
        """
        msg_list: List[str] = []
        if is_html:
            msg_list.append(msg)
        else:
            # the msg is text
            if self.o_etf is not None:
                msg_list.append(self.o_etf.symbol)
            msg_list.append(self.alias)
            if self.err_no != ConfErrorNo.NO_ERR:
                msg_list.append(str(self.err_no))
                msg_list.append(self.err_msg)
            if msg:
                msg_list.append(msg)

        self.o_cf.logger.log_msg(log_type, ":".join(msg_list), is_html)

    def _check_result(self, expr: bool, msg: str) -> None:
        """Use assert to debug

        :param expr: check condition
        :type expr: bool
        :param msg: text message if False
        :type msg: str
        """
        assert expr, msg

    def _check_result_almost(self, result: float, tol: float,
                             msg: str) -> None:
        """Check almost error

        :param result: result
        :type result: float
        :param tol: tolence
        :type tol: float
        :param msg: error msg if result > tol
        :type msg: str
        """
        assert abs(result) < abs(tol), msg

class LtSave():
    """Lt class mapped to Db
    """
    def __init__(self) -> None:
        self.filt_long: int = FILT_LONG
        self.filt_short: int = FILT_SHORT
        self.only_buy: int = 0  #0x1: buy, 0x2:sell

    def __repr__(self) -> str:
        return f"filter long:{self.filt_long} short:{self.filt_short} type:{self.only_buy}"


class RsiSave(LtSave):
    """RSI class mapped to Db
    """
    def __init__(self) -> None:
        super().__init__()
        self.thd_high: float = 0.85
        self.thd_low: float = 0.3

    def __repr__(self) -> str:
        return f"filter long:{self.filt_long} short:{self.filt_short} type:{self.only_buy} thd:{self.thd_high:4}/{self.thd_low:4}"


class MdSave(LtSave):
    """MACD class mapped to Db
    """
    def __init__(self) -> None:
        super().__init__()
        self.filt_dif: int = 5

    def __repr__(self) -> str:
        return f"filter long:{self.filt_long} short:{self.filt_short} dif:{self.filt_dif} type:{self.only_buy}"


class KdSave(RsiSave):
    """KD class mapped to Db
    """
    def __init__(self) -> None:
        super().__init__()
        self.filt_rsv: int = 25

    def __repr__(self) -> str:
        return f"filter long:{self.filt_long} short:{self.filt_short} rsv:{self.filt_rsv} type:{self.only_buy} thd:{self.thd_high:4}/{self.thd_low:4}"


METHODS_MAP: dict = {
    "Lt": LtSave,
    "Rsi": RsiSave,
    "Md": MdSave,
    "Kd": KdSave
}

#main function  將最高層的function以兩個空白行分隔
if __name__ == '__main__':
    # setup Cf
    cf_main = Cf()
    cf_main.post_init_only_main()
    cf_main.logger.log_info("intf_method test!!")
    test_obj = IMethod("imain", cf_main, None)  #type:ignore
    test_obj.post_init_load()
    test_obj.set_err_no(ConfErrorNo.CSV_LEN_TOO_SHORT, "csv length too short")
    test_obj.print_msg("IMethod test")

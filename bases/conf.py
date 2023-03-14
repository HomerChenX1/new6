""" for Configure definitions
logger for main process:
    cf.post_init_only_main()
logger for multi-process:
    cf.post_init(log_queue,sql_lock)
"""

#import python libraries
# from typing import Optional
from datetime import date
from multiprocessing import Queue, Lock

#import third party libraries

#import yourself libraries
from bases.conf_const import ConfConst
from bases.conf_func import ConfFunc
from bases.conf_log import ConfLog, ConfLogServ

#constant definition

# global_variable


class ConfErrorNo:
    """Assign the error nomber
    """
    NO_ERR: int = 0
    # etf error code
    CSV_NOT_FOUND: int = -1
    CSV_NO_CONTENT: int = -2
    CSV_LEN_TOO_SHORT: int = -3
    CSV_NOT_UPDATED: int = -4
    MAX_SHARES_TOO_SMALL: int = -5
    TOO_MANY_WRONG_DATA: int = -6
    # method error code
    NEED_TRAINING: int = -2
    VALUE_NOT_MATCH: int = -3
    LT_TRAINING_FAIL: int = -4
    STOP_LOSS_TRAINING_FAIL: int = -5
    NEED_NOT_TRAINING: int = -6
    #CURR_MRKT_NOT_MATCH: int = -7
    MIN_SHARES_TOO_SMALL: int = -5


class Cf(ConfConst, ConfErrorNo, ConfFunc):
    """ Aggression data

    :param ConfConst: _description_
    :type ConfConst: _type_
    :param ConfErrorNo: _description_
    :type ConfErrorNo: _type_
    """
    logger: ConfLog = None  # type: ignore
    sql_lock: Lock = None  # type: ignore

    def __init__(self) -> None:
        now = date.today()
        self.train_day_p: int = now.day % Cf.TRAINING_DAY
        self.bond_yield_30yr: float = 7.0
        self.bond_yield_1yr: float = 4.0

    def post_init(
            self,
            log_queue: Queue,
            a_lock: Lock = None,  # type: ignore
            is_forced: bool = False) -> None:
        """Setup logger

        :param log_queue: queue needed for logger
        :type log_queue: Queue
        """
        if self.logger is None or is_forced:
            self.logger = ConfLog(log_queue)  # type: ignore
        # else:
        #     self.logger = ConfLog(None) # type: ignore
        #     ConfLogServ.setup_log_system()
        self.sql_lock = a_lock

    def post_init_only_main(self) -> None:
        """ Use for main process testing
        """
        self.logger = ConfLog(None)  # type: ignore
        ConfLogServ.setup_log_system()


#main function  將最高層的function以兩個空白行分隔
if __name__ == '__main__':
    print("week ", Cf.WEEK_DAY, " year ", Cf.YEAR_DAY)
    cf = Cf()
    print(cf.MARKET_BEAR, cf.MARK_BUY)

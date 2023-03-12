"""the calculation for ETF
"""

#import python libraries
from datetime import date
from typing import Optional
from typing_extensions import Self

#import third party libraries
import numpy as np

#import yourself libraries
from bases.conf import Cf
from bases.conf_func import _chk_almost
from bases.def_etf import EtfCalc
from bases.intf_method import IMethod
from dao.dao_csv import DaoCsv
from dao.dao_sql import DaoDb

#constant definition
# global_variable


class EtfLoad(IMethod):
    """Load Etf csv data, verify, and calculate the EtfView.
       Then store the data to Database
    """
    idx_date = 0
    idx_open = 1
    idx_high = 2
    idx_low = 3
    idx_close = 4
    idx_volume = 5

    def __init__(self, cf: Cf, dao_db:DaoDb=None) -> None:  #type:ignore
        """Basic constructor

        :param alias: class alias, normalize is class name
        :type alias: str
        :param cf: a Cf instance
        :type cf: Cf
        """
        if dao_db is None:
            dao_db = DaoDb()
        super().__init__("EtfLoad", cf, dao_db)
        # self.dao_db = DaoDb()
        self.csv_data = []
        self.chk_err_cnt = 0

    def on_destroy(self) -> Optional[Self]:
        #stop SQL
        if self.o_cf.sql_lock:
            self.o_cf.sql_lock.acquire()

        a_obj=self.dao_db.on_destroy()

        if self.o_cf.sql_lock:
            self.o_cf.sql_lock.release()
        return a_obj

    def proc_all(self) -> Optional[Self]:
        return self.calc().store()  #type: ignore

    def post_init_load(self,
                       o_etf: Optional[EtfCalc] = None) -> Optional[Self]:
        """Load csv data and verify

        :param o_etf: the target. The field symbol is necessary.
        :type o_etf: Optional[EtfCalc], optional
        :return: self or None. None mean something wrong
        :rtype: Optional[Self]
        """
        # load csv
        super().post_init_load(o_etf)
        if self.o_etf and self.o_etf.symbol:
            fname: str = self.o_cf.DATA_DIR + self.o_etf.symbol + '.csv'  #type: ignore
            # print(fname)
            self.csv_data = DaoCsv(fname).read_all()
            self.csv_data.sort(reverse=True)
            if (self.csv_data is None) or (len(self.csv_data) == 0):
                self.set_err_no(
                    self.o_cf.CSV_NO_CONTENT,
                    "CSV_NO_CONTENT or CSV_NOT_FOUND").print_error("")
                return None
            if len(self.csv_data) < self.o_cf.EtfLenLimit:
                self.set_err_no(self.o_cf.CSV_LEN_TOO_SHORT,
                                "CSV_LEN_TOO_SHORT").print_error("")
                return None
            self.chk_err_cnt = len(self.csv_data)
            # print("basic len:", str(self.chk_err_cnt))
            if not self._check_last_updated_date(self.csv_data[0][0]):
                return None
            # print("test 1 len:", str(len(self.csv_data)))
        else:
            self.print_error("no symbol assigned!")
            return None
        return self

    def calc(self) -> Optional[Self]:
        if not self._convert_data_and_check():
            return None
        if self.o_etf is None:
            return None
        # truncate if data length too long
        self.o_etf.issued = self.csv_data[-1][0]  #type ignore
        if (self.o_etf is not None) and (self.o_etf.symbol != "^GSPC_tst"):
            self.csv_data = self.csv_data[:self.o_cf.TRUNCATE_DAY]
        # else:  #for output debugging
        #     DaoCsv("test.csv").write_all(self.csv_data)
        # set to np:Array
        self._set_training_flag()
        return self

    def __set_atr_and_rank(self, is_abs: bool = False) -> None:
        """calculate the ATR and rank

        :param is_abs: self.atr is absolute value, defaults to False
                        if true ,self.atr is absolute value.
                            Mean use the absolute value and trends to low price stock
                        if false, self.atr use 3M averaged ATR
        :type is_abs: bool, optional
        """
        if self.o_etf is None:
            return
        t_day = min(
            len(self.o_etf.close),  #type: ignore
            self.o_cf.SEASON_DAY)  # type: ignore
        x_atr: float = self.o_cf.ATR(self.o_etf.high, self.o_etf.low,
                                     self.o_etf.close,
                                     t_day)[0]  # type: ignore
        if not is_abs:
            self.o_etf.atr = x_atr
        else:
            #normalized rank
            a_val = np.average(self.o_etf.close[:t_day])  #type: ignore
            self.o_etf.atr = x_atr / a_val
        self.o_etf.rank = (
            self.o_etf.close[0] -  # type: ignore
            self.o_etf.close[t_day - 1]) / x_atr  # type: ignore
        # print(f"{is_abs} atr: {self.o_etf.atr}, rank:{self.o_etf.rank}")
        return

    def __set_max_shares(self) -> None:
        if self.o_etf is None:
            return
        interval = self.o_etf.volume[:self.o_cf.SEASON_DAY]  # type: ignore
        self.o_etf.max_shares = int(
            interval.min() / self.o_cf.SAFE_SHARE_DIVIDER)  # type: ignore

        if self.o_etf.max_shares < self.o_cf.MIN_BUY_SHARES and self.o_etf.etf_type != 'X':
            self.o_etf.max_shares = -1
            return

        if self.o_etf.max_shares > 0 and self.o_etf.etf_type == 'T':
            # for TW modify
            self.o_etf.max_shares *= self.o_cf.MOD_TW_SHARES
            # print(self.symbol+':for TW modify')
        return

    def __set_buy_sell_price(self) -> None:
        if self.o_etf is None:
            return
        avg_day = min(
            len(self.o_etf.close),  # type: ignore
            self.o_cf.SEASON_DAY)  # type: ignore
        a_buy = self.o_etf.low[:avg_day -  # type: ignore
                               1] / self.o_etf.close[  # type: ignore
                                   1:avg_day] - 1  #type: ignore
        a_buy.sort()
        a_sell = self.o_etf.high[:avg_day -  # type: ignore
                                 1] / self.o_etf.close[  # type: ignore
                                     1:avg_day] - 1  #type: ignore
        a_sell.sort()
        # print(a_sell)
        a_sell = a_sell[::-1]
        # print(a_sell)
        j = len(a_buy)
        k = int(round(j * self.o_cf.MAX_PRICE_RATIO))
        self.o_etf.buy_price = (
            1 + a_buy[k - 1]) * self.o_etf.close[0]  # type: ignore
        self.o_etf.sell_price = (
            1 + a_sell[k - 1]) * self.o_etf.close[0]  # type: ignore
        # print("sell 1:" + str((1 + a_sell[k-3]) * self.o_etf.close[0]))
        # print("sell 2:" + str((1 + a_sell[k-2]) * self.o_etf.close[0]))
        # print((1+a_sell[k - 4])* self.o_etf.close[0]) #type: ignore
        return

    def store(self) -> Optional[Self]:
        #calc EtfView
        if self.o_etf is None:
            return None
        self.o_etf.nav = self.o_etf.close[0]  # type: ignore
        self.o_etf.nav_date = self.o_etf.date[0]  # type: ignore

        self.o_etf.nav_chg = self.o_etf.close[  # type: ignore
            0] / self.o_etf.close[  # type: ignore
                1] - 1  # type: ignore
        self.__set_atr_and_rank()
        self.__set_max_shares()
        self.__set_buy_sell_price()
        #not calculate here
        # self.o_etf.max_op_ratio: int = 0  # # 建議買賣最多股數
        #save EtfView to dao_db
        self.update_db_etf_view()
        return self

    def update_db_etf_view(self) -> None:
        """Add lock to support MP

        :param o_etf: assigned Etf
        :type o_etf: EtfCalc
        """
        if self.o_cf.sql_lock:
            self.o_cf.sql_lock.acquire()
        self.dao_db.update_db_etf_view(self.o_etf)  #type: ignore
        if self.o_cf.sql_lock:
            self.o_cf.sql_lock.release()

    def _check_last_updated_date(self, last_date: str) -> bool:
        """Check the last updated date < 1 week

        :param last_date: last updated date
        :type last_date: str
        :return: if test pass, return True
        :rtype: bool
        """
        if self.o_etf is None:
            return False
        if self.o_etf.symbol == "^GSPC_tst":
            return True

        x_list = last_date.split('/')
        etf_day = date(int(x_list[0]), int(x_list[1]), int(x_list[2]))
        age = date.today() - etf_day
        # print self.lastDate, etf_day, age
        if (self.o_etf.etf_type == "T") or (self.o_etf.symbol=="^TWII"):
            update_limit = 2*self.o_cf.WEEK_DAY
        else:
            update_limit = self.o_cf.WEEK_DAY
        if age.days > update_limit:
            self.set_err_no(
                self.o_cf.CSV_NOT_UPDATED,
                "CSV_NOT_UPDATED").print_error("the csv file is not updated")
            return False
        return True

    def __check_prices(self):
        # check high>close>low and high>open>low
        cls = self.__class__
        result = []
        for item in self.csv_data:
            bool_1 = item[cls.idx_high] >= item[cls.idx_close] >= item[
                cls.idx_low]
            bool_2 = item[cls.idx_high] >= item[cls.idx_open] >= item[
                cls.idx_low]
            if bool_1 and bool_2:
                result.append(item)
            # else:
            #     print(item)
        self.csv_data = result
        return

    def __check_market_not_open(self):
        # cehck high low close the same value in the next day
        cls = self.__class__
        rmv_idx = []
        for idx in range(len(self.csv_data) - 1):
            bool_1 = self.csv_data[idx][cls.idx_close] == self.csv_data[
                idx + 1][cls.idx_close]
            bool_2 = self.csv_data[idx][cls.idx_high] == self.csv_data[
                idx + 1][cls.idx_high]
            bool_3 = self.csv_data[idx][cls.idx_low] == self.csv_data[idx + 1][
                cls.idx_low]
            if bool_1 and bool_2 and bool_3:
                rmv_idx.append(idx)
                continue
        self.csv_data = [
            item for idx, item in enumerate(self.csv_data)
            if idx not in rmv_idx
        ]
        # print(rmv_idx)
        return

    def _convert_data_and_check(self) -> bool:
        if self.o_etf is None:
            return False
        new_data = []
        # self.csv_data
        for row in self.csv_data:
            row_1 = [item.strip() for item in row]
            # row_1[0]="" #test "" OK
            if not all(row_1):
                continue
            row_part = [float(item) for item in row_1[1:]]
            # row_part[-1] = 0 #test 0 except volume OK
            row_part_x = row_part[:-1] if self.o_etf.etf_type == "X" else row_part
            if not all(row_part_x):
                continue
            new_data.append([row_1[0]] + row_part)
            # print(new_data)
        self.csv_data = new_data
        #check other error
        #print(f"_convert_data_and_check 1 : {len(self.csv_data)} ")
        self.__check_prices()
        #print(f"_convert_data_and_check 2 : {len(self.csv_data)} ")
        self.__check_market_not_open()
        #print(f"_convert_data_and_check 3 : {len(self.csv_data)} ")
        tol_len = self.chk_err_cnt
        self.chk_err_cnt -= len(self.csv_data)
        if (len(self.csv_data) < self.o_cf.EtfLenLimit) or (self.o_etf.etf_type !="T" and (self.chk_err_cnt > tol_len / 20)):
            self.set_err_no(self.o_cf.TOO_MANY_WRONG_DATA,
                            "TOO_MANY_WRONG_DATA").print_error(
                                f"wrong cnt: {self.chk_err_cnt} / {tol_len}")
            return False
        # print(f"_convert_data_and_check 4 : {len(self.csv_data)} ")
        self.o_etf.date = np.array(
            [item[self.idx_date] for item in self.csv_data], dtype=str)
        for idx, a_name_s in enumerate(
            ["open", "high", "low", "close", "volume"]):
            setattr(
                self.o_etf, a_name_s,
                np.array([item[idx + 1] for item in self.csv_data],
                         dtype=float))
        # for idx,a_name in enumerate(["date","open", "high", "low","close","volume"]):
        #     print(f"{a_name} {self.csv_data[0][idx]} {getattr(self.o_etf,a_name)[0]}")
        return True

    def _set_training_flag(self) -> None:
        if self.o_etf is None:
            return
        t_flag = self.o_etf.hash_id % self.o_cf.TRAINING_DAY
        self.o_etf.training_flag = (t_flag == self.o_cf.train_day_p)
        # self.print_error(f"training flag:{self.o_etf.training_flag} _id:{t_flag}, t_flag:{self.o_cf.train_day_p}")
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
    # need copy_from()
    # obj_etf_b = EtfConf("X", "^TYX", "美30年債殖利率_idx", False, "")
    # obj_etf_b.hash_id = 256
    # obj_etf.copy_from(obj_etf_b)
    #load csv : post_init_load
    etf_load.post_init_load(obj_etf)
    if etf_load.csv_data[0][0] != '2009/03/17':
        print("the last date is incorrect!")
    if len(etf_load.csv_data) != 12385:
        print("the len of data file is incorrect!")
    etf_load.calc()
    if len(etf_load.csv_data) != 12377:
        print("the len2 of data file is incorrect!")
    etf_load.store()
    # for a_name in [
    #         "last_nav", "last_change", "last_date", "sell_price", "buy_price",
    #         "max_shares", "atr", "max_op_ratio", "rank", "issued"
    # ]:
    #     print(a_name + ":" + str(getattr(etf_load.o_etf, a_name)))
    etf_load.on_destroy()

    if etf_load.o_etf is None:
        print("o_etf is None")
        exit()
    if not _chk_almost(etf_load.o_etf.nav, 778.12, 0.01):
        print("test last_nav: False!")
    if not _chk_almost(etf_load.o_etf.nav_chg, 0.0321399673692, 0.0001):
        print("test last_change: False!")
    if not _chk_almost(etf_load.o_etf.sell_price, 786.0017427439777, 0.0001):
        print(f"test sell_price: False:{etf_load.o_etf.sell_price}")
    if not _chk_almost(etf_load.o_etf.buy_price, 766.87880013, 0.0001):
        print("test buy_price: False!")
    if not _chk_almost(etf_load.o_etf.atr, 26.29153846153847, 0.0001):
        print("test atr: False!")
    if not _chk_almost(etf_load.o_etf.rank, -3.631206296263788, 0.0001):
        print(f"test rank: False:{etf_load.o_etf.rank}")
    if not _chk_almost(etf_load.o_etf.max_shares, 15465500.0, 0.1):
        print("test max_shares: False!")
    # for single process, do not need to stop logserver

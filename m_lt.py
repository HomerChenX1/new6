"""For the method LT
LT training 成功率
maxmanize
tot_profit I:success ratio: 0.78125
tot_profit*odd I:success ratio: 0.8671875 use it 0.9207547169811321
"""
#import python libraries
from typing import Any, Dict, Optional
from typing_extensions import Self

#import third party libraries
import numpy as np
from numpy.typing import ArrayLike

#import yourself libraries
from bases.conf import Cf
from bases.conf_func import _chk_almost
from bases.def_etf import EtfCalc
from bases.intf_method import METHODS_MAP, IMethod, LtSave
from dao.dao_plots import DaoPlots
from dao.dao_sql import DaoDb
from m_etf_load import EtfLoad
from m_eval import MthEval

#constant definition
MA_LT_MAX: int = 20 * Cf.MONTH_DAY
MA_MT_MAX: int = 6 * Cf.MONTH_DAY
MA_ST_MAX: int = 3 * Cf.MONTH_DAY
MA_ST_MIN: int = 3
#global_variable
LT_TRAINING_TRY: bool = True
LT_DRAW: bool = True
ENABLE_PREDICT: bool = True


class Lt(IMethod, LtSave):
    """For long term calculation. Used for long term trendency
    """
    def __init__(self, cf: Cf, dao_db: DaoDb) -> None:
        super().__init__("Lt", cf, dao_db)
        LtSave.__init__(self)
        self.dao_db = dao_db
        self.st_indicator: ArrayLike = np.array([0, 1, 2], dtype=int)
        self.hold_day_thd: int = self.o_cf.MONTH_DAY
        self.in_data: ArrayLike = None  #type:ignore
        self.eval_val: ArrayLike = None  #type:ignore
        self.in_data_acc: ArrayLike = None  #type:ignore
        self.cache_d: Dict[int, Any] = {}
        self.o_eval: MthEval = MthEval(cf, self.st_indicator,
                                       self.eval_val)  #type:ignore
        self.m_id: int = 0
        self.training_flag: bool = False
        self.draw_arrays: list = []  #debug used

    def _set_hold_day_thd(self) -> None:
        """Set the minimum hold time for training by law

        :return: maxmin hold time
        :rtype: int
        """
        # if self.alias == 'Lt':
        #     xtemp = self.o_cf.MONTH_DAY
        # else:
        #     xtemp = self.o_cf.WEEK_DAY
        #self.hold_day_thd = min([self.filt_short, xtemp])
        #self.hold_day_thd = int((self.filt_short+xtemp)/2)
        self.hold_day_thd = self.o_cf.WEEK_DAY * 2 if self.alias == 'Lt' else self.o_cf.WEEK_DAY

    def post_init_load(self,
                       o_etf: Optional[EtfCalc] = None) -> Optional[Self]:
        if super().post_init_load(o_etf) is None:
            return None
        if self.o_etf is None:
            return None

        row = self.dao_db.load_data_from_table(self.alias, self.o_etf)

        for a_name in vars(METHODS_MAP[self.alias]()):
            setattr(self, a_name, getattr(row, a_name))
        self.m_id = row.id
        #setup o_eval debug header
        self.o_eval.symbol = self.o_etf.symbol

        self.set_training_flag()
        self._set_hold_day_thd()
        self.in_data = self.o_etf.close
        self.eval_val = self.o_etf.close  #type:ignore
        #self._set_prepare()
        return self

    def set_training_flag(self) -> None:
        """Set training_flag
        Output: self.training_flag
        """
        if self.o_etf.training_flag or (self.only_buy == 0):  #type: ignore
            self.training_flag = True
        else:
            self.training_flag = False

    # def _set_prepare(self) -> Self:

    #     # self.in_data_acc = np.add.accumulate(self.in_data)
    #     self.cache_d.clear()
    #     return self

    def fetch_cache_d(self, filt_long: int) -> ArrayLike:
        """fetch data from cache_d, if not exist, store it

        :param filt_long: _description_
        :type filt_long: int
        :return: _description_
        :rtype: ArrayLike
        """
        try:
            long_data = self.cache_d[filt_long]
        except KeyError:
            long_data = self.o_cf.new_average(self.in_data_acc, filt_long, 1)
            self.cache_d[filt_long] = long_data
        return long_data

    def calc(self) -> Optional[Self]:
        if (super().calc() is None) or (self.o_etf is None):
            return None
        if self.training_flag:
            self.prepare_training().training()
        self.prepare_calc()
        self._calc().mix_lt_indicator()  #type:ignore
        self.o_eval.post_init_load(self.st_indicator, self.eval_val,
                                   self.hold_day_thd)
        self.o_eval.calc(self.o_etf.etf_type, self.only_buy,
                         self.o_etf.max_shares)
        # print(
        #     f"lt train3 {self.filt_long}, {self.filt_short} , {self.only_buy}, {self.o_eval.min_hold_days}, {self.o_eval.avg_profit_yr}"
        # )
        # print(f"lt train3 {self.o_eval.tot_profit}")
        self.o_etf.lt_hold_day_avg = self.o_eval.hold_day_avg  #type: ignore
        return self

    def store(self) -> Optional[Self]:
        """Store LtSave and other methods
        Store Method result view
        """
        if self.o_etf is None:
            return None

        # print(
        #     f"lt train3p {self.filt_long}, {self.filt_short}, {self.only_buy}, {self.o_eval.tot_profit}, {self.o_eval.tot_profit*self.o_eval.kelly}"
        # )

        if self.o_etf.symbol in ["VT", "VTI", "^GSPC_tst"
                                 ] and LT_DRAW:  #type: ignore
            DaoPlots.draw_lines(self.o_etf.symbol + "_" + self.alias,
                                self.o_etf.lt_indicator, self.draw_arrays)

        if self.o_cf.sql_lock:
            self.o_cf.sql_lock.acquire()
        # store self.only_buy and filter parameter to LtSave if training
        if self.training_flag:
            #correct the Taiwan Etf only buy issue
            if self.o_etf.etf_type == "T":
                if self.only_buy in [
                        self.o_cf.FILT_BULL_ONLY, self.o_cf.FILT_BULL_BEAR
                ]:
                    self.only_buy = self.o_cf.FILT_BULL_ONLY
                else:  # keep the same but warning
                    self.print_msg(
                        f"Taiwan stocks with only_buy: {self.only_buy}")

            self.dao_db.update_db_method(
                self.m_id,  #type:ignore
                self,
                METHODS_MAP[self.alias])

        # store m_eval
        self.dao_db.update_db_mthd_view(self.m_id, self.o_eval)
        # flush SQL results
        self.dao_db.on_stop()
        if self.o_cf.sql_lock:
            self.o_cf.sql_lock.release()

        return self

    def training(self) -> None:
        """Real training body

        :raises NotImplementedError: training fail
        """
        #print("Start training!")

        tot_profit_max: float = -100
        filt_long_max: float = 0
        filt_short_max: float = 0
        only_buy_max: int = 0

        tot_profit_max2: float = -100
        filt_long_max2: float = 0
        filt_short_max2: float = 0
        only_buy_max2: int = 0

        #calc lt
        lt_max: int = int(min([MA_LT_MAX,
                               len(self.in_data) / 2]))  #type:ignore
        for filt_long in range(lt_max, MA_MT_MAX, -1):
            self.filt_long = filt_long
            for filt_short in range(MA_ST_MAX, MA_ST_MIN, -1):
                self.filt_short = filt_short
                self._set_st_indicator()
                self.o_eval.post_init_load(self.st_indicator, self.eval_val,
                                           self.hold_day_thd)
                self.o_eval.training_fix(self.o_etf.etf_type)  #type: ignore
                for filt_buy in [
                        self.o_cf.FILT_BULL_BEAR, self.o_cf.FILT_BULL_ONLY, self.o_cf.FILT_BEAR_ONLY
                ]:
                    self.only_buy = filt_buy
                    #start calculate
                    self.o_eval.training_var(filt_buy)
                    # print(
                    #     f"deb {self.filt_long}, {self.filt_short}, {self.o_eval.tot_profit} {tot_profit_max} {self.o_eval.min_hold_days}"
                    # )
                    if self.o_eval.min_hold_days < self.hold_day_thd:  #law limit
                        continue
                    # if self.o_eval.odd <= 0.65:
                    #     continue
                    #a_target = self.o_eval.tot_profit * self.o_eval.odd
                    a_target = self.o_eval.tot_profit * self.o_eval.kelly
                    if a_target >= tot_profit_max:
                        tot_profit_max, only_buy_max = a_target, self.only_buy
                        filt_long_max, filt_short_max = self.filt_long, self.filt_short

                    a_target = self.o_eval.tot_profit
                    if a_target >= tot_profit_max2:
                        tot_profit_max2, only_buy_max2 = a_target, self.only_buy
                        filt_long_max2, filt_short_max2 = self.filt_long, self.filt_short

        #if tot_profit_max <= 0 and tot_profit_max2 > 0:
        #tot_profit_max fail but tot_profit_max2 success
        if tot_profit_max <= 0:
            #tot_profit_max fail but ignore tot_profit_max2 fail or not
            tot_profit_max, only_buy_max = tot_profit_max2, only_buy_max2
            filt_long_max, filt_short_max = filt_long_max2, filt_short_max2

        # define self.only_buy if training
        self.only_buy = only_buy_max
        self.filt_long, self.filt_short = filt_long_max, filt_short_max

        if tot_profit_max <= 0:
            self.set_err_no(
                self.o_cf.STOP_LOSS_TRAINING_FAIL,
                "STOP_LOSS_TRAINING_FAIL").print_error(
                    f"training error 1, no tot_profit_max: {self.only_buy}")
            raise NotImplementedError

        # print(
        #     f"lt train1p {self.filt_long}, {self.filt_short}, {self.only_buy}, {tot_profit_max}"
        # )
        if not LT_TRAINING_TRY:
            return

        self._set_st_indicator()
        self.o_eval.post_init_load(self.st_indicator, self.eval_val,
                                   self.hold_day_thd)
        self.o_eval.training_fix(
            self.o_etf.etf_type).training_var(  #type:ignore
                only_buy_max)
        self.only_buy = 0
        # print(
        #     f"lt train1 {self.filt_long}, {self.filt_short}, {tot_profit_max}")

        if self.o_eval.training_res(Cf.FILT_BEAR_ONLY):
            self.only_buy += Cf.FILT_BEAR_ONLY
        if self.o_eval.training_res(Cf.FILT_BULL_ONLY):
            self.only_buy += Cf.FILT_BULL_ONLY
        # print(
        #     f"lt train2 {self.filt_long}, {self.filt_short} , {self.only_buy}, {self.o_eval.min_hold_days}, {self.o_eval.avg_profit_yr}"
        # )
        if self.only_buy == 0:
            self.set_err_no(
                self.o_cf.STOP_LOSS_TRAINING_FAIL, "STOP_LOSS_TRAINING_FAIL"
            ).print_error(
                f"only_buy error: {self.filt_long} {self.filt_short} {self.only_buy} {only_buy_max}"
            )
            raise NotImplementedError
        self.only_buy = only_buy_max
        # print(  #test OK
        #     f"lt train2p {self.filt_long}, {self.filt_short}, {self.only_buy}, {tot_profit_max}"
        # )

    def prepare_training(self) -> Self:
        """Prepare data from training
        """
        self.cache_d.clear()
        if ENABLE_PREDICT:
            self.in_data = self.o_etf.close[  #type: ignore
                self.o_cf.PREDICT_DAY:]
        else:
            self.in_data = self.o_etf.close  #type: ignore
        self.in_data_acc = np.add.accumulate(self.in_data)
        return self

    def prepare_calc(self) -> Self:
        """Restore data from training
        """
        self.cache_d.clear()
        self.in_data = self.o_etf.close  #type: ignore
        self.in_data_acc = np.add.accumulate(self.in_data)
        return self

    def _set_st_indicator(self) -> Self:

        self._set_hold_day_thd()
        long_data = self.fetch_cache_d(self.filt_long)
        short_data = self.fetch_cache_d(
            self.filt_short)[:len(long_data)]  #type:ignore
        delta_data = short_data - long_data  #type:ignore
        #xfr to st_indicator
        self.st_indicator = np.where(delta_data > 0, self.o_cf.MARK_BUY,
                                     self.o_cf.MARK_SELL)
        return self

    def _calc(self) -> Optional[Self]:
        #print("Start _calc!")
        self._set_hold_day_thd()
        self.in_data = self.o_etf.close  #type:ignore
        #calc lt
        # self._set_st_indicator() and apply only_buy
        long_data = self.o_cf.new_average(self.in_data, self.filt_long)
        short_data = self.o_cf.new_average(
            self.in_data, self.filt_short)[:len(long_data)]  #type:ignore
        self.st_indicator = short_data - long_data  #type:ignore

        if self.alias == "Lt" and self.o_etf.symbol in [  #type:ignore
                "VT", "VTI", "^GSPC_tst"
        ]:
            self.print_msg(
                f"closed value: short {short_data[0]}, long {long_data[0]}"  #type: ignore
            )  #type: ignore
            self.draw_arrays = [self.in_data, long_data, short_data]
        return self

    def mix_lt_indicator(self):
        ''' mix with lt_indicator
            reserved to others
        '''
        #save lt_indicator
        self.o_etf.lt_indicator = np.where(  #type: ignore
            self.st_indicator > 0,  #type: ignore
            self.o_cf.MARK_BUY,
            self.o_cf.MARK_SELL)
        #xfr to st_indicator
        mark_buy = self.o_cf.MARK_BUY if self.only_buy & self.o_cf.FILT_BULL_ONLY else self.o_cf.MARK_HOLD
        mark_sell = self.o_cf.MARK_SELL if self.only_buy & self.o_cf.FILT_BEAR_ONLY else self.o_cf.MARK_HOLD
        self.st_indicator = np.where(
            self.st_indicator > 0,  #type: ignore
            mark_buy,  #type: ignore
            mark_sell)
        return self


def test_lt(obj_cf, dao_db, etf) -> None:
    """Test Lt module

    :param obj_cf: common configuration
    :type obj_cf: Cf
    :param dao_db: Database
    :type dao_db: DaoDb
    :param etf: Accmulated result data
    :type etf: EtfCalc
    """
    m_lt = Lt(obj_cf, dao_db)
    m_lt.post_init_load(etf)
    #print(m_lt)
    m_lt.training_flag = True
    m_lt.prepare_training().training()
    test_result = [
        m_lt.filt_long == 391, m_lt.filt_short == 64, m_lt.only_buy == 1
    ]
    assert all(test_result), "training fail 1"
    if not _chk_almost(m_lt.o_eval.avg_profit_yr, 0.083573, 0.0001):
        print("training fail 2!")
    m_lt.training_flag = False
    m_lt.calc()
    assert all(test_result), "training fail 3"
    if not _chk_almost(m_lt.o_eval.avg_profit_yr, 0.081889, 0.0001):
        print("training fail 4!")
    # store self.only_buy and filter parameter to LtSave if training
    m_lt.store()  # store m_eval


#main function  將最高層的function以兩個空白行分隔
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

    test_lt(cf_main, etf_load.dao_db, obj_etf)
    # last call to write SQL
    etf_load.on_destroy()

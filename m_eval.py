"""public class for evaluate the result of methods
"""
#import python libraries
import statistics
from typing import List
from typing_extensions import Self

#import third party libraries
import numpy as np
from numpy.typing import ArrayLike

#import yourself libraries
from bases.conf import Cf
from bases.def_etf import MthdView

from dao.dao_models import DB_LT
from dao.dao_sql import DaoDb

#constant definition

#global_variable
tst_ind = np.array([1, 1, 0, -1, -1, 0, 1, 1, -1, -1, 1, 1])
tst_val = np.array(
    [1.2, 1.1, 1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1])


class Sect():
    """definition of a section
    the section (idx_end, idx_start]
    it is (exclude,include]
    """
    def __init__(self, idx_end: int, idx_start: int) -> None:
        super().__init__()
        self.idx_end: int = idx_end
        self.idx_start: int = idx_start
        self.hold_day: int = idx_start - idx_end
        self.dec: int = -2  # buy or sell, decision of idx_start
        self.profit: float = 0

    def __str__(self) -> str:
        return f"sect ({self.idx_end}, {self.idx_start}] dec:{self.dec} profit:{self.profit} hold_day:{self.hold_day}"


class MthEval(MthdView):
    """Evaluate the tot_profit, kelly and min hold_day
    input:
        st_indicator, eval_val, hold_day_thd
    output:
        tot_profit, odd, cnt_profit, kelly, m_rank
    """
    def __init__(self, cf: Cf, st_indicator: ArrayLike,
                 eval_val: ArrayLike) -> None:
        super().__init__()
        self.o_cf: Cf = cf  #type: ignore
        self.alias: str = "mthd_view"  # same as DaoDb definition
        self.symbol: str = "my_def"  # for debug
        self.hold_day_thd: int = cf.WEEK_DAY
        self.st_indicator = st_indicator
        self.eval_val = eval_val
        self.m_rank: float = -1
        # self.op_ratio: float calc after all etf calculated, database default=-1
        # self.curr_mrkt: int = 1 wait the cutloss, database default=1
        # self.xpts_org: List[int] = []
        self.xpts: List[int] = []
        self.sects: List[Sect] = []
        self._dec_sects: List[Sect] = []
        self.min_hold_days: int = 0
        self.hold_day_tot: int = 0
        self.avg_profit: float = 0
        self._day_profit: float = 0

    def post_init_load(self, st_indicator: ArrayLike, eval_val: ArrayLike,
                       hold_day_thd: int) -> Self:
        """to change the active parameters

        :param st_indicator: indicator array
        :type st_indicator: ArrayLike
        :param eval_val: eval values array
        :type eval_val: ArrayLike
        """
        self.st_indicator = st_indicator
        self.eval_val = eval_val
        self.hold_day_thd = hold_day_thd
        #print(f"hold_day_thd: {self.hold_day_thd}")
        return self

    def set_day_ago(self) -> Self:
        """Set day_ago day_ago_dec day_ago_nav
        Input: self.xpts, st_indicator and eval_val
        """
        if len(self.xpts) == 0:
            self.day_ago = len(self.st_indicator) - 1  #type: ignore
            # print(f"{self.symbol}: debug set_day_ago len(self.xpts) == 0")
            #raise NotImplementedError
        else:
            self.day_ago = int(self.xpts[0])
        self.day_ago_dec = int(self.st_indicator[self.day_ago])  #type:ignore
        self.day_ago_nav = self.eval_val[self.day_ago]  #type:ignore
        # print(
        #     f"day_ago: {self.day_ago}, day_ago_dec: {self.day_ago_dec}, day_ago_nav: {self.day_ago_nav}"
        # )
        return self

    def set_hold_day(self) -> Self:
        """Calculate the data about hold day
        Input: self._dec_sects
        Output: hold_day_avg hold_day_tot hold_day_min
        """
        hold_days = [sect.hold_day for sect in self._dec_sects]
        if hold_days != []:
            self.hold_day_avg = statistics.median(hold_days)
            self.hold_day_tot = int(sum(hold_days))
            self.min_hold_days = int(min(hold_days))
        else:
            # print(f"{self.symbol}: debug set_hold_day: ")
            self.hold_day_avg, self.hold_day_tot, self.min_hold_days = 0, 0, 0
        # print(
        #     f"hold_day_avg: {self.hold_day_avg}, hold_day_tot: {self.hold_day_tot}, min_hold_days: {self.min_hold_days}"
        # )
        return self

    def set_avg_profit_yr(self) -> Self:
        """calculate the avg_profit_yr and _day_profit
        """
        # self.tot_profit=1.00107 check ok, 0.07
        if self.hold_day_tot == 0:
            self._day_profit = 1
            # print(f"{self.symbol} debug set_avg_profit_yr")
        else:
            self._day_profit = np.power(self.tot_profit,
                                        1.0 / self.hold_day_tot)
        self.avg_profit_yr = (self._day_profit - 1) * self.o_cf.YEAR_DAY
        # print(
        #     f"hold_day_tot: {self.hold_day_tot}, avg_profit_yr: {self.avg_profit_yr}"
        # )
        return self

    def set_loan(self) -> Self:
        """The stock is loanable
        CHARGE_LOAN: 貸款利率*3, 免得白幹

        Input: self.avg_profit_yr
        Output: self.loan
        """
        # CHARGE_LOAN: float = 0.07 * 3  # per year
        self.loan = True if self.avg_profit_yr > self.o_cf.CHARGE_LOAN else False
        #print(f"lim: {self.o_cf.CHARGE_LOAN}, loan: {self.loan} ")
        return self

    def set_track(self) -> Self:
        """test the stock is trackable
        Input: st_indicator day_ago hold_day_avg avg_profit_yr
        Output: self.track
        到投資時段末期不參加
        等補漲
        確定方向正確
        """
        if self.st_indicator[0] == self.o_cf.MARKET_HOLD:  #type:ignore
            self.track = False
            return self
        if self.day_ago < self.o_cf.WEEK_DAY * 2:
            # decision within 2 weeks, allow track
            self.track = True
            return self
        #到投資時段末期不參加
        if self.day_ago > 0.66 * self.hold_day_avg:
            # print(self.symbol+':do not track, too late!')
            self.track = False
            #print('loan:' + str(self.loan) + ':track:' + str(self.track))
            return self

        #等補漲
        goal_profit = np.power(self._day_profit, self.day_ago)
        curr_profit = self.eval_val[0] / self.eval_val[  #type:ignore
            self.day_ago]  #type: ignore
        if self.st_indicator[0] == self.o_cf.MARK_SELL:  #type:ignore
            curr_profit = 1.0 / curr_profit
            # print(f"{self.symbol}: debug set_track1")
            #raise NotImplementedError
        #curr_profit>1 確定方向正確
        if 1 <= curr_profit < goal_profit:
            self.track = True
            # print(
            #     f"{self.symbol}: debug set_track2: {curr_profit}, {goal_profit} {self.track}"
            # )
            # raise NotImplementedError
        else:
            self.track = False
        #print('goal_profit:' + str(goal_profit) + ' track:' + str(self.track))
        return self

    def _set_min_shares_fee_fix(self, etf_type: str, max_shares: int) -> Self:
        """券商手續費: 固定
        chargeMin/(the averge profit) < chargeMinRatio

        :param etf_type: ETF is TW AM
        :type etf_type: str
        :param max_shares: proceed error
        :type max_shares: int
        """
        safe_factor = 20
        if self.avg_profit <= 1:
            self.min_shares = max_shares + Cf.MAX_SHARES_ERR
            return self
        fee = self.o_cf.CHARGE_MIN_TW if etf_type == "T" else self.o_cf.CHARGE_MIN
        cap = fee * 2 / (self.avg_profit - 1) * safe_factor
        # 證券交易稅 抽成 >> 固定,
        # cap * CHARGE_MIN_RATIO_TW >> CHARGE_MIN_TW
        if etf_type == "T":
            cap_tw = 2 * self.o_cf.CHARGE_MIN_TW / self.o_cf.CHARGE_MIN_RATIO_TW * safe_factor
            if cap_tw > cap:
                cap = cap_tw
        self.min_shares = int(cap / self.eval_val[0] + 0.5)  #type:ignore
        if self.min_shares <= 0:
            self.min_shares = max_shares + Cf.MAX_SHARES_ERR
            # print(f"{self.symbol}: debug _set_min_shares_fee_fix")
            #raise NotImplementedError

        return self

    def set_min_shares(self, etf_type: str, max_shares: int) -> Self:
        """The global entry for set min shares

        券商手續費: 固定(USD7 and NTD20)與 抽成 (NTD0.1425%)
        證券交易稅 抽成 (NTD0.3%)
        所得稅 股利(USD0.3 and NTD0.2)

        :param etf_type: ETF is TW or AM
        :type etf_type: str
        :param max_shares: proceed error
        :type max_shares: int
        """
        self._set_min_shares_fee_fix(etf_type, max_shares)
        self._set_tax_to_shares(etf_type, max_shares)
        self.min_shares = int(self.min_shares + 0.5)
        if self.min_shares > 0 and \
            self.min_shares < self.o_cf.MIN_BUY_SHARES:
            # for easy to buy and sell
            self.min_shares = self.o_cf.MIN_BUY_SHARES
        #print('max shares:' + str(max_shares) + ' min:' + str(self.min_shares))
        return self

    def _set_tax_to_shares(self, etf_type: str, max_shares) -> Self:
        """Mapping tax to min shares

        For the bond and cash market the interest is taxed by 30%
        But not for trading, no implements because interest paid
        by month/season/year ??
        set tax to Shares for bond and currency

        cap*(interest/yr)*avgHoldDay*tax*safeFactor >= chargeMin*2
        cap >= chargeMin*2 / interest / avgHoldDay * yr / safeFactor / tax

        :param etf_type: which ETF, TW or AM
        :type etf_type: str
        """
        fee = self.o_cf.CHARGE_MIN_TW if etf_type == "T" else self.o_cf.CHARGE_MIN
        tax_max = self.o_cf.TAX_MAX_TW if etf_type == "T" else self.o_cf.TAX_MAX
        safe_factor: int = 4
        if (etf_type != 'B') and (etf_type != 'U'):
            return self
        interest = (self.o_cf.bond_yield_30yr/100) if etf_type == 'B' else\
         (self.o_cf.bond_yield_1yr/100)

        if self.hold_day_avg == 0:
            print(f"{self.symbol}: debug _set_tax_to_shares")
            self.min_shares = max_shares + Cf.MAX_SHARES_ERR
            return self

        xtemp = fee*2 / interest / self.hold_day_avg *\
          self.o_cf.YEAR_DAY / tax_max

        min_shares = xtemp * safe_factor / self.eval_val[0]  #type: ignore
        if min_shares > self.min_shares:
            self.min_shares = min_shares
        return self

    def set_sharpe(self):
        """create the profit list and calculate sharpe
        Input: self._dec_sects
        Output: self.sharpe
        """
        temp_list = []

        for sect in self._dec_sects:
            # print(sect)
            list1 = self.eval_val[sect.idx_end:sect.idx_start]  #type:ignore
            list2 = self.eval_val[sect.idx_end +  #type:ignore
                                  1:sect.idx_start +  #type:ignore
                                  1]  #type:ignore
            # print("list1:", list1)
            # print("list2:", list2)
            if sect.dec == self.o_cf.MARK_BUY:
                temp_list.append(list1 / list2)  #type:ignore
            else:
                temp_list.append(list2 / list1)  #type:ignore
            # print("temp_list:", temp_list)
        if not temp_list:
            print(f"{self.symbol}: debug set_sharpe error")
            self.sharpe = -100
            return self

        result = np.concatenate(temp_list) - 1
        # print("result:", result)
        self.sharpe = self.o_cf.sharpe_ratio(result) * self.o_cf.YEAR_DAY
        #print('sharpe:' + str(self.sharpe))
        return self

    def gen_xpts(self) -> Self:
        """generate the cross points
        """
        # self.xpts = list(np.where((self.st_indicator[:-1] * self.st_indicator[1:]) < 0)[0])
        xpt_data = self.st_indicator[:-1] - self.st_indicator[  #type: ignore
            1:]  #type: ignore
        self.xpts = list(np.where(xpt_data != 0)[0])
        # self.xpts_org = self.xpts
        # self.o_cf.logger.log_info(f"_gen_xpts: {self.xpts}")
        return self

    def add_head_tail(self) -> Self:
        """Add the head point and end point
        """
        xlen = len(self.st_indicator) - 1  #type: ignore
        #no cross-points
        if len(self.xpts) == 0:
            self.xpts = [0, xlen]
            return self
        # has cross-points
        if self.xpts[0] != 0:  #the first point is not the end point
            self.xpts = [0] + self.xpts
        if self.xpts[-1] != xlen:
            self.xpts.append(xlen)
        #self.o_cf.logger.log_info(f"_add_head_tail: {self.xpts}")
        #self.o_cf.logger.log_info(f"{self.eval_val[self.xpts]}")  #type: ignore
        return self

    def set_sects_profit(self, etf_type: str) -> Self:
        """calculate the raw profit per sect
        """
        charge_min_ratio = self.o_cf.CHARGE_MIN_RATIO_TW if etf_type == "T" else self.o_cf.CHARGE_MIN_RATIO
        for sect in self.sects:
            sect.profit = self.eval_val[  #type: ignore
                sect.idx_end] / self.eval_val[  #type: ignore
                    sect.idx_start]  #type: ignore
            if sect.dec == self.o_cf.MARK_SELL:
                sect.profit = 1.0 / sect.profit
        # for fee/charge, if x is 1+total_profit, c is fee% of (profit)
        # CHARGE_MIN_RATIO : 交易損失
        # if x>1 and x>>c, (x-1)*(1-c) + 1 = x-1-xc+c + 1 = x-xc+c ~ x-xc = x(1-c)
        # if x<1 and x>c  (x-1)*(1+c) + 1 = x-1 +xc -c +1 = x+xc-c ~ x-c
        for sect in self.sects:
            sect.profit *= 1 - charge_min_ratio
        return self

    def gen_raw_sects(self) -> Self:
        """ Build sectors from cross-points
        Input:  self.xpts
        Output: self.sects
        """
        self.sects = [
            Sect(self.xpts[idx], self.xpts[idx + 1])
            for idx in range(len(self.xpts) - 1)
        ]
        for sect in self.sects:
            sect.dec = self.st_indicator[sect.idx_start]  #type: ignore
            #print(sect)
        # remove MARK_HOLD
        self.sects = [
            sect for sect in self.sects if sect.dec != self.o_cf.MARK_HOLD
        ]
        #TODO: sect[0] hold_day must be conpensate, or one day missing
        # for easy calculate, ignore this day

        # print("gen_raw_sects:")
        # for sect in self.sects:
        #     print(sect)
        return self

    def filter_raw_sects(self) -> Self:
        """filter raw sects for statistic
        Input: self.sects
        Output: self.sects
        """
        try:
            # for statistic stable, remove head/tail small sect
            if self.sects[-1].hold_day < self.hold_day_thd:
                self.sects.remove(self.sects[-1])
            if self.sects[0].hold_day < self.hold_day_thd:
                self.sects.remove(self.sects[0])
        except IndexError:
            print(f"{self.symbol}: filter_raw_sects: something wrong")
        # print("final test result:")
        # for sect in self.sects:
        #     print(sect)
        return self

    def select_sects(self, buy_only: int) -> Self:
        """Select sects by condition buy_only

        Input: self.sects
        Output: self._dec_sects

        :param buy_only: FILT_BULL_ONLY, FILT_BEAR_ONLY , FILT_BULL_BEAR
        :type buy_only: int
        """
        if buy_only == self.o_cf.FILT_BULL_ONLY:
            self._dec_sects = [
                sect for sect in self.sects if sect.dec == self.o_cf.MARK_BUY
            ]
        elif buy_only == self.o_cf.FILT_BEAR_ONLY:
            self._dec_sects = [
                sect for sect in self.sects if sect.dec == self.o_cf.MARK_SELL
            ]
        else:
            self._dec_sects = [] + self.sects

        # check sects and _dec_sects are different objects
        return self

    def gen_profits(self) -> Self:
        """Generate the profits by condition
        Input: self._dec_sects
        Output: cnt_profit tot_profit odd kelly avg_profit
        """
        self.cnt_profit = len(self._dec_sects)  # 全部操作次數
        if self.cnt_profit == 0:
            self.tot_profit = -100  # 總獲利
            self.odd = 0  # 勝率
            self.kelly = 0
            self.avg_profit = 0
        else:
            self.__calc_profits(self._dec_sects)

        # print(f"cnt_profit: {self.cnt_profit}, avg_profit {self.avg_profit} ")
        # print(
        #     f"tot_profit: {self.tot_profit} , odd: {self.odd}, kelly: {self.kelly}"
        # )
        return self

    def __calc_profits(self, sects: List[Sect]) -> Self:
        """Generate the profits by condition
        Input: self._dec_sects
        Output: tot_profit odd kelly avg_profit
        """
        profit_list = np.array([sect.profit for sect in sects], float)
        self.tot_profit = np.multiply.accumulate(profit_list)[-1]  # 總獲利
        self.avg_profit = np.mean(profit_list)
        self.odd = np.where(profit_list > 1, 1, 0).mean()  # 勝率
        # self.kelly = self.o_cf.kelly_formula(self.odd) #buffet
        self.kelly = self.o_cf.kelly_formula(self.odd, self.avg_profit, True)  #theory
        return self

    def set_m_rank(self) -> Self:
        """set m_rank
        if short term, use kelly*avg_profit_yr
        """
        # self.m_rank = self.kelly * (self.tot_profit - 1)
        self.m_rank = self.kelly * self.avg_profit_yr
        # print(f"m_rank: {self.m_rank}")
        return self

    def calc(self, etf_type: str, only_buy: int, max_shares: int) -> Self:
        """calculate parameters

        :param etf_type: etf type
        :type etf_type: str
        :param only_buy: only_buy, only sell, buy and sell, training
        :type only_buy: int
        :param max_shares: for bug issue
        :type max_shares: int
        """
        self.gen_xpts().set_day_ago().add_head_tail().gen_raw_sects()
        self.set_sects_profit(etf_type).filter_raw_sects()
        self.select_sects(only_buy).set_hold_day().gen_profits()
        self.set_avg_profit_yr().set_loan().set_track().set_sharpe()
        self.set_min_shares(etf_type, max_shares).set_m_rank()
        return self

    def training_fix(self, etf_type: str) -> Self:
        """part of training, the function is invariable with only_buy

        :param etf_type: etf type
        :type etf_type: str
        """
        self.gen_xpts().set_day_ago().add_head_tail().gen_raw_sects()
        self.set_sects_profit(etf_type).filter_raw_sects()
        return self

    def training_var(self, only_buy: int) -> Self:
        """part of training, the function is variable with only_buy

        :param only_buy: only_buy
        :type only_buy: int
        """
        #self.select_sects(Cf.FILT_BULL_BEAR).set_hold_day().gen_profits()
        self.select_sects(only_buy).set_hold_day().gen_profits()
        self.set_avg_profit_yr()
        return self

    def training_res(self, only_buy: int) -> Self:
        """get tot_profit for differet

        :param only_buy: BEAR/BULL
        :type only_buy: int
        :return: _description_
        :rtype: Self
        """
        self.select_sects(only_buy).set_hold_day().gen_profits()
        self.set_avg_profit_yr()
        # print(f"debt3 {self.tot_profit}, {self.avg_profit_yr}, {self.odd}")
        if self.kelly == 0:
            # raise NotImplementedError
            return None  #type:ignore
        return self


#main function  將最高層的function以兩個空白行分隔
if __name__ == '__main__':
    # setup Cf
    cf_main = Cf()
    cf_main.post_init_only_main()
    cf_main.logger.log_info("m_eval test!!")
    o_eval = MthEval(cf_main, tst_ind, tst_val)
    # o_eval.calculate()
    # print("calc FILT_BULL_BEAR")
    # o_eval.gen_total_profit(o_eval.o_cf.FILT_BULL_BEAR)
    # print("calc FILT_BEAR_ONLY")
    # o_eval.gen_total_profit(o_eval.o_cf.FILT_BEAR_ONLY)
    # print("calc FILT_BULL_ONLY")
    # o_eval.gen_total_profit(o_eval.o_cf.FILT_BULL_ONLY)
    # o_eval._set_day_ago()._set_hold_day_avg()._set_avg_profit_yr()._set_loan()

    o_eval.gen_xpts()  #[1, 2, 4, 5, 7, 9]
    assert (len(o_eval.xpts) == 6), "gen_xpts test fail"
    o_eval.set_day_ago()  #day_ago: 1, day_ago_dec: 1, day_ago_nav: 1.1
    assert (o_eval.day_ago == 1
            and o_eval.day_ago_nav == 1.1), "test set_day_ago fail"
    o_eval.add_head_tail()  #[0, 1, 2, 4, 5, 7, 9, 11]
    assert (len(o_eval.xpts) == 8), "add_head_tail test fail"
    o_eval.gen_raw_sects()
    assert (len(o_eval.sects) == 5), "gen_raw_sects test fail"
    o_eval.set_sects_profit("T")
    assert abs(o_eval.sects[1].profit -
               0.7452) < abs(0.0001), "set_sects_profit test fail 1"
    assert abs(o_eval.sects[2].profit -
               1.3041) < abs(0.0001), "set_sects_profit test fail 2"
    assert abs(o_eval.sects[3].profit -
               0.5589) < abs(0.0001), "set_sects_profit test fail 3"
    # o_eval.set_sects_profit("X")
    o_eval.filter_raw_sects()
    assert (len(o_eval.sects) == 3), "filter_raw_sects test fail"
    # o_eval.select_sects(o_eval.o_cf.FILT_BULL_BEAR)
    # assert (len(o_eval._dec_sects) == 3), "select_sects test fail 1"
    # o_eval.select_sects(o_eval.o_cf.FILT_BULL_ONLY)
    # assert (len(o_eval._dec_sects) == 1), "select_sects test fail 2"
    o_eval.select_sects(o_eval.o_cf.FILT_BEAR_ONLY)
    assert (len(
        o_eval._dec_sects) == 2), "select_sects test fail 3"  #type: ignore
    o_eval.set_hold_day()
    test_res:bool = o_eval.hold_day_avg==2.0 and o_eval.hold_day_tot==4 \
        and o_eval.min_hold_days==2
    assert test_res, "set_hold_day test fail"
    o_eval.gen_profits()
    assert (o_eval.cnt_profit == 2), "gen_profits test fail 1"
    assert abs(o_eval.avg_profit -
               0.65205) < abs(0.0001), "set_sects_profit test fail 2"
    assert abs(o_eval.tot_profit -
               0.41649228) < abs(0.0001), "set_sects_profit test fail 3"
    assert abs(o_eval.odd - 0) < abs(0.0001), "set_sects_profit test fail 4"
    assert abs(o_eval.kelly - 0) < abs(0.0001), "set_sects_profit test fail 5"
    o_eval.set_avg_profit_yr()
    assert abs(o_eval.avg_profit_yr -
               -51.327127) < abs(0.0001), "set_avg_profit_yr test fail"
    o_eval.set_loan()
    assert not o_eval.loan, "set_loan test fail"
    old_day_ago = o_eval.day_ago
    o_eval.day_ago = o_eval.o_cf.WEEK_DAY * 2 +1
    o_eval.set_track()
    #TODO: 無法遍歷set_track()
    assert not o_eval.track, "set_track test fail"
    o_eval.day_ago = old_day_ago
    o_eval.set_sharpe()
    assert abs(o_eval.sharpe - -691.2248) < abs(0.0001), "set_sharpe test fail"

    o_eval.avg_profit = 1.2
    # o_eval.set_min_shares("T", 10000)
    o_eval.set_min_shares("B", 10000)
    assert abs(o_eval.min_shares - 290000) < abs(1), "set_min_shares test fail"
    o_eval.set_m_rank()

    dao_db = DaoDb()
    dao_db.update_db_mthd_view(246 + DB_LT, o_eval)
    dao_db.on_destroy()

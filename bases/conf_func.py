""" For common functions
"""
#import python libraries
#import third party libraries
import numpy as np
from numpy.typing import ArrayLike
from numpy import linalg as LA

#import yourself libraries
#constant definition
# global_variable

high_pts: ArrayLike = np.array(
    [0.6795, 0.682, 0.682, 0.696, 0.693, 0.7099, 0.7170, 0.722])
low_pts: ArrayLike = np.array(
    [0.6720, 0.671, 0.6706, 0.6736, 0.68, 0.6923, 0.6019, 0.41247])
close_pts: ArrayLike = np.array(
    [0.6744, 0.671, 0.6706, 0.6736, 0.68, 0.6923, 0.7073, 0.7124])
bench_pts: ArrayLike = np.array(
    [0.68, 0.68, 0.68, 0.68, 0.68, 0.68, 0.68, 0.68])
long_pts: ArrayLike = np.concatenate((close_pts, high_pts))
long_pts2: ArrayLike = np.concatenate((close_pts, high_pts, low_pts))


class ConfFunc():
    """The common used functions
    """
    @classmethod
    def new_average(cls, in_data, m_items: int, acc_flag=None):
        """Average by accumulation of input data

        :param in_data: Input data
        :type in_data: float
        :param m_items: average dividend
        :type m_items: int
        :param acc_flag: input data is accumulaed or not, defaults to None
        :type acc_flag: bool, optional
        :return: result of average
        :rtype: np.array
        """
        # if accFlag is None :
        #   accData=add.accumulate(inData)
        # else:
        #   accData=inData
        acc_data: ArrayLike = np.add.accumulate(
            in_data) if acc_flag is None else in_data

        ret_data: ArrayLike = acc_data[m_items:] - acc_data[:-m_items]

        # retData=concatenate((accData[mItems-1:mItems],retData))*(1.0/mItems)
        # insrt the first(0) item from accData to retData
        try:
            # print "debug data ",len(retData),mItems,mItems-1,len(accData)
            ret_data = np.insert(ret_data, [0],
                                 acc_data[m_items - 1]) * (1.0 / m_items)
        except IndexError:
            # the problem is mItems > len(accData)
            m_items = len(acc_data) - 1
            ret_data = np.insert(ret_data, [0],
                                 acc_data[m_items - 1]) * (1.0 / m_items)
            # print "len ",len(retData),mItems,mItems-1
            # xem1=1
            # xem=1/(xem1-1)
            # pass
        return ret_data

    @classmethod
    def kelly_formula(cls,
                      odd: float,
                      return_of_inv: float = 0,
                      mark: bool = False) -> float:  #type ignore
        """Kelly formula

        :param odd: 勝率
        :type odd: float
        :param return_of_inv: 投資回報, 0 means the equation modified by Warren Edward
            Buffett, (odd>returnOfInv) to get positive kelly value
        :type return_of_inv: float, optional
        :param mark: _description_, defaults to None
        :type mark: bool, optional, False mean use Exp(returnOfInv) , else use real returnOfInv
        :return: kelly value
        :rtype: float
        """
        if (odd <= 0 or odd > 1):
            return 0
        if return_of_inv < 0:
            return 0
        if return_of_inv == 0:
            # Buffett
            kelly = 2 * odd - 1 if odd > 0.5 else 0
            return kelly
        # the averge returnOfInv == expected value == returnOfInv*winningRatio
        if not mark:
            return_of_inv /= odd

    #        if(returnOfInv <= (1-winningRatio)/winningRatio):
    #            print "returnOfInv too small to cover fat tail effect"
    #            return 0
        kelly = (return_of_inv * odd - (1 - odd)) / return_of_inv
        return kelly if kelly > 0 else 0

    @classmethod
    def sharpe_ratio(cls, target_rtn: ArrayLike, bench_rtn=None) -> float:
        """Calculate the Sharpe Ratio

        :param target_rtn: target return
        :type target_rtn: np.Array
        :param bench_rtn: bench return, defaults to None
        :type bench_rtn: np.Array, optional
        :return: Sharpe Ratio
        :rtype: float
        """
        # x=target_rtn-bench_rtn
        # print x
        # print "mean ",np.mean(x),"stdev ",np.std(target_rtn,ddof=1)
        target_rtn = target_rtn if bench_rtn is None else (target_rtn -
                                                           bench_rtn)
        return np.mean(target_rtn) / np.std(target_rtn)
        # Geometric Mean
        # a_temp = np.log(target_rtn)
        # return np.exp(a_temp.mean()) / np.std(target_rtn)

    @classmethod
    def sortino_ratio(cls, target_rtn: ArrayLike, bench_rtn=None) -> float:
        """Calculation of Sortino Ratio

        :param targetRtn: target return
        :type targetRtn: np.Array
        :param benchRtn: reference benchmark, defaults to None
        :type benchRtn: np.Array, optional
        :return: Sortino Ratio
        :rtype: float
        """
        target_rtn = target_rtn if bench_rtn is None else (target_rtn -
                                                           bench_rtn)
        u_0 = np.mean(target_rtn)
        y_1 = target_rtn - np.mean(target_rtn)
        # print y1
        y_r = (y_1 - np.abs(y_1)) / 2
        # print y
        # print "mean ",u0,"norm ",LA.norm(y),y.size,
        d_0 = LA.norm(y_r) / np.sqrt(y_r.size - 1)
        # print d0
        return u_0 / d_0

    @classmethod
    def ATR(cls, today_high, today_lo, today_close, m_days: int):
        """Calculate the SEA TURTLE method's ATR

        :param today_high: High array
        :type today_high: np.Array
        :param today_lo: Low array
        :type today_lo: np.Array
        :param today_close: Close array
        :type today_close: np.Array
        :param m_days: time interval of average
        :type m_days: int
        :return: ATR array
        :rtype: np.Array
        """
        today_high_1 = today_high[:-1]
        today_lo_1 = today_lo[:-1]
        previous_close = today_close[1:]

        true_range = np.column_stack(
            (today_high_1 - today_lo_1, today_high_1 - previous_close,
             previous_close - today_lo_1)).max(axis=1)
        # print true_range,m_days
        ret_data = cls.new_average(true_range, m_days)
        return ret_data

    @classmethod
    def mix_ind_same(cls, s_1, s_2):
        """ mix two indicators, only keep the same parts

        :param s1: int array
        :type s1: np.Array
        :param s2: int array
        :type s2: np.Array
        :return: mixed result
        :rtype: np.Array
        """
        xlen = min(len(s_1), len(s_2))
        s_3 = np.zeros(xlen, dtype=int)
        s_4 = (s_1[:xlen] == s_2[:xlen])[:xlen]
        # print(f"xlen:{xlen} s3:{len(s3)} s4:{len(s4)} ")
        s_3[s_4] = (s_1[:xlen])[s_4]
        return s_3


def _chk_almost(indata: ArrayLike, target, tol: float) -> bool:
    """check abs(indata-target)<=tol

    :param indata: input data needed to check
    :type indata: ArrayLike
    :param target: target data
    :type target: ArrayLike
    :param tol: tolence
    :type tol: float
    :return: check result
    :rtype: bool
    """
    result = abs(indata - target) <= tol
    try:
        return result.all()
    except AttributeError:
        return result


#main function  將最高層的function以兩個空白行分隔
if __name__ == '__main__':
    # print(ConfFunc.kelly_formula(0.45, 1.2, True))
    # print(ConfFunc.kelly_formula(0.45, 0.85, True))
    #test new_average
    val_1 = ConfFunc.new_average(high_pts, 3)
    val_2 = np.array(
        [0.68116667, 0.68666667, 0.69033333, 0.69963333, 0.70663333, 0.7163])
    if not _chk_almost(val_1, val_2, 0.01):
        print("test new_average 1: False!")
    val_1 = ConfFunc.new_average(high_pts, len(high_pts) + 2)
    val_2 = np.array([0.6942])
    if not _chk_almost(val_1, val_2, 0.01):
        print("test new_average 2: False!")

    #kelly_formula
    val_1 = np.array([
        ConfFunc.kelly_formula(0.6),
        ConfFunc.kelly_formula(0.5, 1.5),
        ConfFunc.kelly_formula(0.6, 0.8, True)
    ])
    if not _chk_almost(val_1, np.array([0.2, 0.33333, 0.1]), 0.001):
        print("test kelly_formula : False!")
    #sharpe_ratio
    val_1 = ConfFunc.sharpe_ratio(close_pts, bench_pts)
    if not _chk_almost(val_1, 0.3312, 0.001):
        print("test sharpe_ratio : False!")
    #sortino_ratio
    val_1 = ConfFunc.sortino_ratio(close_pts, bench_pts)
    if not _chk_almost(val_1, 0.5226, 0.001):
        print("test sortino_ratio : False!")
    #ATR
    val_1 = ConfFunc.ATR(high_pts, low_pts, close_pts, 3)
    if not _chk_almost(
            val_1,
            np.array([0.01043333, 0.01506667, 0.0156, 0.01766667, 0.04856667]),
            0.001):
        print("test ATR : False!")
    #mix_indicators
    val_1 = ConfFunc.mix_ind_same(np.array([0, 0, 0, 1, 1, 1, -1, -1, -1]),
                                  np.array([0, 1, -1, 0, 1, -1, 0, 1, -1]))
    if not _chk_almost(val_1, np.array([0, 0, 0, 0, 1, 0, 0, 0, -1]), 0.001):
        print("test mix_ind_same : False!")

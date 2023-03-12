""" define Config and constants
Cf -> ConfConst, ConfCharge, ConfErrorNo
"""

#import python libraries

#import third party libraries

#import yourself libraries

#constant definition

# global_variable


class ConfigData:
    """ the definitions for csv data files
    """
    DATA_DIR: str = "D:\\homer\\Documents\\invest\\dataf\\"
    UPDATE_DIR: str = DATA_DIR + "update\\"
    FILT_LONG: int = 276
    FILT_SHORT: int = 27
    EtfLenLimit = 2 * FILT_LONG + FILT_SHORT


class ConfInterval:
    """ the definition of working days
    """
    WEEK_DAY: int = 5
    MONTH_DAY: int = 22
    SEASON_DAY: int = 65
    HALF_YEAR_DAY: int = 130
    YEAR_DAY: int = 261
    TRUNCATE_DAY: int = YEAR_DAY * 15
    TRAINING_DAY: int = 13
    PREDICT_DAY: int = 1


class ConfCharge:
    """constants used for the charge and tax
    """
    CHARGE_MIN: int = 7  # The charges for Firstrade USD
    CHARGE_MIN_TW: int = 20
    CHARGE_MIN_RATIO: float = 0.01  # chargeMin/(the averge profit) < chargeMinRatio
    CHARGE_MIN_RATIO_TW: float = 0.0585 + 0.01
    TAX_MAX: float = 0.3  # Fed tax for non-residents : 30% per year for bond/currency
    TAX_MAX_TW: float = 0.2
    CHARGE_LOAN: float = 0.07 * 3  # per year
    SAFE_SHARE_DIVIDER: int = 100
    MAX_PRICE_RATIO: float = 0.5
    CALC_DELAY: int = 1
    MOD_TW_SHARES: int = 1000
    MOD_NTD_EXANGE: float = 30
    MIN_BUY_SHARES: int = 10
    MAX_SHARES_ERR = MIN_BUY_SHARES + 100


class ConfConst(ConfigData, ConfInterval, ConfCharge):
    """ constants used for the market and the time interval
    """

    # constants used for the market
    MARK_BUY: int = 1
    MARK_HOLD: int = 0
    MARK_SELL: int = -1

    MARKET_BULL: int = 1
    MARKET_HOLD: int = 0
    MARKET_BEAR: int = -1

    FILT_BULL_ONLY: int = 1  # 只做多
    FILT_BULL_BEAR: int = 3  # 多空並做
    FILT_BEAR_ONLY: int = 2  # 只做空


if __name__ == '__main__':
    pass

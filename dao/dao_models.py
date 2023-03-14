"""Help files for dao_sql.py
"""

#import python libraries

#import third party libraries

from sqlalchemy import Boolean, Column, Float, Integer, String, Text
from sqlalchemy.orm import declarative_base

#import yourself libraries
from bases.def_etf import EtfConf

#constant definition
DB_MASK_BIT: int = 16
DB_MASK: int = (1 << DB_MASK_BIT) - 1
DB_LT: int = 1 << DB_MASK_BIT
DB_RSI: int = 2 << DB_MASK_BIT
DB_MD: int = 3 << DB_MASK_BIT
DB_KD: int = 4 << DB_MASK_BIT
DB_CUTLOSS: int = 1 << (DB_MASK_BIT + 4)  # methods can not be over 16

#global_variable
DBase = declarative_base()


def db_id_mapping(etf_id: int, alias: str) -> int:
    """mapping Etf id to Method id by name

    :param etf_id: Etf id
    :type etf_id: int
    :param alias: table name
    :type alias: str
    :return: method id
    :rtype: int
    """
    d_mapper: dict = {"Lt": DB_LT, "Rsi": DB_RSI, "Md": DB_MD, "Kd": DB_KD}
    return etf_id + d_mapper[alias]


def db_name_to_table(alias: str):
    """map the table name to Table class

    :param alias: table name
    :type alias: str
    :return: Db class
    :rtype: class
    """
    d_mapper: dict = {"Lt": DbLt, "Rsi": DbRsi, "Md": DbMd, "Kd": DbKd}
    return d_mapper[alias]


class DbConf(DBase):
    """Database Table mapped into EtfConf
    """
    __tablename__ = 'etf'
    id = Column(Integer, primary_key=True, autoincrement=True)
    etf_type = Column(Text, nullable=False)
    symbol = Column(Text, nullable=False, unique=True)
    cname = Column(Text, nullable=False, unique=True)
    disabled = Column(Boolean, nullable=False)
    notes = Column(String, nullable=True)

    def __init__(self, o_etf: EtfConf) -> None:
        self.etf_type = o_etf.etf_type
        self.symbol = o_etf.symbol
        self.cname = o_etf.cname
        self.disabled = o_etf.disabled
        self.notes = o_etf.notes

    def __repr__(self) -> str:
        return "<etf('%s', '%s', '%s', '%r', '%s')>" % (
            self.etf_type, self.symbol, self.cname, self.disabled, self.notes)


class DbEtfView(DBase):
    """Etf data within information table
    """
    __tablename__ = 'etf_view'
    id = Column(Integer, primary_key=True,
                autoincrement=False)  # same as DbConf
    symbol = Column(Text, nullable=False, unique=True)
    atr = Column(Float)  # calculation
    nav = Column(Float)  #淨值
    nav_chg = Column(Float)  #淨值變動
    nav_date = Column(Text)  #淨值日期 2021/11/17
    sell_price = Column(Float)  #  ~ 2000.11
    buy_price = Column(Float)  # 1000.11
    max_shares = Column(Integer)  #股數 9999+股
    op_ratio = Column(Integer)  #股數 9999股
    rank = Column(Float)  #排名
    issued = Column(Text)

    def __init__(self, o_etf: EtfConf) -> None:
        self.id = o_etf.hash_id  #type: ignore
        self.symbol = o_etf.symbol

    def __repr__(self) -> str:
        return f"<{self.__tablename__}: e_if:{self.id:x}, sym:{self.symbol}>"


class DbMthdView(DBase):
    """Store the calculations' result of ETF
    """
    __tablename__ = 'mthd_view'

    id = Column(Integer, primary_key=True,
                autoincrement=False)  # method id, m_id from different method
    m_rank = Column(Float, default=-1)
    #curr_mrkt = Column(Integer, default=-2)
    day_ago = Column(Integer)
    day_ago_dec = Column(Integer)
    day_ago_nav = Column(Float)
    hold_day_avg = Column(Float)
    odd = Column(Float)
    cnt_profit = Column(Integer)
    kelly = Column(Float)
    avg_profit_yr = Column(Float)
    loan = Column(Boolean, default=False)
    track = Column(Boolean, default=False)
    min_shares = Column(Integer)
    op_ratio = Column(Float, default=0)
    tot_profit = Column(Float)
    sharpe = Column(Float)

    def __init__(self, method_id: int) -> None:
        self.id = method_id  #type: ignore

    def __repr__(self) -> str:
        return f"<{self.__tablename__}:m_id {self.id:x}>"


class DbCutLoss(DBase):
    """The parameters of cutloss of the different methods
    """
    __tablename__ = 'cut_loss'

    id = Column(Integer, primary_key=True, autoincrement=False)  # cutloss id
    m_id = Column(Integer, nullable=False,
                  unique=True)  # method id, m_id from different method
    cut_bull = Column(Float, default=0)  #cut loss for bull market
    cut_bear = Column(Float, default=0)  #cut loss for bear market

    def __init__(self, method_id: int) -> None:
        self.id = DB_CUTLOSS + method_id  #type: ignore
        self.m_id = method_id

    def __repr__(self) -> str:
        return f"<{self.__tablename__}:id {self.id:x}:m_id {self.m_id:x}>"


class DbLt(DBase):
    """The parameters of Lt
    """
    __tablename__ = 'Lt'

    id = Column(Integer, primary_key=True,
                autoincrement=False)  # method id, e_id+mask
    e_id = Column(Integer, nullable=False, unique=True)  # same as DbConf
    symbol = Column(Text, nullable=False, unique=True)
    filt_long = Column(Integer, default=276)
    filt_short = Column(Integer, default=27)
    only_buy = Column(Integer, default=0)

    def __init__(self, o_etf: EtfConf) -> None:
        self.id = o_etf.hash_id + DB_LT  #type: ignore
        self.e_id = o_etf.hash_id
        self.symbol = o_etf.symbol

    def __repr__(self) -> str:
        return f"<{self.__tablename__}:m_id {self.id:x}:e_id {self.e_id:x}:sym {self.symbol}>"


class DbKd(DBase):
    """The parameters of KD method
    """

    __tablename__ = 'Kd'

    id = Column(Integer, primary_key=True,
                autoincrement=False)  # method id, e_id+mask
    e_id = Column(Integer, nullable=False, unique=True)  # same as DbConf
    symbol = Column(Text, nullable=False, unique=True)
    filt_long = Column(Integer, default=8)
    filt_short = Column(Integer, default=4)
    filt_rsv = Column(Integer, default=11)
    thd_high = Column(Float, default=0.85)
    thd_low = Column(Float, default=0.2)
    only_buy = Column(Integer, default=0)

    def __init__(self, o_etf: EtfConf) -> None:
        self.id = o_etf.hash_id + DB_KD  #type: ignore
        self.e_id = o_etf.hash_id
        self.symbol = o_etf.symbol

    def __repr__(self) -> str:
        return f"<{self.__tablename__}:m_id {self.id:x}:e_id {self.e_id:x}:sym {self.symbol}>"


class DbMd(DBase):
    """The parameters of MACD method
    """
    __tablename__ = 'Md'

    id = Column(Integer, primary_key=True,
                autoincrement=False)  # method id, e_id+mask
    e_id = Column(Integer, nullable=False, unique=True)  # same as DbConf
    symbol = Column(Text, nullable=False, unique=True)
    filt_long = Column(Integer, default=33)
    filt_short = Column(Integer, default=14)
    filt_dif = Column(Integer, default=5)
    only_buy = Column(Integer, default=0)

    def __init__(self, o_etf: EtfConf) -> None:
        self.id = o_etf.hash_id + DB_MD  #type: ignore
        self.e_id = o_etf.hash_id
        self.symbol = o_etf.symbol

    def __repr__(self) -> str:
        return f"<{self.__tablename__}:m_id {self.id:x}:e_id {self.e_id:x}:sym {self.symbol}>"


class DbRsi(DBase):
    """The parameters of RSI method
    """
    __tablename__ = 'Rsi'

    id = Column(Integer, primary_key=True,
                autoincrement=False)  # method id, e_id+mask
    e_id = Column(Integer, nullable=False, unique=True)  # same as DbConf
    symbol = Column(Text, nullable=False, unique=True)
    filt_long = Column(Integer, default=17)
    filt_short = Column(Integer, default=5)
    thd_high = Column(Float, default=0.85)
    thd_low = Column(Float, default=0.3)
    only_buy = Column(Integer, default=0)

    def __init__(self, o_etf: EtfConf) -> None:
        self.id = o_etf.hash_id + DB_RSI  #type: ignore
        self.e_id = o_etf.hash_id
        self.symbol = o_etf.symbol

    def __repr__(self) -> str:
        return f"<{self.__tablename__}:m_id {self.id:x}:e_id {self.e_id:x}:sym {self.symbol}>"


if __name__ == '__main__':
    pass

""" Access data by SQL. Use SQLAlchemy
In Windows, Engine can not be shared because Engine can not be pickled.
It means every process needs an Engine. May be need mp.lock

Reference:
    https://docs.sqlalchemy.org/en/14/core/pooling.html#using-connection-pools-with-multiprocessing-or-os-fork

    https://mikolaje.github.io/2019/sqlalchemy_with_multiprocess.html

SQL Insert 受 autoflash=false 影響, 只能在 main process 使用, 不能用於MP
SQL Query 受 autoflash=true 影響, 不能用於MP
SQL Update, Delete, Flush 必
"""

#import python libraries
from multiprocessing import Pool
# from typing import Optional
# from typing_extensions import Self

#import third party libraries
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

#import yourself libraries
from bases.def_etf import EtfCalc, EtfConf, EtfView, MthdView
from dao.dao_models import DbCutLoss, DBase, DbConf, \
    DbEtfView, DbLt, DbKd, DbMd, DbMthdView, DbRsi, \
    db_id_mapping, db_name_to_table

#constant definition
# global_variable


class DaoDb():
    """ Database access. Use SQLite engine
    """
    @staticmethod
    def create(fname: str = 'invest.db') -> Engine:
        """ Create the SQLite engine

        :return: SQLAlchemy engine for SQLite
        :rtype: Engine
        """
        s_init: str = 'sqlite:///' + fname + '?check_same_thread=False'
        # print(f"SQLite init: {s_init}")
        engine: Engine = create_engine(s_init, echo=False)
        return engine

    def __init__(self, is_mp: bool = False) -> None:
        self.db_engine: Engine = DaoDb.create()
        if is_mp:
            self.db_engine.dispose()
        # checkfirst=True mean creating tables but ignore exist
        DBase.metadata.create_all(self.db_engine, checkfirst=True)
        # DbSession = sessionmaker(bind=self.db_engine) # type ignore
        if is_mp:
            # debug , autoflush=False
            self.session = (sessionmaker(bind=self.db_engine, autoflush=False))()
        else:
            self.session = (sessionmaker(bind=self.db_engine))()

    def on_destroy(self) -> None:
        """close the DaoDb

        :return: _description_
        :rtype: Self
        """
        self.session.commit()
        self.session.close()
        if self.db_engine:
            self.db_engine.dispose()
            # self.db_engine = None #type ignore

    def on_stop(self) -> None:
        """flush pending SQL requests
        """
        self.session.commit()
        #self.session.flush()

    def row_add_to_dbconf(self, o_etf: EtfConf) -> None:
        """Add a EtfConf to Db

        :param o_etf: EtfConf object
        :type o_etf: EtfConf
        """
        #query o_etf
        row = self.session.query(DbConf).filter(
            DbConf.symbol == o_etf.symbol).first()
        if row:
            #if exist, update it
            o_etf.hash_id = row.id
            row.etf_type = o_etf.etf_type
            row.cname = o_etf.cname
            row.disabled = o_etf.disabled
            row.notes = o_etf.notes
            #o_etf.hash_id = row.id
        else:
            #else insert o_etf
            new_row = DbConf(o_etf)
            self.session.add(new_row)
            #self.session.commit()
            # query again, get id
            row = self.session.query(DbConf).filter(
                DbConf.symbol == o_etf.symbol).first()
            if row:
                o_etf.hash_id = row.id
        #print(o_etf.hash_id, ":", row)
        # DbEtfView
        row = self.session.query(DbEtfView).filter(
            o_etf.hash_id == DbEtfView.id).first()
        if row is None:
            self.session.add(DbEtfView(o_etf))
            #self.session.commit()
        row = self.session.query(DbEtfView).filter(
            o_etf.hash_id == DbEtfView.id).first()
        #print(row)

    def add_dbcutloss(self, rows):
        """add rows to DbCutLoss

        :param rows: rows of different methods
        :type rows: DbLt(), DbRsi(), ...etc
        :return: the result of added
        :rtype: List[DbCutLoss]
        """
        chk_rows = [
            self.session.query(DbCutLoss).filter(
                DbCutLoss.m_id == row.id).first() for row in rows
        ]
        need_add_rows = [
            idx for idx, ins_row in enumerate(chk_rows) if ins_row is None
        ]
        #need insert row
        _ = [
            self.session.add(DbCutLoss(rows[idx].id)) for idx in need_add_rows
        ]
        #self.session.commit()
        #check DbCutLoss again
        chk_rows = [
            self.session.query(DbCutLoss).filter(
                DbCutLoss.m_id == row.id).first() for row in rows
        ]
        # print("add all for DbCutLoss:")
        # for row in chk_rows:
        #     print(row)
        return chk_rows

    def add_row_to_dbmthdview(self, rows):
        """add methods and theirs cutloss result into DbMthdView

        :param rows: rows of methods and theirs cutloss
        :type rows: such as DbLt() and DbCutLoss()
        :return: list of DbMthdView
        :rtype: List[DbMthdView]
        """
        chk_rows = [
            self.session.query(DbMthdView).filter(
                DbMthdView.id == row.id).first() for row in rows
        ]
        _ = [
            self.session.add(DbMthdView(rows[idx].id))
            for idx, row in enumerate(chk_rows) if row is None
        ]
        #self.session.commit()
        chk_rows = [
            self.session.query(DbMthdView).filter(
                DbMthdView.id == row.id).first() for row in rows
        ]
        # print("add into DbMthdView:")
        # for row in chk_rows:
        #     print(row)
        return chk_rows

    def add_row_to_methods(self, o_etf: EtfConf) -> None:
        """add EtfConf into different methods

        :param o_etf: the assigned EtfConf
        :type o_etf: EtfConf
        """
        a_methods = [DbLt, DbRsi, DbMd, DbKd]
        rows = [
            self.session.query(a_type).filter(
                a_type.e_id == o_etf.hash_id).first() for a_type in a_methods
        ]
        need_add_rows = [
            idx for idx, ins_row in enumerate(rows) if ins_row is None
        ]
        for idx in need_add_rows:
            #need insert row
            self.session.add(a_methods[idx](o_etf))
        #self.session.commit()

        #query again
        rows = [
            self.session.query(a_type).filter(
                a_type.e_id == o_etf.hash_id).first() for a_type in a_methods
        ]
        # print("row added into methods:")
        # for row in rows:
        #     print(row)

        rows += self.add_dbcutloss(rows)
        rows = self.add_row_to_dbmthdview(rows)

    def update_db_etf_view(self, o_etf: EtfCalc) -> None:
        """update data to DbEtfView

        :param o_etf: _description_
        :type o_etf: EtfCalc
        """
        row = self.session.query(DbEtfView).filter(
            DbEtfView.id == o_etf.hash_id).scalar()
        for a_name in vars(EtfView()):
            # print(f"deb: {a_name} : ")
            # print(f"val: {getattr(o_etf, a_name)}")
            setattr(row, a_name, getattr(o_etf, a_name))
        # self.session.commit()

    def load_data_from_table(self, tab_name: str, o_etf: EtfConf):
        """get row data from the assigned table name

        :param tab_name: table name
        :type tab_name: str
        :param o_etf: Etf object with correct id
        :type o_etf: EtfConf
        :return: row data
        :rtype: row
        """
        a_table = db_name_to_table(tab_name)
        tab_id = db_id_mapping(o_etf.hash_id, tab_name)
        # print(a_table.id)
        #row = self.session.query(DbLt).filter(DbLt.id == tab_id).scalar()
        row = self.session.query(a_table).filter(a_table.id == tab_id).scalar()
        return row

    def update_db_mthd_view(self, tab_id: int, a_mth_eval):
        """update DbMthdView table

        :param tab_id: id of etf+method+cutloss
        :type tab_id: int
        :param a_mth_eval: MthdView object
        :type a_mth_eval: MthdView
        """
        row = self.session.query(DbMthdView).filter(
            DbMthdView.id == tab_id).scalar()
        # print(vars(MthdView()))
        for a_name in vars(MthdView()):
            # print(f"deb: {a_name} : ")
            # print(f"val: {getattr(a_mth_eval, a_name)}")
            setattr(row, a_name, getattr(a_mth_eval, a_name))
        # self.session.commit()

    def update_db_method(self, m_id: int, o_method, o_method_view):
        """update Db of methods

        :param etf_id: Etf id
        :type etf_id: int
        :param o_method: Method as Lt
        :type o_method: Lt, Rsi, etc
        :param o_method_view: LtSave etc
        :type o_method_view: LtSave
        """
        o_db_type = db_name_to_table(o_method.alias)
        row = self.session.query(o_db_type).filter(
            o_db_type.id == m_id).scalar()
        for a_name in vars(o_method_view()):
            # print(f"deb: {a_name} : ")
            # print(f"val: {getattr(o_method, a_name)}")
            setattr(row, a_name, getattr(o_method, a_name))
        # self.session.commit()


def __run_in_process(sym: str):
    """Run multiprocess test

    :param sym: the target symbol
    :type sym: str
    """
    print(f"in run_in_process {sym}")
    dao_db = DaoDb()
    row = dao_db.session.query(DbConf).filter(DbConf.symbol == sym).first()
    if row:
        print(row)
    else:
        print(f"row: {sym} is not exist!")


#main function  將最高層的function以兩個空白行分隔
if __name__ == '__main__':
    print(f"The DAO version: {sqlalchemy.__version__}")

    o_dao_db = DaoDb(False)  #create tables and session
    #fill the table
    obj_etf = EtfConf("X", "^TYX", "美30年債殖利率_idx", False, "")
    o_dao_db.row_add_to_dbconf(obj_etf)
    o_dao_db.add_row_to_methods(obj_etf)
    o_dao_db.on_destroy()

    print("The multiprocess DAO test:")
    with Pool(2) as pool:
        pool.map(__run_in_process, ["^STI", "^TWII", "^TYX"])

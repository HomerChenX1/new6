""" for main program of invest
    for working correct, need to put a .pth file
    in getusersitepackages() folder
    content is D:\\homer\\Documents\\invest\\new6
"""

#import python libraries
#import os
from site import getusersitepackages
import sys
from multiprocessing import Pool, Process, Queue, Manager, cpu_count, Lock
import winsound

#import third party libraries

#import yourself libraries
from bases.conf import Cf
from bases.conf_log import ConfLog, ConfLogServ
from bases.def_etf import EtfCalc, EtfConf
from dao.dao_csv import DaoCsv
from dao.dao_ftp import DaoFtpClient
from dao.dao_ticket import RepoTickets
from dao.dao_sql import DaoDb
from init_conf import InitConf
from m_etf_load import EtfLoad
from m_lt import Lt

#constant definition
# global_variable
ENABLE_FTP: bool = False
ENABLE_ALL_ETF: bool = True


def test_csv() -> None:
    """Test DaoCsv actions
    """
    print("path is ")
    print(sys.path)
    print("the working week is: ")
    print(Cf.WEEK_DAY)
    print("The site-package pos: ")
    print(getusersitepackages())
    dao_csv = DaoCsv("D:\\homer\\Documents\\invest\\new6\\config.csv")
    new_data = dao_csv.read_all()
    print(new_data[0])


def run_init_conf(cf_main: Cf) -> InitConf:
    """Run InitConf

    :param cf_main: _descripta Cf object
    :type cf_main: Cf
    :return: init_configure
    :rtype: InitConf
    """
    cf_main.logger.log_info("InitConf test!!")
    init_configure: InitConf = InitConf(cf_main)
    init_configure.proc_all()
    # for etf_item in init_configure.all_etfs:
    #     init_configure.print_error(str(etf_item))
    return init_configure


def run_ftp(i_conf: InitConf) -> None:
    """Download assigned ETF symbols

    :param i_conf: the result of run_init_conf()
    :type i_conf: InitConf
    """
    str_symbols: str = " ".join(i_conf.etf_symbol_list)
    repo = RepoTickets(str_symbols)
    repo.download()
    repo.proc_failed_list()
    if repo.failed_list:
        i_conf.print_error("FTP download error: " + " ".join(repo.failed_list))


def run_dao_sql_init(i_conf: InitConf) -> None:
    """Create and check database

    :param i_conf: result of InitConf
    :type i_conf: InitConf
    """
    o_dao_db = DaoDb(False)  #create tables and session
    #fill the table
    for o_etf in i_conf.all_etfs:
        o_dao_db.row_add_to_dbconf(o_etf)
        o_dao_db.add_row_to_methods(o_etf)
    o_dao_db.on_destroy()


def mp_init(a_queue: Queue, a_lock: Lock):  # type: ignore
    """Initializer

    :param a_queue: for logger's queue
    :type a_queue: Queue
    """
    global log_queue, Sql_Lock  # type: ignore
    log_queue = a_queue
    Sql_Lock = a_lock


def mp_worker(o_etf: EtfConf, o_cf: Cf) -> bool:
    """Calculation of Methods

    :param argv: (o_etf, o_cf)
    :type argv: tuple
    :return: _description_
    :rtype: _type_
    """
    #pid: int = os.getpid()
    #setup cf
    o_cf.post_init(log_queue, Sql_Lock, True)
    #o_cf.logger.log_msg("info", f"current pid {pid}: sym {o_etf.symbol}")
    #setup EtfLoad
    if o_etf.disabled:
        o_cf.logger.log_msg("debug", f"sym: {o_etf.symbol} is disabled!")
        return False
    etf_load = EtfLoad(o_cf, DaoDb(True))
    obj_etf = EtfCalc()
    # need copy_from()
    obj_etf.copy_from(o_etf)
    #load csv : post_init_load
    try:
        etf_load.post_init_load(obj_etf)
        etf_load.proc_all()
    except AttributeError:
        o_cf.logger.log_msg("info", f"sym: {o_etf.symbol} is wrong!")
        etf_load.on_destroy()
        return False
    # finally:
    #     etf_load.on_destroy()

    # start to run all methods
    try:
        m_lt = Lt(o_cf, etf_load.dao_db)
        m_lt.post_init_load(obj_etf)
        m_lt.calc()
        m_lt.store()
    except NotImplementedError as o_err:
        err_str = f"{o_etf.symbol} task fail!"
        if o_err.__doc__:
            err_str = err_str + o_err.__doc__
        o_cf.logger.log_msg("info", err_str)
        return False
    finally:
        etf_load.on_destroy()
    return True


#main function  將最高層的function以兩個空白行分隔
if __name__ == '__main__':
    #setup global variable

    # test_csv()
    # create the shared queue
    log_queue = Queue()
    Sql_Lock = Lock()
    # start manager list
    with Manager() as manager:
        log_list = manager.list()
        # start the logger process
        logger_p = Process(target=ConfLogServ.fork_log_serv,
                           args=(
                               log_queue,
                               log_list,
                           ))
        logger_p.start()

        # setup Cf
        cf = Cf()
        cf.post_init(log_queue)
        # report initial message
        cf.logger.log_info('Main process started.')
        # init configuration
        o_init_conf = run_init_conf(cf)  #for non FTP
        #setup database
        run_dao_sql_init(o_init_conf)
        #start FTP
        if ENABLE_FTP:
            run_ftp(o_init_conf)  #run FTP
        #run methods
        if ENABLE_ALL_ETF:
            test_etfs = o_init_conf.all_etfs
        else:
            test_etfs = [
                x_etf for x_etf in o_init_conf.all_etfs
                if x_etf.symbol in ["VT", "VTI"]
            ]

        mth_argvs = [
            (
                obj_etf,
                cf,
                # ) for obj_etf in o_init_conf.all_etfs]
            ) for obj_etf in test_etfs
        ]
        with Pool(initializer=mp_init,
                  initargs=(log_queue, Sql_Lock),
                  processes=cpu_count() * 2) as pool:
            #start run process
            result = pool.starmap(mp_worker, mth_argvs)
            x_acc: int = 0
            for x_val in result:
                if x_val:
                    x_acc += 1
            cf.logger.log_info(f'success ratio: {x_acc/len(result)}')

        #TODO: next to select or cash tables

        cf.logger.log_info('Main process done.')
        # shutdown the queue correctly
        ConfLog.stop_log_serv(logger_p, log_queue)
        # print out the list
        print('Print out log_list!!')
        for msg_txt in log_list:
            print(msg_txt)

    if ENABLE_FTP:
        a_ftp = DaoFtpClient("192.168.0.1", "HomerTp", "87109az")
        a_ftp.change_remote_dir("G/Download/data")
        a_ftp.put_file_to_host("invest.htm")
        a_ftp.bye()
    winsound.PlaySound('Cuckoo.wav', winsound.SND_FILENAME)

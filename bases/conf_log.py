""" Generate the log system of multiprocess
    References:
        https://shengyu7697.github.io/python-logging/
        https://superfastpython.com/multiprocessing-logging-in-python/

"""

#import python libraries

from typing import Dict, Optional, Tuple
from random import random
from time import sleep

from multiprocessing import Process, Queue, current_process, Manager
from multiprocessing.process import BaseProcess

import logging
from html import escape  # python 3.x

#import third party libraries

#import yourself libraries

#constant definition

# global_variable


class ConfLog:
    """ the worker process of the log system
    """

    proc_queue: Optional[Queue] = None
    _xfr_func: int = 0
    _xfr_sym: int = 1
    _xfr_color = 2
    _xfr_to_html = 3
    _xfr_dir: Dict[str, Tuple] = {
        "debug": (
            logging.debug,
            "D:",
            None,
            False,
        ),
        "info": (
            logging.info,
            "I:",
            "text-info",
            False,
        ),
        "warning": (
            logging.warning,
            "W:",
            "text-warning",
            True,
        ),
        "error": (
            logging.error,
            "E:",
            "text-danger",
            True,
        ),
        "critical": (
            logging.critical,
            "C:",
            "bg-danger",
            True,
        )
    }

    def __init__(self, proc_queue: Queue) -> None:
        if ConfLog.proc_queue is None:
            ConfLog.proc_queue = proc_queue

    @classmethod
    def log_info(cls, msg: str, is_html: bool = False) -> None:
        """The log interface for replacing the print function

        :param msg: text/html message
        :type msg: str
        :param is_html: Is msg html format, defaults to False
        :type is_html: bool, optional
        """
        cls.log_msg("info", msg, is_html)

    @classmethod
    def log_msg(cls, log_type: str, msg: str, is_html: bool = False) -> None:
        """ log public interface

        :param log_type: 'debug', 'info', 'warning', etc
        :type log_type: str
        :param msg: the text message
        :type msg: str
        :param is_html: if False, msg will convert to HTML format
        :type is_html: bool, optional
        """

        if cls.proc_queue is not None:
            cls.proc_queue.put([log_type, msg, is_html])
        else:
            log_fmt = cls._xfr_dir[log_type]
            log_fmt[cls._xfr_func](log_fmt[cls._xfr_sym] + msg)

    @staticmethod
    def test_task(test_q: Queue) -> None:
        """ test routine
        """
        test_logger = ConfLog(test_q)

        # get the current process
        p_worker: BaseProcess = current_process()
        # report initial message
        if test_q is not None:
            # test_q.put(f'Child {p_worker.name} starting.')
            test_logger.log_msg("debug", f'Child {p_worker.name} starting.')
            # simulate doing work
            for i in range(5):
                # report a message
                # test_q.put(f'Child {p_worker.name} step {i}.')
                test_logger.log_msg("warning",
                                    f'Child {p_worker.name} step {i}. s&p500')
                # block
                sleep(random())  # type: ignore
            # report final message
            #test_q.put(f'Child {p_worker.name} done.')
            test_logger.log_msg("debug", f'Child {p_worker.name} done.')
        else:
            print("ConfLog:test_task test_q is not exist!!")

    @classmethod
    def stop_serv(cls) -> None:
        """shutdown the queue correctly
        """
        if cls.proc_queue is not None:
            print("stop_serv start!")
            cls.proc_queue.put(None)
        else:
            print("ConfLog:stop_serv proc_queue is not exist!!")

    @staticmethod
    def stop_log_serv(srv_p: Process, srv_q: Queue) -> None:
        """shutdown the queue correctly to serv process

        :param p: server process
        :type p: Process
        :param q: queue of server
        :type q: Queue
        """
        # print("stop_log_serv start!")
        conf_log = ConfLog(srv_q)
        conf_log.stop_serv()
        if srv_p.is_alive():
            # print("stop_log_serv: wait server stop!")
            srv_p.join()
        print("stop_log_serv finished!!")


class ConfLogServ(ConfLog):
    """ the server process of the log system
    """
    serv_list: Optional[list] = None
    fn_log: str = "invest.log"

    def __init__(self, proc_queue: Queue, proc_list: Optional[list]) -> None:
        super().__init__(proc_queue)
        if ConfLogServ.serv_list is None:
            ConfLogServ.serv_list = proc_list
        if self.proc_queue is not None:
            self.setup_log_system()

    @classmethod
    def colorize(cls, msg: str, clr: str) -> str:
        """Setup HTML color sign

        :param msg: input msg
        :type msg: str
        :param clr: HTML color
        :type clr: str
        :return: colorized msg
        :rtype: str
        """
        str_header: str = '<i class="bi bi-lightbulb-fill class_clr">'
        str_tail: str = '</i>'
        return str_header.replace("class_clr", clr) + str_tail + msg

    @classmethod
    def setup_log_system(cls) -> None:
        """ Setup the python logging system
        """
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        # formatter = logging.Formatter(
        #     '[%(levelname)1.1s %(asctime)s %(module)s:%(lineno)d] %(message)s',
        #     datefmt='%Y%m%d %H:%M:%S')

        char_handle = logging.StreamHandler()
        char_handle.setLevel(logging.DEBUG)
        # ch.setFormatter(formatter)

        # log_filename = datetime.datetime.now().strftime("%Y-%m-%d_%H_%M_%S.log")
        log_filename = cls.fn_log
        file_handle = logging.FileHandler(log_filename)
        file_handle.setLevel(logging.DEBUG)
        # fh.setFormatter(formatter)

        logger.addHandler(char_handle)
        logger.addHandler(file_handle)

    @classmethod
    def _paser_msg(cls, msg: list) -> None:
        if msg is not None:
            a_sym, a_txt, i_html = msg

            # for log string
            log_fmt = cls._xfr_dir.get(a_sym, cls._xfr_dir["info"])
            log_msg: str = a_txt if i_html else log_fmt[cls._xfr_sym] + a_txt
            log_fmt[cls._xfr_func](log_msg)
            # for html list log_msg is correct string
            if i_html:
                # colorize
                # append to list
                if cls.serv_list is not None:
                    cls.serv_list.append(
                        cls.colorize(log_msg, log_fmt[cls._xfr_color]))

            elif log_fmt[cls._xfr_to_html]:
                # html encoding
                log_msg = escape(log_msg)
                # colorize
                # append to list
                if cls.serv_list is not None:
                    cls.serv_list.append(
                        cls.colorize(log_msg, log_fmt[cls._xfr_color]))

            # logging.debug(msg[0] + msg[1])
            # if cls.serv_list is not None:
            #     cls.serv_list.append(msg[1])
        else:
            print("ConfLogServ:_paser_msg msg is not exist!!")

    @classmethod
    def start_serv(cls) -> None:
        """ start server
        """
        # run forever
        print("start_serv for log!")
        while True:
            # consume a log message, block until one arrives
            if cls.proc_queue is not None:
                message = cls.proc_queue.get()
                # check for shutdown
                if message is None:
                    # logging.shutdown() useless
                    # need to flush all streams, very important
                    logger = logging.getLogger()
                    _ = [x.close() for x in logger.handlers]
                    _ = [logger.removeHandler(x) for x in logger.handlers]
                    break
                # log the message
                cls._paser_msg(message)
            else:
                print("ConfLogServ:start_serv: no queue is exist!")

    @staticmethod
    def fork_log_serv(srv_q: Queue, srv_l: list) -> None:
        """ start server with all options

        :param srv_q: queue of server
        :type srv_q: Queue
        :param srv_l: log list of server
        :type srv_l: list
        """
        log_serv = ConfLogServ(srv_q, srv_l)
        log_serv.start_serv()


if __name__ == '__main__':
    # create the shared queue
    queue = Queue()
    # start manager list
    with Manager() as manager:
        log_list = manager.list()
        # start the logger process
        logger_p = Process(target=ConfLogServ.fork_log_serv,
                           args=(
                               queue,
                               log_list,
                           ))
        logger_p.start()

        # report initial message
        print('Main process started.')

        # configure child processes
        processes = [
            Process(target=ConfLog.test_task, args=(queue, )) for i in range(4)
        ]

        # start child processes
        for process in processes:
            process.start()
        # wait for child processes to finish
        for process in processes:
            process.join()

        # report final message
        print('Main process done.')
        # shutdown the queue correctly
        ConfLog.stop_log_serv(logger_p, queue)
        # print out the list
        print('Print out log_list!!')
        for msg_txt in log_list:
            print(msg_txt)

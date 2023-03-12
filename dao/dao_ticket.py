""" Download the historical data from Yahoo Finance
need remove eeb auo DRYS
"""

#import python libraries
from concurrent.futures import ThreadPoolExecutor
import os
from threading import Lock
import time
from typing import Tuple, Union, List

#import third party libraries
import yfinance as yf

#import yourself libraries
from bases.conf_const import ConfConst
from dao.dao_csv import DaoCsv
from dao.dao_file import DaoFile

#constant definition
# global_variable


class DaoTicket:
    """ Download single ticket from Yahoo Fianace
    """
    def __init__(self, ticket: str) -> None:
        """Constructor

        :param ticket: stock symbol in Yahoo Finance
        :type ticket: str
        """
        self.ticket: str = ticket
        self.fn_save: str = ConfConst.DATA_DIR + ticket + '.csv'
        self.fn_update: str = ConfConst.UPDATE_DIR + ticket + '.csv'
        self.csv_update: DaoCsv
        self.csv_save: DaoCsv
        self.data_update: List[List[str]]
        self.data_save: List[List[str]]

    def _translate_data_update(self) -> None:
        """read fn_update and translate to correct form

        test OK
        """
        self.csv_update: DaoCsv = DaoCsv(self.fn_update)
        data1: List[List[str]] = self.csv_update.read_all()
        data2: List[List[str]] = [x[:6] for x in data1]
        for a_row in data2:
            a_row[0] = "/".join(a_row[0].split("-"))
        # print("len: ", len(data2), " elements: ", len(data2[0]))
        self.data_update = data2

    def download(self):
        """ download historical data by yfinance
        """
        # print('processing: ' + self.ticket)
        # 填入股票代碼後直接下載成 csv 格式
        _stock = yf.Ticker(self.ticket)

        if os.path.exists(self.fn_save):
            # download short sequence
            # print("download 3 months")
            _stock.history(period='1mo').to_csv(self.fn_update)
        else:
            # download long sequence
            # print("download 6 months")
            # date from '2002-01-01'
            _stock.history(start='2002-01-01').to_csv(self.fn_update)

        # wait a little time, prevent busy, move to RepoTickets
        # time.sleep(0.5)

    @staticmethod
    def clean_data(rows: List[List[str]]) -> List[List[str]]:
        """ remove wrong row in file

        Args:
            rows (List[List[str]]): input csv data

        Returns:
            List[List[str]]: filtered csv data
        """
        clean_list: List[List[str]] = []
        for row in rows:
            # check every items
            need_loop: bool = False
            for item in row:
                #remove all empty row
                if item.strip() == "":
                    need_loop = True
                    break
            if need_loop:
                continue
            #check first item is comment
            if row[0][0] == "#":
                continue
            #check volume==0 need check ticket
            # if float(row[5])==0:
            #     continue
            clean_list.append(row)
        return clean_list

    def merge_csv(self) -> Tuple[bool, str]:
        """read fn_update data and translate to correct format

        :raises NotImplementedError: not test
        :return: merge result. True mean merge success
        :rtype: Tuple[bool, str]
        """
        self._translate_data_update()
        if len(self.data_update) < 3:
            # print(self.ticket, ": no enough data or not found!")
            return (False, self.ticket)

        self.csv_save = DaoCsv(self.fn_save)
        if not os.path.exists(self.fn_save):
            # write to fn_save
            self.csv_save.write_all(DaoTicket.clean_data(self.data_update[1:]))
            return (True, self.ticket)

        self.data_save = self.csv_save.read_all()
        # check the last element
        last_time: str = self.data_save[-1][0]
        #print(self.ticket, ": len: ", len(self.data_save), " last item: ", last_time)
        try:
            last_idx = [x[0] for x in self.data_update].index(last_time)
        except ValueError:
            return (False, self.ticket)
        #index found
        last_residual = self.data_update[last_idx + 1:]
        if len(last_residual) == 0:
            # print(self.ticket, ": no data updated.")
            return (True, self.ticket)

        # print("old close: ", self.data_save[-1][1], " new close: ", self.data_update[last_idx][1])
        delta_val: float = float(self.data_save[-1][1]) - float(
            self.data_update[last_idx][1])
        if abs(delta_val) > 0.01:
            #raise NotImplementedError
            print(self.ticket,
                  ": something wrong, maybe reload all data. delta: ",
                  delta_val)
            return (False, self.ticket)
        self.data_save += last_residual
        self.csv_save.write_all(DaoTicket.clean_data(self.data_save))
        return (True, self.ticket)


class RepoTickets:
    """ Download the historical data from Yahoo Finance
    for multiple tickets
    """
    mthreads_lock: Lock = Lock()

    def __init__(self, tickets: Union[str, List[str]]) -> None:
        self.tickets_list: List[str] = []
        self.failed_list: list[str] = []  # no error exception

        if isinstance(tickets, str):
            self.tickets_list = tickets.split()
        if isinstance(tickets, list):
            self.tickets_list += tickets

        # tickets_list must be unique
        self.tickets_list = list(set(self.tickets_list))
        # print("input tickets: " + " ".join(self.tickets_list))

    @staticmethod
    def _download(ticket: str) -> Tuple[bool, str]:
        # print(ticket, ": enter thread.")
        t_job = DaoTicket(ticket)
        with RepoTickets.mthreads_lock:
            #print(ticket, ": enter lock.")
            t_job.download()
            time.sleep(0.5)
            #print(ticket, ": leave lock.")

        #print(ticket, ": enter callback.")
        return t_job.merge_csv()

    def download(self) -> None:
        """Download historical data by mutithreading from tickets_list

           check the result from self.failed_list
        """
        start_time = time.monotonic()
        # self.tickets_list
        with ThreadPoolExecutor(max_workers=5) as pool:
            results = pool.map(RepoTickets._download, self.tickets_list)
        self.failed_list = [a_row[1] for a_row in results if not a_row[0]]
        print("total tickets count: ", len(self.tickets_list), end=" ")
        print("total time cost:", time.monotonic() - start_time)
        print("fail_list:", self.failed_list)

    def proc_failed_list(self) -> None:
        """ process the failed_list
            if fail again, something wrong
        """
        if len(self.failed_list) == 0:
            return
        #remove all fail file in save directory
        for a_fail_ticket in self.failed_list:
            fname: str = ConfConst.DATA_DIR + a_fail_ticket + '.csv'
            dao_fail = DaoFile(fname)
            if dao_fail.is_exist():
                # print("remove: ", fname)
                dao_fail.remove()
        #download again
        self.tickets_list = self.failed_list
        self.failed_list = []
        self.download()


#main function  將最高層的function以兩個空白行分隔
if __name__ == '__main__':
    print("DATA_DIR: ", ConfConst.DATA_DIR)
    print("UPDATE_DIR: ", ConfConst.UPDATE_DIR)
    # a_ticket: str = "VT"
    # a_job = DaoTicket(a_ticket)
    # a_job.download()
    # # a_job.translate_data_update()
    # a_job.merge_csv()
    # repo = RepoTickets("VAW VCR VDC VT VTI AAAAPL")
    # #repo=RepoTickets("AAAAPL")
    # repo.download()

    dao_symbols = DaoFile("D:\\homer\\Documents\\invest\\symbols\\symbols.txt")
    str_symbols = dao_symbols.read_all()
    repo = RepoTickets(str_symbols)
    repo.download()
    repo.proc_failed_list()
    print("finished!")

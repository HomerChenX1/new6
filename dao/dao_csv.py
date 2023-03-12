""" for csv file read/write
Reference:
    import雜談之三———sys.path的洪荒之時
    https://ithelp.ithome.com.tw/m/articles/10196901
"""

#import python libraries
# import os
import sys
from typing import List
import csv

#import third party libraries

#import yourself libraries
# need this if pkg or .dao from invest
# need dao from if execute from this file
from dao.dao_file import DaoFile
#from bases.conf import ConfigData

#constant definition

# global_variable


class DaoCsv(DaoFile):
    """_summary_
    """
    def __init__(self, fname: str, enc_str: str = "cp950") -> None:
        super().__init__(fname, enc_str)
        self.delim: str = ","

    def read_all(self) -> List[List[str]]:
        """ Read data from the assign CSV file

        test OK

        :return: return data list
        :rtype: List[List[str]]
        """
        __retlist: List[List[str]] = []
        try:
            with open(self.fname, self.mode_str) as csvfile:
                reader = csv.reader(csvfile)
                # for x in reader:
                #     if x != [] and x[0][0] != '#' and x[0] != '':
                #         retlist.append(x)
                __retlist = [
                    x for x in reader
                    if (x != [] and x[0][0] != '#' and x[0] != '')
                ]
        except FileNotFoundError as err:
            print(err)
        return __retlist

    def write_all(self, data_s: List[List[str]]) -> None:
        """ write string rows to CSV file in windows format

        test OK

        :param csvRows: input data
        :type csvRows: List[List[str]]
        """
        with open(self.fname, 'w', newline="",
                  encoding=self.enc_str) as csvfile:
            writer = csv.writer(csvfile, delimiter=self.delim)
            writer.writerows(data_s)

    def write_symbols(self, symbols: List[str]) -> None:
        """ write the symbols file in Windows format
        FIXME : not test

        :param symbols: the list of all symbols
        :type symbols: List[str]
        """
        with open(self.fname, 'w', newline="\r\n",
                  encoding=self.enc_str) as symfile:
            symfile.write(" ".join(symbols))


#main function  將最高層的function以兩個空白行分隔
if __name__ == '__main__':
    print("path is ")
    print(sys.path)
    # print(ConfigData.WEEK_DAYS)
    dao_csv = DaoCsv("D:\\homer\\Documents\\invest\\new6\\dao\\config.csv")
    new_data = dao_csv.read_all()
    print(new_data[0])

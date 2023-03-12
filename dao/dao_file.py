""" This module to process the basic CRUD of a file
  now is working for a text file
  codec ref codecs — Codec registry and base classes
  https://docs.python.org/3/library/codecs.html#codec-base-classes

  Todo Tree Extension: http://jonasbn.github.io/til/vscode/todo_tree_extension.html

WARN: This is a warning, be aware

TODO: At some point this should be done

FIXME: This is clearly a bug, please fix

HACK: Be warned this is indeed a hack

BUG: A big bug

REF: http://jonasbn.github.io/til/vscode/todo_tree_extension.html

XXX: to default
"""

#import python libraries
import os

#import third party libraries
#import yourself libraries
#constant definition
# global_variable


class DaoFile:
    """ Initialize
        self.fname
        self.enc_str :
            REF: https://docs.python.org/3/library/codecs.html#codec-base-classes
        self.mode_str :
            'r'=read 'w'=write 'a':append 'r+'=read/write from head
    """
    def __init__(self,
                 fname: str,
                 enc_str: str = "utf-8",
                 mod_str: str = 'r+') -> None:
        self.fname: str = fname
        self.enc_str = enc_str
        self.mode_str = mod_str

    def read_all(self) -> str:
        """ read all contents of the file to a string

        :return: file contents
        :rtype: str
        """
        __data_str: str = ""
        with open(self.fname, self.mode_str, encoding=self.enc_str) as fhandle:
            __data_str = fhandle.read()

        return __data_str

    def write_all(self, data_s: str) -> int:
        """ write string to a file

        :param data_str: data to file
        :type data_str: str
        :return: write count. if zero , mean something wrong
        :rtype: int
        """
        __cnt: int = 0
        with open(self.fname, self.mode_str, encoding=self.enc_str) as fhandle:
            __cnt = fhandle.write(data_s)
        return __cnt

    def is_exist(self) -> bool:
        """ check the file exist or not

        :return: true for exist
        :rtype: bool
        """
        return os.path.exists(self.fname)

    def remove(self) -> None:
        """ delete a file
        """
        os.remove(self.fname)


#main function  將最高層的function以兩個空白行分隔
if __name__ == '__main__':
    # for the test code
    dao_file = DaoFile("D:\\homer\\Documents\\invest\\new6\\dao\\config.csv",
                       "cp950")
    if dao_file.is_exist():
        print("file is exist!")
        data_str: str = dao_file.read_all()
        print(data_str)
        dao_file.mode_str = "a"
        dao_file.write_all("測試中")
    else:
        print("file not exist!")

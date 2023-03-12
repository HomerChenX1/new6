""" For FTP client

reference:
    FTP: https://www.796t.com/content/1549146064.html
         https://dataxujing.github.io/ftplib/
    FTPS: https://gist.github.com/Ryanb58/43e8bf5a8935405c455c5b41f8f8a0a3
"""

#import python libraries
from ftplib import FTP, FTP_TLS
from typing_extensions import Self

#import third party libraries

#import yourself libraries

#constant definition
# global_variable


class DaoFtpClient:
    """transfer a file by the FTP client interface
    """
    def __init__(self, ip: str, usr: str, pwd: str, is_ssl=False) -> None:
        """Constructor

        :param ip: IP
        :type ip: str
        :param usr: user name
        :type usr: str
        :param pwd: password
        :type pwd: str
        :param is_ssl: is FTPS? defaults to False
        :type is_ssl: bool, optional
        """
        self.local_path:str="D:\\homer\\Documents\\invest\\new5\\"
        self.bufsize = 1024

        if is_ssl:
            self.ftp = FTP_TLS(ip, usr, pwd)
            self.ftp.prot_p()
        else:
            self.ftp = FTP(ip, usr, pwd)
        self.ftp.set_debuglevel(2)
        # 重新設定下編碼方式
        # self.ftp.encoding = 'Big5'
        self.ftp.dir()

    def bye(self) -> None:
        """Stop and close FTP
        """
        self.ftp.set_debuglevel(0)
        self.ftp.quit()

    def change_remote_dir(self, dname: str) -> Self:
        """change remote directory

        :param dname: the wanted directory
        :type dname: str
        :return: self
        :rtype: Self
        """
        self.ftp.cwd(dname)
        # self.ftp.dir() if use dir , the working directory will goto root,
        # can not find reason
        self.ftp.retrlines('LIST')
        return self

    def get_file_from_host(self, fname: str) -> Self:
        """ get a file from remote

        :param fname: remote file name
        :type fname: str
        :return: self
        :rtype: Self
        """
        with open(self.local_path+fname, 'wb') as fhandle:
            self.ftp.retrbinary('RETR ' + fname, fhandle.write, self.bufsize)
        return self

    def put_file_to_host(self, fname: str) -> Self:
        """send a file to remote

        :param fname: local filename
        :type fname: str
        :return: self
        :rtype: Self
        """
        with open(self.local_path+fname, 'rb') as fhandle:
            self.ftp.storbinary('STOR ' + fname, fhandle, self.bufsize)
        return self


def __main_test() -> None:
    """test code
    """
    a_ftp = DaoFtpClient("192.168.0.1", "HomerTp", "87109az")
    a_ftp.change_remote_dir("G/Download/data")
    # a_ftp.get_file_from_host("pwd.pdf")
    # a_ftp.get_file_from_host("台南.txt")
    a_ftp.put_file_to_host("invest.htm")
    a_ftp.bye()


#main function  將最高層的function以兩個空白行分隔
if __name__ == '__main__':
    __main_test()

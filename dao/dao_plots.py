"""Plot data
"""
#import python libraries
from typing import List

#import third party libraries
import numpy as np
from numpy.typing import ArrayLike
import matplotlib.pyplot as plt
#import yourself libraries
#constant definition
#global_variable


class DaoPlots():
    """Draw different plots
    """
    fname: str = "dao_plots.png"

    @classmethod
    def draw_lines(cls,
                   sym: str,
                   a_idx: ArrayLike,
                   argv: List[ArrayLike],
                   is_show: bool = False) -> None:
        """Draw lines

        :param argc: count of lines
        :type argc: int
        :param is_show: True in main process, else only output PNG
        :type argc: bool
        """
        cls.fname = sym + ".png"
        temp_max = [np.max(a_array) for a_array in argv]
        temp_min = [np.min(a_array) for a_array in argv]
        temp_len = [len(a_array) for a_array in argv]  #type: ignore
        temp_max = max(temp_max)
        temp_min = min(temp_min)
        temp_len = min(temp_len)
        new_argv = [a_array[:temp_len] for a_array in argv]  #type: ignore
        temp_avg = (temp_max + temp_min) / 2
        temp_span = (temp_max - temp_min) / 2
        temp_idx = a_idx[:temp_len] * temp_span + temp_avg  #type: ignore

        x_vals = range(temp_len, 0, -1)
        # plt.ioff()
        fig = plt.figure()
        plt.title(cls.fname)
        plt.plot(x_vals, temp_idx)
        for a_array in new_argv:
            plt.plot(x_vals, a_array)
        if is_show:
            plt.show()
        else:
            fig.savefig(cls.fname)


#main function  將最高層的function以兩個空白行分隔
if __name__ == '__main__':
    x = [1, 2, 3, 4, 5]
    # 畫出顏色紅色、圓形錨點、虛線、粗細 2、資料點大小 6 的線條
    plt.plot(x, 'ro--', linewidth=2, markersize=6)
    plt.title('Legend inside')
    plt.show()

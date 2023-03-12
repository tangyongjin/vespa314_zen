import matplotlib.pyplot as plt
from IPython.display import clear_output, display

from ZenMaster import ZenMaster

from .PlotDriver import PlotDriver


class AnimateDriver:
    def __init__(self, chan: ZenMaster, plot_config=None, plot_para=None):
        if plot_config is None:
            plot_config = {}
        if plot_para is None:
            plot_para = {}
        for _ in chan.step_load():
            g = PlotDriver(chan, plot_config, plot_para)
            clear_output(wait=True)
            display(g.figure)
            plt.close(g.figure)

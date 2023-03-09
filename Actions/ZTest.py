import os
from Chan import CChan
from ChanConfig import CChanConfig
from Common.CEnum import AUTYPE, DATA_SRC, KL_TYPE
from Plot.AnimatePlotDriver import CAnimateDriver
from Plot.PlotDriver import CPlotDriver
from Tools.DebugTool import cprint
from colorama import Fore, Back, Style

# import echarts
from pyecharts.charts import *
from pyecharts.components import Table
from pyecharts import options as opts
from pyecharts.commons.utils import JsCode
import random
import datetime
from pyecharts.globals import ThemeType
from pyecharts.globals import CurrentConfig
from pyecharts.charts import   EffectScatter 

async def ZTest():
        from pyecharts.globals import CurrentConfig
        json_compatible_item_data =  {"code":"200","charts":['aa','bb']}
        # return json_compatible_item_data
        CurrentConfig.ONLINE_HOST = "https://cdn.kesci.com/lib/pyecharts_assets/"

        # %matplotlib inline
        # %pylab inline

        code = "sz.000001"
        begin_time = "2018-01-01"
        end_time = None
        data_src = DATA_SRC.BAO_STOCK
        lv_list = [KL_TYPE.K_DAY]

        config = CChanConfig({
            "bi_strict": True,
            "triger_step": False,
            "skip_step": 0,
            "divergence_rate": float("inf"),
            "bsp2_follow_1": False,
            "bsp3_follow_1": False,
            "min_zs_cnt": 0,
            "bs1_peak": False,
            "macd_algo": "peak",
            "bs_type": '1,2,3a,1p,2s,3b',
            "print_warming": True,
        })

        plot_config = {
            "plot_kline": True,
            # "plot_kline": False,
            "plot_kline_combine": True,
            "plot_bi": True,
            # "plot_bi": False,
            # 'plot_boll': True,
            # "plot_seg": False,
            "plot_seg": True,
            
            # "plot_eigen": True,
            # "plot_segseg": False,    
            # "plot_zs": True,
            # "plot_zs": False,
            # "plot_macd": True,
            # "plot_mean": False,
            "plot_channel": False,
            # "plot_bsp": True,
            # "plot_bsp": False,
            "plot_extrainfo": True,
        }

        plot_para = {
            "seg": {
            },
            "bi": {
                # "show_num": True,
                # "disp_end": True,
            },
            "figure": {
                # "x_range": 50,
            },
        }
        chan = CChan(
            code=code,
            begin_time=begin_time,
            end_time=end_time,
            data_src=data_src,
            lv_list=lv_list,
            config=config,
            autype=AUTYPE.QFQ,
        )

        if not config.triger_step:
            
            plot_driver = CPlotDriver(
                chan,
                plot_config=plot_config,
                plot_para=plot_para,
            )
        else:
            plot_driver=CAnimateDriver(
                chan,
                plot_config=plot_config,
                plot_para=plot_para,
            )

        cprint(  " notebook.ipynb:100:plot_driver",pcolor= Fore.RED)    
        return plot_driver.echartsData




 

 
 
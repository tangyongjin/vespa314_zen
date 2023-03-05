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
            # "plot_bi": True,
            # "plot_bi": False,
            # 'plot_boll': True,
            # "plot_seg": False,
            # "plot_seg": True,
            
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
        print( plot_driver.version) 
        print( type (plot_driver.echartsData))

        kline = Kline()
        kline.set_global_opts(
                xaxis_opts=opts.AxisOpts(is_scale=True),
                
                yaxis_opts=opts.AxisOpts(
                    is_scale=True,
                    splitarea_opts=opts.SplitAreaOpts(
                        is_show=True, areastyle_opts=opts.AreaStyleOpts(opacity=1)
                    ),
                ),
                tooltip_opts=opts.TooltipOpts(is_show=True,
                                                   # 鼠标移动或者点击时触发
                                                   trigger_on="mousemove|click"),
                datazoom_opts=[opts.DataZoomOpts(pos_bottom="-2%")],
            )


        per_js = """function (param) {return param.substring(2,10);}"""

       
        kline.add_xaxis(plot_driver.echartsData['x'])
        kline.add_yaxis("K 线图", plot_driver.echartsData['y'])
        kline.set_global_opts(title_opts=opts.TitleOpts(title="xxx"),
                                    xaxis_opts=opts.AxisOpts(name_rotate=60,
                                                            # axislabel_opts=opts.LabelOpts(rotate=65, formatter=JsCode(per_js)) ,
                                                            # axislabel_opts={"rotate":45}
                                                            ))
                


        grid_chart = Grid(init_opts=opts.InitOpts(width='100%', height='800px' , theme='dark'))
        grid_chart.add(
            kline,
            grid_opts=opts.GridOpts(width="100%", height="95%", pos_left='2%', ),
        )
        grid_chart.render_notebook()    
        jsons=grid_chart.dump_options();
        return plot_driver.echartsData;




 

 
 
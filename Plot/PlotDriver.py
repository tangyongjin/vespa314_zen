import inspect
from typing import Dict, List, Optional, Tuple, Union
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from Tools.DebugTool import cprint
from Chan import CChan
from Common.CEnum import BI_DIR, FX_TYPE, KL_TYPE, KLINE_DIR, TREND_TYPE
from Common.ChanException import CChanException, ErrCode
from .PlotMeta import CBi_meta, CChanPlotMeta, CZS_meta


def reformat_plot_config(plot_config: Dict[str, bool]):
    """
    兼容不填写`plot_`前缀的情况
    """
    def _format(s):
        return s if s.startswith("plot_") else f"plot_{s}"

    return {_format(k): v for k, v in plot_config.items()}


def parse_single_lv_plot_config(plot_config: Union[str, dict, list]) -> Dict[str, bool]:
    """
    返回单一级别的plot_config配置
    """
    if isinstance(plot_config, dict):
        return reformat_plot_config(plot_config)
    elif isinstance(plot_config, str):
        return reformat_plot_config(dict([(k.strip().lower(), True) for k in plot_config.split(",")]))
    elif isinstance(plot_config, list):
        return reformat_plot_config(dict([(k.strip().lower(), True) for k in plot_config]))
    else:
        raise CChanException("plot_config only support list/str/dict", ErrCode.PLOT_ERR)


def parse_plot_config(plot_config: Union[str, dict, list], lv_list: List[KL_TYPE]) -> Dict[KL_TYPE, Dict[str, bool]]:
    """
    支持：
        - 传入字典
        - 传入字符串，逗号分割
        - 传入数组，元素为各个需要画的笔的元素
        - 传入key为各个级别的字典
        - 传入key为各个级别的字符串
        - 传入key为各个级别的数组
    """
    if isinstance(plot_config, dict):
        if all(isinstance(_key, str) for _key in plot_config.keys()):  # 单层字典
            return {lv: parse_single_lv_plot_config(plot_config) for lv in lv_list}
        elif all(isinstance(_key, KL_TYPE) for _key in plot_config.keys()):  # key为KL_TYPE
            for lv in lv_list:
                assert lv in plot_config
            return {lv: parse_single_lv_plot_config(plot_config[lv]) for lv in lv_list}
        else:
            raise CChanException("plot_config if is dict, key must be str/KL_TYPE", ErrCode.PLOT_ERR)
    return {lv: parse_single_lv_plot_config(plot_config) for lv in lv_list}


def set_x_tick(ax, x_limits, tick):
    ax.set_xlim(x_limits[0], x_limits[1]+1)
    ax.set_xticks(range(x_limits[0], x_limits[1], max([1, int((x_limits[1]-x_limits[0])/10)])))
    ax.set_xticklabels([tick[i] for i in ax.get_xticks()], rotation=20)


def cal_y_range(meta: CChanPlotMeta, ax):
    x_begin = ax.get_xlim()[0]
    y_min = float("inf")
    y_max = float("-inf")
    for klc_meta in meta.klc_list:
        if klc_meta.klu_list[-1].idx < x_begin:
            continue  # 不绘制范围外的
        if klc_meta.high > y_max:
            y_max = klc_meta.high
        if klc_meta.low < y_min:
            y_min = klc_meta.low
    return (y_min, y_max)


def create_figure(plot_macd: Dict[KL_TYPE, bool], figure_config, lv_lst: List[KL_TYPE]) -> Tuple[Figure, Dict[KL_TYPE, List[Axes]]]:
    """
    返回：
        - Figure
        - Dict[KL_TYPE, List[Axes]]: 如果Axes长度为1, 说明不需要画macd, 否则需要
    """
    default_w, default_h = 24, 10
    macd_h_ration = figure_config.get('macd_h', 0.3)
    w = figure_config.get('w', default_w)
    h = figure_config.get('h', default_h)

    total_h = 0
    gridspec_kw = []
    sub_pic_cnt = 0
    for lv in lv_lst:
        if plot_macd[lv]:
            total_h += h*(1+macd_h_ration)
            gridspec_kw.extend((1, macd_h_ration))
            sub_pic_cnt += 2
        else:
            total_h += h
            gridspec_kw.append(1)
            sub_pic_cnt += 1
    
    plt.rcParams['font.sans-serif']=['SimHei'] #用来正常显示中文标签
    plt.rcParams['axes.unicode_minus'] = False #用来正常显示负号
    # plt.title(u"Zen-K汉字")        
    plt.style.use('ggplot')
    
    figure, axes = plt.subplots(
        sub_pic_cnt,
        1,
        figsize=(w, total_h),
        gridspec_kw={'height_ratios': gridspec_kw}
    )
    
    
    try:
        axes[0]
    except Exception:  # 只有一个级别，且不需要画macd
        axes = [axes]

    axes_dict: Dict[KL_TYPE, List[Axes]] = {}
    idx = 0
    for lv in lv_lst:
        if plot_macd[lv]:
            axes_dict[lv] = axes[idx: idx+2]  # type: ignore
            idx += 2
        else:
            axes_dict[lv] = [axes[idx]]  # type: ignore
            idx += 1
    assert idx == len(axes)
    return figure, axes_dict


def cal_x_limit(meta: CChanPlotMeta, x_range):
    X_LEN = meta.klu_len
    return [X_LEN - x_range, X_LEN - 1] if x_range and X_LEN > x_range else [0, X_LEN - 1]


def set_grid(ax, config):
    if config is None:
        return
    if config == "xy":
        ax.grid(True)
        return
    if config in ("x", "y"):
        ax.grid(True, axis=config)
        return
    raise CChanException(f"unsupport grid config={config}", ErrCode.PLOT_ERR)


def GetPlotMeta(chan: CChan, figure_config) -> List[CChanPlotMeta]:
    plot_metas = [CChanPlotMeta(chan[kl_type]) for kl_type in chan.lv_list]
    if figure_config.get("only_top_lv", False):
        plot_metas = [plot_metas[0]]
    return plot_metas


class CPlotDriver:
    def __init__(self, chan: CChan, plot_config: Union[str, dict, list] = '', plot_para=None):
        cprint("PlotDriver.py:156, init-->plot_para")
        print(plot_para)
        if plot_para is None:
            plot_para = {}
        figure_config: dict = plot_para.get('figure', {})

        plot_config = parse_plot_config(plot_config, chan.lv_list)
        plot_metas = GetPlotMeta(chan, figure_config)
        self.lv_lst = chan.lv_list[:len(plot_metas)]

        cprint("PlotDriver.py:164,初始化plot_driver")

        x_range = self.GetRealXrange(figure_config, plot_metas[0])
        plot_macd: Dict[KL_TYPE, bool] = {kl_type: conf.get("plot_macd", False) for kl_type, conf in plot_config.items()}
        self.figure, axes = create_figure(plot_macd, figure_config, self.lv_lst)

        sseg_begin = 0
        slv_seg_cnt = plot_para.get('seg', {}).get('sub_lv_cnt', None)
        sbi_begin = 0
        slv_bi_cnt = plot_para.get('bi', {}).get('sub_lv_cnt', None)
        srange_begin = 0
        assert slv_seg_cnt is None or slv_bi_cnt is None, "you can set at most one of seg_sub_lv_cnt/bi_sub_lv_cnt"

        for meta, lv in zip(plot_metas, self.lv_lst):  # type: ignore
            ax = axes[lv][0]
            ax_macd = None if len(axes[lv]) == 1 else axes[lv][1]
            set_grid(ax, figure_config.get("grid", "xy"))
            # 设置标题位置,颜色
            ax.set_title(f"{chan.code}/{lv.name.split('K_')[1]}", fontsize=16, loc='center', color='r')

            x_limits = cal_x_limit(meta, x_range)
            if lv != self.lv_lst[0]:
                if sseg_begin != 0 or sbi_begin != 0:
                    x_limits[0] = max(sseg_begin, sbi_begin)
                elif srange_begin != 0:
                    x_limits[0] = srange_begin
            set_x_tick(ax, x_limits, meta.datetick)
            if ax_macd:
                set_x_tick(ax_macd, x_limits, meta.datetick)
            self.y_min, self.y_max = cal_y_range(meta, ax)  # 需要先设置 x_tick后计算

            self.DrawSubFig(plot_config[lv], meta, ax, lv, plot_para, ax_macd, x_limits)

            if lv != self.lv_lst[-1]:
                sseg_begin = meta.sub_last_kseg_start_idx(slv_seg_cnt)
                sbi_begin = meta.sub_last_kbi_start_idx(slv_bi_cnt)
                if x_range != 0:
                    srange_begin = meta.sub_range_start_idx(x_range)

            ax.set_ylim(self.y_min, self.y_max)

    def GetRealXrange(self, figure_config, meta: CChanPlotMeta):
        x_range = figure_config.get("x_range", 0)
        bi_cnt = figure_config.get("x_bi_cnt", 0)
        seg_cnt = figure_config.get("x_seg_cnt", 0)
        x_begin_date = figure_config.get("x_begin_date", 0)
        if x_range != 0:
            assert bi_cnt == 0 and seg_cnt == 0 and x_begin_date == 0, "x_range/x_bi_cnt/x_seg_cnt/x_begin_date can not be set at the same time"
            return x_range
        if bi_cnt != 0:
            assert x_range == 0 and seg_cnt == 0 and x_begin_date == 0, "x_range/x_bi_cnt/x_seg_cnt/x_begin_date can not be set at the same time"
            X_LEN = meta.klu_len
            if len(meta.bi_list) < bi_cnt:
                return 0
            x_range = X_LEN-meta.bi_list[-bi_cnt].begin_x
            return x_range
        if seg_cnt != 0:
            assert x_range == 0 and bi_cnt == 0 and x_begin_date == 0, "x_range/x_bi_cnt/x_seg_cnt/x_begin_date can not be set at the same time"
            X_LEN = meta.klu_len
            if len(meta.seg_list) < seg_cnt:
                return 0
            x_range = X_LEN-meta.seg_list[-seg_cnt].begin_x
            return x_range
        if x_begin_date != 0:
            assert x_range == 0 and bi_cnt == 0 and seg_cnt == 0, "x_range/x_bi_cnt/x_seg_cnt/x_begin_date can not be set at the same time"
            x_range = 0
            for date_tick in meta.datetick[::-1]:
                if date_tick >= x_begin_date:
                    x_range += 1
                else:
                    break
            return x_range
        return x_range

    def DrawSubFig(self, plot_config: Dict[str, bool], meta, ax: Axes, lv, plot_para, ax_macd: Optional[Axes], x_limits):
        cprint("PlotDriver.py:238,绘制元素, plot_config.get(某项配置,缺省False)  ")
        cprint('plot_config type:' +type (plot_config).__name__ )
        print(plot_config)
        cprint('plot_para type:'+ type (plot_para).__name__)
        print( plot_para) 
        cprint("debug-End")
         
        if plot_config.get("plot_kline", False):
            self.draw_klu(meta, ax, **plot_para.get('kl', {}))
        if plot_config.get("plot_kline_combine", False):
            self.draw_klc(meta, ax, **plot_para.get('klc', {}) )
        if plot_config.get("plot_bi", False):
            self.draw_bi(meta, ax, lv, **plot_para.get('bi', {}))
        if plot_config.get("plot_seg", False):
            self.draw_seg(meta, ax, lv, **plot_para.get('seg', {}))
        if plot_config.get("plot_segseg", False):
            self.draw_segseg(meta, ax, **plot_para.get('segseg', {}))
        if plot_config.get("plot_eigen", False):
            self.draw_eigen(meta, ax, **plot_para.get('eigen', {}))
        if plot_config.get("plot_zs", False):
            self.draw_zs(meta, ax, **plot_para.get('zs', {}))
        if plot_config.get("plot_segzs", False):
            self.draw_segzs(meta, ax, **plot_para.get('segzs', {}))
        if plot_config.get("plot_macd", False):
            assert ax_macd is not None
            self.draw_macd(meta, ax_macd, x_limits, **plot_para.get('macd', {}))
        if plot_config.get("plot_mean", False):
            self.draw_mean(meta, ax, **plot_para.get('mean', {}))
        if plot_config.get("plot_channel", False):
            self.draw_channel(meta, ax, **plot_para.get('channel', {}))
        if plot_config.get("plot_boll", False):
            self.draw_boll(meta, ax, **plot_para.get('boll', {}))
        if plot_config.get("plot_bsp", False):
            self.draw_bs_point(meta, ax, **plot_para.get('bsp', {}))
        if plot_config.get("plot_segbsp", False):
            self.draw_seg_bs_point(meta, ax, **plot_para.get('seg_bsp', {}))

    def ShowDrawFuncHelper(self):
        # 写README的时候显示所有画图函数的参数和默认值
        for func in dir(self):
            if not func.startswith("draw_"):
                continue
            show_func_helper(eval(f'self.{func}'))

    def save2img(self, path):
        plt.savefig(path, bbox_inches='tight')

    def draw_klu(self, meta: CChanPlotMeta, ax: Axes, width=0.4, rugd=True, plot_mode="kl"):
        cprint ("PlotDriver.py: 288,绘制K线图")
        # rugd: red up green down
        up_color = 'r' if rugd else 'g'
        down_color = 'g' if rugd else 'r'

        x_begin = ax.get_xlim()[0]
        _x, _y = [], []
        for kl in meta.klu_iter():
            i = kl.idx
            if i+width < x_begin:
                continue  # 不绘制范围外的
            if plot_mode == "kl":
                if kl.close > kl.open:
                    ax.add_patch(
                        Rectangle((i - width / 2, kl.open), width, kl.close - kl.open, fill=False, color=up_color))
                    ax.plot([i, i], [kl.low, kl.open], up_color)
                    ax.plot([i, i], [kl.close, kl.high], up_color)
                else:  # 画阴线
                    ax.add_patch(Rectangle((i - width / 2, kl.open), width, kl.close - kl.open, color=down_color))
                    ax.plot([i, i], [kl.low, kl.high], color=down_color)
            elif plot_mode in "close":
                _y.append(kl.close)
                _x.append(i)
            elif plot_mode == "high":
                _y.append(kl.high)
                _x.append(i)
            elif plot_mode == "low":
                _y.append(kl.low)
                _x.append(i)
            elif plot_mode == "open":
                _y.append(kl.low)
                _x.append(i)
            else:
                raise CChanException(f"unknow plot mode={plot_mode}, must be one of kl/close/open/high/low", ErrCode.PLOT_ERR)
        if _x:
            ax.plot(_x, _y)

    def draw_klc(self, meta: CChanPlotMeta, ax: Axes, width=0.4, plot_single_kl=True):
        color_type = {FX_TYPE.TOP: 'red', FX_TYPE.BOTTOM: 'blue', KLINE_DIR.UP: 'green', KLINE_DIR.DOWN: 'green'}
        x_begin = ax.get_xlim()[0]

        for klc_meta in meta.klc_list:
            if klc_meta.klu_list[-1].idx+width < x_begin:
                continue  # 不绘制范围外的
            if klc_meta.end_idx == klc_meta.begin_idx and not plot_single_kl:
                continue
            ax.add_patch(
                Rectangle(
                    (klc_meta.begin_idx - width, klc_meta.low),
                    klc_meta.end_idx - klc_meta.begin_idx + width*2,
                    klc_meta.high - klc_meta.low,
                    fill=False,
                    color=color_type[klc_meta.type]))


    # 画笔
    def draw_bi(
        self,
        meta: CChanPlotMeta,
        ax: Axes,
        lv,
        color='black',
        show_num=False,
        # show_num=True,
        
        num_color="red",
        sub_lv_cnt=None,
        facecolor='green',
        alpha=0.1,
        disp_end=False,
        # disp_end=True,
        end_color='black',
        end_fontsize=10,
    ):
        cprint("画笔>>>draw_bi")
        x_begin = ax.get_xlim()[0]
        for bi_idx, bi in enumerate(meta.bi_list):
            if bi.end_x < x_begin:
                continue
            plot_bi_element(bi, ax, color)
            if show_num and bi.begin_x >= x_begin:
                ax.text((bi.begin_x+bi.end_x)/2, (bi.begin_y+bi.end_y)/2, f'{bi.idx}', fontsize=15, color=num_color)

            if disp_end:
                bi_text(bi_idx, ax, bi, end_fontsize, end_color)
        if sub_lv_cnt is not None and len(self.lv_lst) > 1 and lv != self.lv_lst[-1]:
            if sub_lv_cnt >= len(meta.bi_list):
                return
            else:
                begin_idx = meta.bi_list[-sub_lv_cnt].begin_x
            y_begin, y_end = ax.get_ylim()
            x_end = int(ax.get_xlim()[1])
            ax.fill_between(range(begin_idx, x_end + 1), y_begin, y_end, facecolor=facecolor, alpha=alpha)

    def draw_seg(
        self,
        meta: CChanPlotMeta,
        ax: Axes,
        lv,
        width=5,
        color="g",
        sub_lv_cnt=None,
        facecolor='green',
        alpha=0.1,
        disp_end=False,
        end_color='g',
        end_fontsize=13,
    ):
        x_begin = ax.get_xlim()[0]

        for seg_idx, seg_meta in enumerate(meta.seg_list):
            if seg_meta.end_x < x_begin:
                continue
            if seg_meta.is_sure:
                ax.plot([seg_meta.begin_x, seg_meta.end_x], [seg_meta.begin_y, seg_meta.end_y], color=color, linewidth=width)
            else:
                ax.plot([seg_meta.begin_x, seg_meta.end_x], [seg_meta.begin_y, seg_meta.end_y], color=color, linewidth=width, linestyle='dashed')
            if disp_end:
                bi_text(seg_idx, ax, seg_meta, end_fontsize, end_color)
        if sub_lv_cnt is not None and len(self.lv_lst) > 1 and lv != self.lv_lst[-1]:
            if sub_lv_cnt >= len(meta.seg_list):
                return
            else:
                begin_idx = meta.seg_list[-sub_lv_cnt].begin_x
            y_begin, y_end = ax.get_ylim()
            x_end = int(ax.get_xlim()[1])
            ax.fill_between(range(begin_idx, x_end+1), y_begin, y_end, facecolor=facecolor, alpha=alpha)

    def draw_segseg(
        self,
        meta: CChanPlotMeta,
        ax: Axes,
        width=7,
        color="brown",
        disp_end=False,
        end_color='brown',
        end_fontsize=15,
    ):
        x_begin = ax.get_xlim()[0]

        for seg_idx, seg_meta in enumerate(meta.segseg_list):
            if seg_meta.end_x < x_begin:
                continue
            if seg_meta.is_sure:
                ax.plot([seg_meta.begin_x, seg_meta.end_x], [seg_meta.begin_y, seg_meta.end_y], color=color, linewidth=width)
            else:
                ax.plot([seg_meta.begin_x, seg_meta.end_x], [seg_meta.begin_y, seg_meta.end_y], color=color, linewidth=width, linestyle='dashed')
            if disp_end:
                if seg_idx == 0:
                    ax.text(
                        seg_meta.begin_x,
                        seg_meta.begin_y,
                        f'{seg_meta.begin_y:.2f}',
                        fontsize=end_fontsize,
                        color=end_color,
                        verticalalignment="top" if seg_meta.dir == BI_DIR.UP else "bottom",
                        horizontalalignment='center')
                ax.text(
                    seg_meta.end_x,
                    seg_meta.end_y,
                    f'{seg_meta.end_y:.2f}',
                    fontsize=end_fontsize,
                    color=end_color,
                    verticalalignment="top" if seg_meta.dir == BI_DIR.DOWN else "bottom",
                    horizontalalignment='center')

    def draw_eigen(self, meta: CChanPlotMeta, ax: Axes, color_top="r", color_bottom="b", aplha=0.5, only_peak=False):
        x_begin = ax.get_xlim()[0]

        for eigenfx_meta in meta.eigenfx_lst:
            color = color_top if eigenfx_meta.fx == FX_TYPE.TOP else color_bottom
            for idx, eigen_meta in enumerate(eigenfx_meta.ele):
                if eigen_meta.begin_x+eigen_meta.w < x_begin:
                    continue
                if only_peak and idx != 1:
                    continue
                ax.add_patch(Rectangle((eigen_meta.begin_x, eigen_meta.begin_y),
                             eigen_meta.w,
                             eigen_meta.h,
                             fill=True,
                             alpha=aplha,
                             color=color))

    def draw_zs(
        self,
        meta: CChanPlotMeta,
        ax: Axes,
        color='orange',
        linewidth=2,
        sub_linewidth=0.5,
        show_text=False,
        fontsize=14,
        text_color='orange',
        draw_one_bi_zs=False,
    ):
        linewidth = max(linewidth, 2)
        x_begin = ax.get_xlim()[0]
        for zs_meta in meta.zs_lst:
            if not draw_one_bi_zs and zs_meta.is_onebi_zs:
                continue
            if zs_meta.begin+zs_meta.w < x_begin:
                continue
            line_style = '-' if zs_meta.is_sure else '--'
            ax.add_patch(Rectangle((zs_meta.begin, zs_meta.low), zs_meta.w, zs_meta.h, fill=False, color=color, linewidth=linewidth, linestyle=line_style))
            for sub_zs_meta in zs_meta.sub_zs_lst:
                ax.add_patch(Rectangle((sub_zs_meta.begin, sub_zs_meta.low), sub_zs_meta.w, sub_zs_meta.h, fill=False, color=color, linewidth=sub_linewidth, linestyle=line_style))
            if show_text:
                add_zs_text(ax, zs_meta, fontsize, text_color)
                for sub_zs_meta in zs_meta.sub_zs_lst:
                    add_zs_text(ax, sub_zs_meta, fontsize, text_color)

    def draw_segzs(self, meta: CChanPlotMeta, ax: Axes, color='red', linewidth=10, sub_linewidth=4):
        linewidth = max(linewidth, 2)
        x_begin = ax.get_xlim()[0]
        for zs_meta in meta.segzs_lst:
            if zs_meta.begin+zs_meta.w < x_begin:
                continue
            line_style = '-' if zs_meta.is_sure else '--'
            ax.add_patch(Rectangle((zs_meta.begin, zs_meta.low), zs_meta.w, zs_meta.h, fill=False, color=color, linewidth=linewidth, linestyle=line_style))
            for sub_zs_meta in zs_meta.sub_zs_lst:
                ax.add_patch(Rectangle((sub_zs_meta.begin, sub_zs_meta.low), sub_zs_meta.w, sub_zs_meta.h, fill=False, color=color, linewidth=sub_linewidth, linestyle=line_style))

    # 画 MACD 
    def draw_macd(self, meta: CChanPlotMeta, ax: Axes, x_limits, width=0.4):
        macd_lst = [klu.macd for klu in meta.klu_iter()]
        assert macd_lst[0] is not None, "you can't draw macd until you delete macd_metric=False"

        x_begin = x_limits[0]
        x_idx = range(len(macd_lst))
        dif_line = [macd.DIF for macd in macd_lst]
        dea_line = [macd.DEA for macd in macd_lst]
        macd_bar = [macd.macd for macd in macd_lst]
        y_min = min([min(dif_line[x_begin:]), min(dea_line[x_begin:]), min(macd_bar[x_begin:])])
        y_max = max([max(dif_line[x_begin:]), max(dea_line[x_begin:]), max(macd_bar[x_begin:])])
        ax.plot(x_idx, dif_line, "#FFA500")
        ax.plot(x_idx, dea_line, "#0000ff")
        _bar = ax.bar(x_idx, macd_bar, color="r", width=width)
        for idx, macd in enumerate(macd_bar):
            if macd < 0:
                _bar[idx].set_color("#006400")
        ax.set_ylim(y_min, y_max)

    def draw_mean(self, meta: CChanPlotMeta, ax: Axes):
        mean_lst = [klu.trend[TREND_TYPE.MEAN] for klu in meta.klu_iter()]
        Ts = list(mean_lst[0].keys())
        cmap = plt.cm.get_cmap('hsv', max([10, len(Ts)]))  # type: ignore
        for cmap_idx, T in enumerate(Ts):
            mean_arr = [mean_dict[T] for mean_dict in mean_lst]
            ax.plot(range(len(mean_arr)), mean_arr, c=cmap(cmap_idx), label=f'{T} meanline')
        ax.legend()

    def draw_channel(self, meta: CChanPlotMeta, ax: Axes, T=None, top_color="r", bottom_color="b", linewidth=3, linestyle="solid"):
        max_lst = [klu.trend[TREND_TYPE.MAX] for klu in meta.klu_iter()]
        min_lst = [klu.trend[TREND_TYPE.MIN] for klu in meta.klu_iter()]
        config_T_lst = sorted(list(max_lst[0].keys()))
        if T is None:
            T = config_T_lst[-1]
        elif T not in max_lst[0]:
            raise CChanException(f"plot channel of T={T} is not setted in CChanConfig.trend_metrics = {config_T_lst}", ErrCode.PLOT_ERR)
        top_array = [_d[T] for _d in max_lst]
        bottom_array = [_d[T] for _d in min_lst]
        ax.plot(range(len(top_array)), top_array, c=top_color, linewidth=linewidth, linestyle=linestyle, label=f'{T}-TOP-channel')
        ax.plot(range(len(bottom_array)), bottom_array, c=bottom_color, linewidth=linewidth, linestyle=linestyle, label=f'{T}-BUTTOM-channel')
        ax.legend()

    def draw_boll(self, meta: CChanPlotMeta, ax: Axes, mid_color="black", up_color="blue", down_color="purple"):
        x_begin = int(ax.get_xlim()[0])
        try:
            ma = [klu.boll.MID for klu in meta.klu_iter()][x_begin:]
            up = [klu.boll.UP for klu in meta.klu_iter()][x_begin:]
            down = [klu.boll.DOWN for klu in meta.klu_iter()][x_begin:]
        except AttributeError as e:
            raise CChanException("you can't draw boll until you set boll_n in CChanConfig", ErrCode.PLOT_ERR) from e

        ax.plot(range(x_begin, x_begin+len(ma)), ma, c=mid_color)
        ax.plot(range(x_begin, x_begin+len(up)), up, c=up_color)
        ax.plot(range(x_begin, x_begin+len(down)), down, c=down_color)
        self.y_min = min([self.y_min, min(down)])
        self.y_max = max([self.y_max, max(up)])

    def bsp_common_draw(self, bsp_list, ax: Axes, buy_color, sell_color, fontsize, arrow_l, arrow_h, arrow_w):
        x_begin = ax.get_xlim()[0]
        y_range = self.y_max-self.y_min
        for bsp in bsp_list:
            if bsp.x < x_begin:
                continue
            color = buy_color if bsp.is_buy else sell_color
            verticalalignment = 'top' if bsp.is_buy else 'bottom'

            arrow_dir = 1 if bsp.is_buy else -1
            arrow_len = arrow_l*y_range
            arrow_head = arrow_len*arrow_h
            ax.text(bsp.x,
                    bsp.y-arrow_len*arrow_dir,
                    f'{bsp.desc()}',
                    fontsize=fontsize,
                    color=color,
                    verticalalignment=verticalalignment,
                    horizontalalignment='center')
            ax.arrow(bsp.x,
                     bsp.y-arrow_len*arrow_dir,
                     0,
                     (arrow_len-arrow_head)*arrow_dir,
                     head_width=arrow_w,
                     head_length=arrow_head,
                     color=color)
            if bsp.y-arrow_len*arrow_dir < self.y_min:
                self.y_min = bsp.y-arrow_len*arrow_dir
            if bsp.y-arrow_len*arrow_dir > self.y_max:
                self.y_max = bsp.y-arrow_len*arrow_dir

    def draw_bs_point(self, meta: CChanPlotMeta, ax: Axes, buy_color='r', sell_color='g', fontsize=15, arrow_l=0.15, arrow_h=0.2, arrow_w=1):
        self.bsp_common_draw(
            bsp_list=meta.bs_point_lst,
            ax=ax,
            buy_color=buy_color,
            sell_color=sell_color,
            fontsize=fontsize,
            arrow_l=arrow_l,
            arrow_h=arrow_h,
            arrow_w=arrow_w,
        )

    def draw_seg_bs_point(self, meta: CChanPlotMeta, ax: Axes, buy_color='r', sell_color='g', fontsize=18, arrow_l=0.2, arrow_h=0.25, arrow_w=1.2):
        self.bsp_common_draw(
            bsp_list=meta.seg_bsp_lst,
            ax=ax,
            buy_color=buy_color,
            sell_color=sell_color,
            fontsize=fontsize,
            arrow_l=arrow_l,
            arrow_h=arrow_h,
            arrow_w=arrow_w,
            )

    def update_y_range(self, text_box, text_y):
        text_height = text_box.y1 - text_box.y0
        self.y_min = min([self.y_min, text_y-text_height])
        self.y_max = max([self.y_max, text_y+text_height])

    def plot_closeAction(self, plot_cover, cbsp, ax: Axes, text_y, arrow_len, arrow_dir, color):
        if not plot_cover:
            return
        for closeAction in cbsp.close_action:
            ax.arrow(
                cbsp.x,
                text_y,
                closeAction.x-cbsp.x,
                arrow_len*arrow_dir + (closeAction.y-cbsp.y),
                color=color,
            )


def plot_bi_element(bi: CBi_meta, ax: Axes, color: str):
    if bi.id_sure:
        ax.plot([bi.begin_x, bi.end_x], [bi.begin_y, bi.end_y], color=color)
    else:
        ax.plot([bi.begin_x, bi.end_x], [bi.begin_y, bi.end_y], linestyle='dashed', color=color)


def bi_text(bi_idx, ax: Axes, bi, end_fontsize, end_color):
    if bi_idx == 0:
        ax.text(
            bi.begin_x,
            bi.begin_y,
            f'{bi.begin_y:.2f}',
            fontsize=end_fontsize,
            color=end_color,
            verticalalignment="top" if bi.dir == BI_DIR.UP else "bottom",
            horizontalalignment='center')
    ax.text(
        bi.end_x,
        bi.end_y,
        f'{bi.end_y:.2f}',
        fontsize=end_fontsize,
        color=end_color,
        verticalalignment="top" if bi.dir == BI_DIR.DOWN else "bottom",
        horizontalalignment='center')


def show_func_helper(func):
    print(f"{func.__name__}:")
    insp = inspect.signature(func)
    for name, para in insp.parameters.items():
        if para.default == inspect.Parameter.empty:
            continue
            # print(f"\t{name}*")
        elif type(para.default) == str:
            print(f"\t{name}: '{para.default}'")
        else:
            print(f"\t{name}: {para.default}")


def add_zs_text(ax: Axes, zs_meta: CZS_meta, fontsize, text_color):
    ax.text(
        zs_meta.begin,
        zs_meta.low,
        f'{zs_meta.low:.2f}',
        fontsize=fontsize,
        color=text_color,
        verticalalignment="top",
        horizontalalignment='center',
    )
    ax.text(
        zs_meta.begin+zs_meta.w,
        zs_meta.low+zs_meta.h,
        f'{zs_meta.low+zs_meta.h:.2f}',
        fontsize=fontsize,
        color=text_color,
        verticalalignment="bottom",
        horizontalalignment='center',
    )
    

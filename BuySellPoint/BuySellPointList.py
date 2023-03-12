from typing import Generic, List, Optional, TypeVar, Union, overload
from Tools.DebugTool import cprint
from Bi.Bi import Bi
from Bi.BiList import BiList
from Common.CEnum import BSP_TYPE
from Common.func_util import has_overlap
from Seg.Seg import Seg
from Seg.SegListComm import CSegListComm
from ZS.ZS import ZS

from .BS_Point import BuySel_Point
from .BSPointConfig import CBSPointConfig, CPointConfig

LINE_TYPE = TypeVar('LINE_TYPE', Bi, Seg[Bi])
LINE_LIST_TYPE = TypeVar('LINE_LIST_TYPE', BiList, CSegListComm[Bi])


class BuySellPointList(Generic[LINE_TYPE, LINE_LIST_TYPE]):
    def __init__(self, bs_point_config: CBSPointConfig):
        self.lst: List[BuySel_Point[LINE_TYPE]] = []
        self.bsp1_lst: List[BuySel_Point[LINE_TYPE]] = []
        self.config = bs_point_config
        self.last_sure_pos = -1  # 上一次计算时sure seg【起始】klu的位置，用起始原因是因为这一次计算可能最后一个线段是刚刚生成的

    def __iter__(self):
        yield from self.lst

    def __len__(self):
        return len(self.lst)

    @overload
    def __getitem__(self, index: int) -> BuySel_Point: ...

    @overload
    def __getitem__(self, index: slice) -> List[BuySel_Point]: ...

    def __getitem__(self, index: Union[slice, int]) -> Union[List[BuySel_Point], BuySel_Point]:
        return self.lst[index]

    def cal(self, bi_list: LINE_LIST_TYPE, seg_list: CSegListComm[LINE_TYPE]):
        self.lst = [bsp for bsp in self.lst if bsp.klu.idx <= self.last_sure_pos]
        self.bsp1_lst = [bsp for bsp in self.bsp1_lst if bsp.klu.idx <= self.last_sure_pos]

        self.cal_seg_bs1point(seg_list, bi_list)
        self.cal_seg_bs2point(seg_list, bi_list)
        self.cal_seg_bs3point(seg_list, bi_list)

        self.update_last_pos(seg_list)

    def update_last_pos(self, seg_list: CSegListComm):
        self.last_sure_pos = -1
        for seg in seg_list[::-1]:
            if seg.is_sure:
                self.last_sure_pos = seg.end_bi.get_begin_klu().idx
                return

    def seg_need_cal(self, seg: Seg):
        return seg.end_bi.get_end_klu().idx > self.last_sure_pos

    def add_bs(
        self,
        bs_type: BSP_TYPE,
        bi: LINE_TYPE,
        relate_bsp1: Optional[BuySel_Point],
        is_target_bsp: bool = True,
    ):
        is_buy = bi.is_down()
        for exist_bsp in self.lst:
            if exist_bsp.klu.idx == bi.get_end_klu().idx:
                assert exist_bsp.is_buy == is_buy
                exist_bsp.add_another_bsp_prop(bs_type, relate_bsp1)
                return
        if bs_type not in self.config.GetBSConfig(is_buy).target_types:
            is_target_bsp = False

        if is_target_bsp or bs_type in [BSP_TYPE.T1, BSP_TYPE.T1P]:
            bsp = BuySel_Point[LINE_TYPE](
                bi=bi,
                is_buy=is_buy,
                bs_type=bs_type,
                relate_bsp1=relate_bsp1,
            )
        else:
            return
        # cprint("BSPointList.py 85:添加买卖点函数-->")
        # cprint("BSPointList.py 86:Will append")
        # BuySellPoint.BS_Point.BuySel_Point
        # cprint(bsp)
        if is_target_bsp:
            self.lst.append(bsp)
        if bs_type in [BSP_TYPE.T1, BSP_TYPE.T1P]:
            self.bsp1_lst.append(bsp)

    def cal_seg_bs1point(self, seg_list: CSegListComm[LINE_TYPE], bi_list: LINE_LIST_TYPE):
        for seg in seg_list:
            if not self.seg_need_cal(seg):
                continue
            self.cal_single_bs1point(seg, bi_list)

    def cal_single_bs1point(self, seg: Seg[LINE_TYPE], bi_list: LINE_LIST_TYPE):
        BSP_CONF = self.config.GetBSConfig(seg.is_down())
        zs_cnt = seg.get_multi_bi_zs_cnt() if BSP_CONF.bsp1_only_multibi_zs else len(seg.zs_lst)
        is_target_bsp = (BSP_CONF.min_zs_cnt <= 0 or zs_cnt >= BSP_CONF.min_zs_cnt)
        if len(seg.zs_lst) > 0 and not seg.zs_lst[-1].is_one_bi_zs() and seg.zs_lst[-1].bi_out and seg.zs_lst[-1].bi_out.idx == seg.end_bi.idx:
            self.treat_bsp1(seg, BSP_CONF, is_target_bsp)  # 中枢一类买卖点
        else:
            self.treat_pz_bsp1(seg, BSP_CONF, bi_list, is_target_bsp)  # 盘整一类买卖点

    def treat_bsp1(self, seg: Seg[LINE_TYPE], BSP_CONF: CPointConfig, is_target_bsp: bool):
        last_zs = seg.zs_lst[-1]
        assert last_zs.bi_out is not None
        break_peak, _ = last_zs.out_bi_is_peak()  # break_peak=False应该只有线段第一笔直接拉得很低的时候才会有这个情况
        if BSP_CONF.bs1_peak and not break_peak:
            is_target_bsp = False
        is_diver, _ = last_zs.is_divergence(BSP_CONF)
        if not is_diver:
            is_target_bsp = False
        self.add_bs(bs_type=BSP_TYPE.T1, bi=last_zs.bi_out, relate_bsp1=None, is_target_bsp=is_target_bsp)

    def treat_pz_bsp1(self, seg: Seg[LINE_TYPE], BSP_CONF: CPointConfig, bi_list: LINE_LIST_TYPE, is_target_bsp):
        last_bi = seg.end_bi
        pre_bi = bi_list[last_bi.idx-2]
        if last_bi.seg_idx != pre_bi.seg_idx:
            return
        if last_bi.dir != seg.dir:  # 尾部的虚段可能会有不一样的笔
            return
        if last_bi.is_down() and last_bi._low() > pre_bi._low():  # 创新低
            return
        if last_bi.is_up() and last_bi._high() < pre_bi._high():  # 创新高
            return
        in_metric = pre_bi.cal_macd_metric(BSP_CONF.macd_algo, is_reverse=False)
        out_metric = last_bi.cal_macd_metric(BSP_CONF.macd_algo, is_reverse=True)
        is_diver, _ = out_metric <= BSP_CONF.divergence_rate*in_metric, out_metric/(in_metric+1e-7)
        if not is_diver:
            is_target_bsp = False
        if isinstance(bi_list, BiList):
            assert isinstance(last_bi, Bi) and isinstance(pre_bi, Bi)
        self.add_bs(bs_type=BSP_TYPE.T1P, bi=last_bi, relate_bsp1=None, is_target_bsp=is_target_bsp)

    def cal_seg_bs2point(self, seg_list: CSegListComm[LINE_TYPE], bi_list: LINE_LIST_TYPE):
        bsp1_bi_idx_dict = {bsp.bi.idx: bsp for bsp in self.bsp1_lst}
        for seg in seg_list:
            self.treat_bsp2(seg, bsp1_bi_idx_dict, seg_list, bi_list)

    def treat_bsp2(self, seg: Seg, bsp1_bi_idx_dict, seg_list: CSegListComm[LINE_TYPE], bi_list: LINE_LIST_TYPE):
        if not self.seg_need_cal(seg):
            return
        if len(seg_list) > 1:
            BSP_CONF = self.config.GetBSConfig(seg.is_down())
            bsp1_bi = seg.end_bi
            bsp1_bi_idx = bsp1_bi.idx
            real_bsp1 = bsp1_bi_idx_dict.get(bsp1_bi.idx)
            if bsp1_bi.idx + 2 >= len(bi_list):
                return
            break_bi = bi_list[bsp1_bi.idx + 1]
            bsp2_bi = bi_list[bsp1_bi.idx + 2]
        else:
            BSP_CONF = self.config.GetBSConfig(seg.is_up())
            bsp1_bi, real_bsp1 = None, None
            bsp1_bi_idx = -1
            if len(bi_list) == 1:
                return
            bsp2_bi = bi_list[1]
            break_bi = bi_list[0]
        if BSP_CONF.bsp2_follow_1 and bsp1_bi_idx not in bsp1_bi_idx_dict:  # check bsp2_follow_1
            # 不满足时，2，2s都不计算
            return
        retrace_rate = bsp2_bi.amp()/break_bi.amp()
        bsp2_flag = retrace_rate <= BSP_CONF.max_bs2_rate
        if bsp2_flag:
            self.add_bs(bs_type=BSP_TYPE.T2, bi=bsp2_bi, relate_bsp1=real_bsp1)  # type: ignore
        elif BSP_CONF.bsp2s_follow_2:
            return
        self.treat_bsp2s(seg_list, bi_list, bsp2_bi, break_bi, real_bsp1, BSP_CONF)  # type: ignore

    def treat_bsp2s(
        self,
        seg_list: CSegListComm,
        bi_list: LINE_LIST_TYPE,
        bsp2_bi: LINE_TYPE,
        break_bi: LINE_TYPE,
        real_bsp1: Optional[BuySel_Point],
        BSP_CONF: CPointConfig,
    ):
        bias = 2
        _low, _high = None, None
        while bsp2_bi.idx + bias < len(bi_list):  # 计算类二
            bsp2s_bi = bi_list[bsp2_bi.idx + bias]
            assert bsp2s_bi.seg_idx is not None and bsp2_bi.seg_idx is not None
            if BSP_CONF.max_bsp2s_lv is not None and bias/2 > BSP_CONF.max_bsp2s_lv:
                break
            if bsp2s_bi.seg_idx != bsp2_bi.seg_idx and (bsp2s_bi.seg_idx < len(seg_list)-1 or seg_list[bsp2_bi.seg_idx].is_sure):
                break  # 跨线段且（不是最后两段 或 2类段已坐实）
            if bias == 2:
                if not has_overlap(bsp2_bi._low(), bsp2_bi._high(), bsp2s_bi._low(), bsp2s_bi._high()):
                    break
                _low = max([bsp2_bi._low(), bsp2s_bi._low()])
                _high = min([bsp2_bi._high(), bsp2s_bi._high()])
            elif not has_overlap(_low, _high, bsp2s_bi._low(), bsp2s_bi._high()):
                break

            if bsp2s_break_bsp1(bsp2s_bi, break_bi):
                break
            retrace_rate = abs(bsp2s_bi.get_end_val()-break_bi.get_end_val())/break_bi.amp()
            if retrace_rate > BSP_CONF.max_bs2_rate:
                break

            self.add_bs(bs_type=BSP_TYPE.T2S, bi=bsp2s_bi, relate_bsp1=real_bsp1)  # type: ignore
            bias += 2

    def cal_seg_bs3point(self, seg_list: CSegListComm[LINE_TYPE], bi_list: LINE_LIST_TYPE):
        bsp1_bi_idx_dict = {bsp.bi.idx: bsp for bsp in self.bsp1_lst}
        for seg in seg_list:
            if not self.seg_need_cal(seg):
                continue
            if len(seg_list) > 1:
                bsp1_bi = seg.end_bi
                bsp1_bi_idx = bsp1_bi.idx
                BSP_CONF = self.config.GetBSConfig(seg.is_down())
                real_bsp1 = bsp1_bi_idx_dict.get(bsp1_bi.idx)
                next_seg_idx = seg.idx+1
                next_seg = seg.next  # 可能为None, 所以并不一定可以保证next_seg_idx == next_seg.idx
            else:
                next_seg = seg
                next_seg_idx = seg.idx
                bsp1_bi, real_bsp1 = None, None
                bsp1_bi_idx = -1
                BSP_CONF = self.config.GetBSConfig(seg.is_up())
            if BSP_CONF.bsp3_follow_1 and bsp1_bi_idx not in bsp1_bi_idx_dict:
                continue
            if next_seg:
                self.treat_bsp3_after(seg_list, next_seg, BSP_CONF, bi_list, real_bsp1, bsp1_bi_idx, next_seg_idx)
            # len(seg_list)==1 -> next_seg==next_seg，后面可能只有两笔，未形成线段，但也有可能有3类bsp
            self.treat_bsp3_before(seg_list, seg, next_seg, bsp1_bi, BSP_CONF, bi_list, real_bsp1, next_seg_idx)

    def treat_bsp3_after(
        self,
        seg_list: CSegListComm[LINE_TYPE],
        next_seg: Seg[LINE_TYPE],
        BSP_CONF: CPointConfig,
        bi_list: LINE_LIST_TYPE,
        real_bsp1,
        bsp1_bi_idx,
        next_seg_idx
    ):
        first_zs = next_seg.get_first_multi_bi_zs()
        if first_zs is None:
            return
        if BSP_CONF.strict_bsp3 and first_zs.get_bi_in().idx != bsp1_bi_idx+1:  # 严格模式下，必须直接接在1类后面
            return
        if first_zs.bi_out is None or first_zs.bi_out.idx+1 >= len(bi_list):
            return
        bsp3_bi = bi_list[first_zs.bi_out.idx+1]
        if bsp3_bi.seg_idx != next_seg_idx and next_seg_idx < len(seg_list)-2:
            return
        if bsp3_back2zs(bsp3_bi, first_zs):
            return
        bsp3_peak_zs = bsp3_break_zspeak(bsp3_bi, first_zs)
        if BSP_CONF.bsp3_peak and not bsp3_peak_zs:  # 突破笔不是中枢里面最突破的
            return
        self.add_bs(bs_type=BSP_TYPE.T3A, bi=bsp3_bi, relate_bsp1=real_bsp1)  # type: ignore

    def treat_bsp3_before(
        self,
        seg_list: CSegListComm[LINE_TYPE],
        seg: Seg[LINE_TYPE],
        next_seg: Optional[Seg[LINE_TYPE]],
        bsp1_bi: Optional[LINE_TYPE],
        BSP_CONF: CPointConfig,
        bi_list: LINE_LIST_TYPE,
        real_bsp1,
        next_seg_idx
    ):
        cmp_zs = seg.get_final_multi_bi_zs()
        if cmp_zs is None:
            return
        if not bsp1_bi:
            return
        assert cmp_zs.bi_out is not None
        if BSP_CONF.strict_bsp3 and cmp_zs.bi_out.idx != bsp1_bi.idx:  # 严格模式下，后面必须接1类
            return
        end_bi_idx = cal_bsp3_bi_end_idx(next_seg)
        for bsp3_bi in bi_list[bsp1_bi.idx+2::2]:
            if bsp3_bi.idx > end_bi_idx:
                break
            assert bsp3_bi.seg_idx is not None
            if bsp3_bi.seg_idx != next_seg_idx and bsp3_bi.seg_idx < len(seg_list)-1:
                break
            if bsp3_back2zs(bsp3_bi, cmp_zs):  # type: ignore
                continue
            self.add_bs(bs_type=BSP_TYPE.T3B, bi=bsp3_bi, relate_bsp1=real_bsp1)  # type: ignore
            break

    def getLastestBspList(self) -> List[BuySel_Point[LINE_TYPE]]:
        if len(self.lst) == 0:
            return []
        return sorted(self.lst, key=lambda bsp: bsp.bi.idx, reverse=True)


def bsp2s_break_bsp1(bsp2s_bi: LINE_TYPE, bsp2_break_bi: LINE_TYPE) -> bool:
    return (bsp2s_bi.is_down() and bsp2s_bi._low() < bsp2_break_bi._low()) or \
           (bsp2s_bi.is_up() and bsp2s_bi._high() > bsp2_break_bi._high())


def bsp3_back2zs(bsp3_bi: LINE_TYPE, zs: ZS) -> bool:
    return (bsp3_bi.is_down() and bsp3_bi._low() < zs.high) or (bsp3_bi.is_up() and bsp3_bi._high() > zs.low)


def bsp3_break_zspeak(bsp3_bi: LINE_TYPE, zs: ZS) -> bool:
    return (bsp3_bi.is_down() and bsp3_bi._high() >= zs.peak_high) or (bsp3_bi.is_up() and bsp3_bi._low() <= zs.peak_low)


def cal_bsp3_bi_end_idx(seg: Optional[Seg[LINE_TYPE]]):
    # 对于中枢在一类bsp前面的三类bsp，遍历的结束位置应该是一类bsp之后第一个中枢的in_idx
    if not seg:
        return float("inf")
    if seg.get_multi_bi_zs_cnt() == 0 and seg.next is None:
        # 比如最后一虚段只有一笔，后面还跟着一个parent_seg为None的笔
        return float("inf")
    end_bi_idx = seg.end_bi.idx-1
    for zs in seg.zs_lst:
        if zs.is_one_bi_zs():
            continue
        assert zs.bi_out is not None
        end_bi_idx = zs.bi_out.idx
        break
    return end_bi_idx

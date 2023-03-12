from typing import List, Optional, Union, overload
from colorama import Fore, Back, Style

from Common.CEnum import FX_TYPE, KLINE_DIR
from KLine.KLine import KLineCombined
from Tools.DebugTool import cprint
from .Bi import Bi
from .BiConfig import BiConfig


class BiList:
    def __init__(self, bi_conf=BiConfig()):
        self.bi_list: List[Bi] = []
        self.last_end = None  # 最后一笔的尾部
        self.config = bi_conf
        self.free_klc_lst = []  # 仅仅用作第一笔未画出来之前的缓存，为了获得更精准的结果而已，不加这块逻辑其实对后续计算没太大影响

    def __str__(self):
        return "\n".join([str(bi) for bi in self.bi_list])

    def __iter__(self):
        yield from self.bi_list

    @overload
    def __getitem__(self, index: int) -> Bi: ...

    @overload
    def __getitem__(self, index: slice) -> List[Bi]: ...

    def __getitem__(self, index: Union[slice, int]) -> Union[List[Bi], Bi]:
        return self.bi_list[index]

    def __len__(self):
        return len(self.bi_list)

    def try_create_first_bi(self, klc: KLineCombined) -> bool:
        for exist_free_klc in self.free_klc_lst:
            if exist_free_klc.fx == klc.fx:
                continue
            if self.can_make_bi(klc, exist_free_klc):
                self.add_new_bi(exist_free_klc, klc)
                self.last_end = klc
                return True
        self.free_klc_lst.append(klc)
        self.last_end = klc
        return False

    def update_bi(self, klc: KLineCombined, last_klc: KLineCombined, cal_virtual: bool) -> bool:
        # klc: 倒数第二根klc
        # last_klc: 倒数第1根klc
        flag1 = self.update_bi_sure(klc)
        if cal_virtual:
            flag2 = self.try_add_virtual_bi(last_klc)
            return flag1 or flag2
        else:
            return flag1

    def update_bi_sure(self, klc: KLineCombined) -> bool:
        # klc: 倒数第二根klc
        _tmp_end = self.get_last_klu_of_last_bi()
        self.delete_virtual_bi()
        # 返回值：是否出现新笔
        if klc.fx == FX_TYPE.UNKNOWN:
            return _tmp_end != self.get_last_klu_of_last_bi()  # 虚笔是否有变
        if self.last_end is None or len(self.bi_list) == 0:
            return self.try_create_first_bi(klc)
        if klc.fx == self.last_end.fx:
            return self.try_update_end(klc)
        elif self.can_make_bi(klc, self.last_end):
            self.add_new_bi(self.last_end, klc)
            self.last_end = klc
            return True
        return _tmp_end != self.get_last_klu_of_last_bi()  # 可能新增加的K线使得原本的虚笔消失，比如 US.BELFA@2017-02-15 v.s. US.BELFA@2017-02-17

    def delete_virtual_bi(self):
        if len(self) > 0 and not self.bi_list[-1].is_sure:
            if self.bi_list[-1].is_virtual_end():
                self.bi_list[-1].restore_from_virtual_end()
            else:
                del self.bi_list[-1]

    def try_add_virtual_bi(self, klc: KLineCombined, need_del_end=False):
        if need_del_end:
            self.delete_virtual_bi()
        if len(self) == 0:
            return False
        if klc.idx == self[-1].end_klc.idx:
            return False
        if (self[-1].is_up() and klc.high >= self[-1].end_klc.high) or (self[-1].is_down() and klc.low <= self[-1].end_klc.low):
            # 更新最后一笔
            self.bi_list[-1].update_virtual_end(klc)
            return True
        _tmp_klc = klc
        while _tmp_klc and _tmp_klc.idx > self[-1].end_klc.idx:
            assert _tmp_klc is not None
            if not self.satisfy_bi_span(_tmp_klc, self[-1].end_klc):
                return False
            if ((self[-1].is_down() and _tmp_klc.dir == KLINE_DIR.UP and _tmp_klc.low > self[-1].end_klc.low) or (self[-1].is_up() and _tmp_klc.dir == KLINE_DIR.DOWN and _tmp_klc.high < self[-1].end_klc.high)) and self[-1].end_klc.check_fx_valid(_tmp_klc, self.config.bi_fx_check, for_virtual=True):
                # 新增一笔
                self.add_new_bi(self.last_end, _tmp_klc, is_sure=False)
                return True
            _tmp_klc = _tmp_klc.pre
        return False

    def add_new_bi(self, pre_klc, cur_klc, is_sure=True):
        
        # cprint(  "添加新笔 add_new_bi",pcolor= Fore.RED)    
        
        
        self.bi_list.append(Bi(pre_klc, cur_klc, idx=len(self.bi_list), is_sure=is_sure))
        if len(self.bi_list) >= 2:
            self.bi_list[-2].next = self.bi_list[-1]
            self.bi_list[-1].pre = self.bi_list[-2]

    def satisfy_bi_span(self, klc: KLineCombined, last_end: KLineCombined):
        bi_span = self.get_klc_span(klc, last_end)
        if self.config.is_strict:
            return bi_span >= 4
        uint_kl_cnt = 0
        tmp_klc = last_end.next
        while tmp_klc:
            uint_kl_cnt += len(tmp_klc.lst)
            if not tmp_klc.next:  # 最后尾部虚笔的时候，可能klc.idx == last_end.idx+1
                return False
            if tmp_klc.next.idx < klc.idx:
                tmp_klc = tmp_klc.next
            else:
                break
        return bi_span >= 3 and uint_kl_cnt >= 3

    def get_klc_span(self, klc: KLineCombined, last_end: KLineCombined) -> int:
        span = klc.idx - last_end.idx
        if not self.config.gap_as_kl:
            return span
        if span >= 4:  # 加速运算，如果span需要真正精确的值，需要去掉这一行
            return span
        tmp_klc = last_end
        while tmp_klc and tmp_klc.idx < klc.idx:
            if tmp_klc.has_gap_with_next():
                span += 1
            tmp_klc = tmp_klc.next
        return span

    def can_make_bi(self, klc: KLineCombined, last_end: KLineCombined):
        if self.config.bi_algo == "fx":
            return True
        satisify_span = self.satisfy_bi_span(klc, last_end) if last_end.check_fx_valid(klc, self.config.bi_fx_check) else False
        if satisify_span and self.config.bi_end_is_peak:
            return end_is_peak(last_end, klc)
        else:
            return satisify_span

    def try_update_end(self, klc: KLineCombined) -> bool:
        if len(self.bi_list) == 0:
            return False
        last_bi = self.bi_list[-1]
        if (last_bi.is_up() and klc.fx == FX_TYPE.TOP and klc.high >= last_bi.get_end_val()) or \
           (last_bi.is_down() and klc.fx == FX_TYPE.BOTTOM and klc.low <= last_bi.get_end_val()):
            last_bi.update_new_end(klc)
            self.last_end = klc
            return True
        else:
            return False

    def get_last_klu_of_last_bi(self) -> Optional[int]:
        return self.bi_list[-1].get_end_klu().idx if len(self) > 0 else None


def end_is_peak(last_end: KLineCombined, cur_end: KLineCombined) -> bool:
    if last_end.fx == FX_TYPE.BOTTOM:
        cmp_thred = cur_end.high  # 或者严格点选择get_klu_max_high()
        klc = last_end.get_next()
        while True:
            if klc.idx >= cur_end.idx:
                return True
            if klc.high > cmp_thred:
                return False
            klc = klc.get_next()
    elif last_end.fx == FX_TYPE.TOP:
        cmp_thred = cur_end.low  # 或者严格点选择get_klu_min_low()
        klc = last_end.get_next()
        while True:
            if klc.idx >= cur_end.idx:
                return True
            if klc.low < cmp_thred:
                return False
            klc = klc.get_next()
    return True

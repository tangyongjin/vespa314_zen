from typing import List
import time
from Bi.Bi import CBi
from BuySellPoint.BS_Point import CBS_Point
from Common.CEnum import FX_TYPE ,BI_DIR
from KLine.KLine import CKLine
from KLine.KLine_List import CKLine_List
from Seg.Eigen import CEigen
from Seg.EigenFX import CEigenFX
from Seg.Seg import CSeg
from ZS.ZS import CZS
from Tools.DebugTool import cprint
from colorama import Fore, Back, Style


class Cklc_meta:
    def __init__(self, klc: CKLine):
        self.high = klc.high
        self.low = klc.low
        self.begin_idx = klc.lst[0].idx
        self.end_idx = klc.lst[-1].idx
        self.type = klc.fx if klc.fx != FX_TYPE.UNKNOWN else klc.dir

        self.klu_list = list(klc.lst)


class CBi_meta:
    def __init__(self, bi: CBi):
        self.idx = bi.idx
        self.dir = bi.dir
        self.type = bi.type
        self.begin_x = bi.get_begin_klu().idx
        self.end_x = bi.get_end_klu().idx
        self.begin_y = bi.get_begin_val()
        self.end_y = bi.get_end_val()
        self.id_sure = bi.is_sure


class CSeg_meta:
    def __init__(self, seg: CSeg):
        if type(seg.start_bi) == CBi:
            self.begin_x = seg.start_bi.get_begin_klu().idx
            self.begin_y = seg.start_bi.get_begin_val()
            self.end_x = seg.end_bi.get_end_klu().idx
            self.end_y = seg.end_bi.get_end_val()
        else:
            assert type(seg.start_bi) == CSeg
            self.begin_x = seg.start_bi.start_bi.get_begin_klu().idx
            self.begin_y = seg.start_bi.start_bi.get_begin_val()
            self.end_x = seg.end_bi.end_bi.get_end_klu().idx
            self.end_y = seg.end_bi.end_bi.get_end_val()
        self.dir = seg.dir
        self.is_sure = seg.is_sure

        self.has_tl = False
        self.tl_y0 = None
        self.tl_y1 = None
        self.tl_x0 = None
        self.tl_x1 = None


class CEigen_meta:
    def __init__(self, eigen: CEigen):
        self.begin_x = eigen.lst[0].get_begin_klu().idx
        self.end_x = eigen.lst[-1].get_end_klu().idx
        self.begin_y = eigen.low
        self.end_y = eigen.high
        self.w = self.end_x - self.begin_x
        self.h = self.end_y - self.begin_y


class CEigenFX_meta:
    def __init__(self, eigenFX: CEigenFX):
        self.ele = [CEigen_meta(ele) for ele in eigenFX.ele if ele is not None]
        assert len(self.ele) == 3
        assert eigenFX.ele[1] is not None
        self.gap = eigenFX.ele[1].gap
        self.fx = eigenFX.ele[1].fx


class CZS_meta:
    def __init__(self, zs: CZS):
        self.low = zs.low
        self.high = zs.high
        self.begin = zs.begin.idx
        self.end = zs.end.idx
        self.w = self.end - self.begin
        self.h = self.high - self.low
        self.is_sure = zs.is_sure
        self.sub_zs_lst = [CZS_meta(t) for t in zs.sub_zs_lst]
        self.is_onebi_zs = zs.is_one_bi_zs()


class CBS_Point_meta:
    def __init__(self, bsp: CBS_Point, is_seg):
        self.is_buy = bsp.is_buy
        self.type = bsp.type2str()
        self.is_seg = is_seg

        self.x = bsp.klu.idx
        self.y = bsp.klu.low if self.is_buy else bsp.klu.high

    def desc(self):
        is_seg_flag = "※" if self.is_seg else ""
        return f'{is_seg_flag}b{self.type}' if self.is_buy else f'{is_seg_flag}s{self.type}'


class ZenPlotMeta:
    def __init__(self, kl_list: CKLine_List):
        self.data = kl_list

        self.klc_list: List[Cklc_meta] = [Cklc_meta(klc) for klc in kl_list.lst]
        self.datetick = [klu.time.to_str() for klu in self.klu_iter()]
        self.klu_len = sum(len(klc.klu_list) for klc in self.klc_list)

        self.bi_list = [CBi_meta(bi) for bi in kl_list.bi_list]
        
        
        
        self.bi_orginal_list =  []
        
        
        #  # print( len(self.bi_list) )
        # print(  type   (pre_klc) )
        # print  (pre_klc) 
        # print(  vars(pre_klc))
        
        # cprint( ">>>>>>>>>>>",pcolor= Fore.RED)
        # print( pre_klc.time_begin )
        
        # if pre_klc.fx == FX_TYPE.TOP:
        #     _kl_value=pre_klc.high
        # if pre_klc.fx == FX_TYPE.BOTTOM:
        #     _kl_value=pre_klc.low
        
        
        
        
        
        cprint("ZenPlotMeta 118",Fore.RED)
        for xxxbi in kl_list.bi_list:
            cprint("--------------> 122",Fore.RED)
            print(  xxxbi._CBi__begin_klc.time_end)
            print(  xxxbi._CBi__begin_klc.high)
            print(  xxxbi._CBi__begin_klc.low)
            
            print(  xxxbi._CBi__end_klc.time_end)
            print(  xxxbi._CBi__end_klc.high)
            print(  xxxbi._CBi__end_klc.low)
            print(  xxxbi._CBi__dir)
            print( vars(xxxbi) )
            print( xxxbi )
            
            point1={}
            point2={}
            # from Common.CEnum import FX_CHECK_METHOD, FX_TYPE, KLINE_DIR

            if xxxbi._CBi__dir ==BI_DIR.UP:
                cprint("--------------> UP",Fore.RED)
                point1={ "date":xxxbi._CBi__begin_klc.time_end, "value": xxxbi._CBi__begin_klc.low  }
                point2={ "date":xxxbi._CBi__end_klc.time_end, "value":xxxbi._CBi__end_klc.high }
            else:   
                cprint("--------------> DOWN",Fore.RED)
                point1={ "date":xxxbi._CBi__begin_klc.time_end, "value": xxxbi._CBi__begin_klc.high  }
                point2={ "date":xxxbi._CBi__end_klc.time_end, "value":xxxbi._CBi__end_klc.low }
                
                
            # bi_orginal_list    
            
            if not self.bi_orginal_list:
                self.bi_orginal_list.append(point1)
                self.bi_orginal_list.append(point2)
            else:
                print("List is not empty")
                if self.bi_orginal_list[-1]==point1:
                    self.bi_orginal_list.append(point2)
                else:
                    self.bi_orginal_list.append(point1)
                    self.bi_orginal_list.append(point2)        
        
        cprint("最后数组 178",Fore.RED)
        print(  self.bi_orginal_list)      
        
        

        self.Zbi_dates = [ item['date'].__str__()  for item in self.bi_orginal_list]
        self.Zbi_values = [item['value'] for item in self.bi_orginal_list]
          
        self.seg_list: List[CSeg_meta] = []
        self.eigenfx_lst: List[CEigenFX_meta] = []
        for seg in kl_list.seg_list:
            self.seg_list.append(CSeg_meta(seg))
            if seg.eigen_fx:
                self.eigenfx_lst.append(CEigenFX_meta(seg.eigen_fx))

        self.segseg_list: List[CSeg_meta] = [CSeg_meta(segseg) for segseg in kl_list.segseg_list]
        self.zs_lst: List[CZS_meta] = [CZS_meta(zs) for zs in kl_list.zs_list]
        self.segzs_lst: List[CZS_meta] = [CZS_meta(segzs) for segzs in kl_list.segzs_list]

        self.bs_point_lst: List[CBS_Point_meta] = [CBS_Point_meta(bs_point, is_seg=False) for bs_point in kl_list.bs_point_lst]
        self.seg_bsp_lst: List[CBS_Point_meta] = [CBS_Point_meta(seg_bsp, is_seg=True) for seg_bsp in kl_list.seg_bs_point_lst]

    def klu_iter(self):
        for klc in self.klc_list:
            yield from klc.klu_list

    def sub_last_kseg_start_idx(self, seg_cnt):
        if seg_cnt is None or len(self.data.seg_list) <= seg_cnt:
            return 0
        else:
            return self.data.seg_list[-seg_cnt].get_begin_klu().sub_kl_list[0].idx

    def sub_last_kbi_start_idx(self, bi_cnt):
        if bi_cnt is None or len(self.data.bi_list) <= bi_cnt:
            return 0
        else:
            return self.data.bi_list[-bi_cnt].begin_klc.lst[0].sub_kl_list[0].idx

    def sub_range_start_idx(self, x_range):
        for klc in self.data[::-1]:
            for klu in klc[::-1]:
                x_range -= 1
                if x_range == 0:
                    return klu.sub_kl_list[0].idx
        return 0

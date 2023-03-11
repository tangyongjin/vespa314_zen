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



class ZenPlotMeta: 
    def __init__(self, kl_list: CKLine_List):
        self.data = kl_list

        self.klc_list: List[Cklc_meta] = [Cklc_meta(klc) for klc in kl_list.lst]
        self.datetick = [klu.time.to_str() for klu in self.klu_iter()]
        self.klu_len = sum(len(klc.klu_list) for klc in self.klc_list)
        self.bi_list = [Bi_meta(bi) for bi in kl_list.bi_list]
        # 得到echarts 版本的 笔s
        self.BiPoints  = self.GET_BiPoints_echarts(kl_list.bi_list )
        # 得到echarts 版本的 线段
        self.SegPoints  = self.GET_SegPoints_echarts(kl_list.seg_list )
        

        self.seg_list: List[Seg_meta] = []
        self.eigenfx_lst: List[CEigenFX_meta] = []
        for seg in kl_list.seg_list:

            # print( vars(seg.start_bi._CBi__begin_klc._CKLine_Combiner__time_begin) )
            self.seg_list.append(Seg_meta(seg))
            if seg.eigen_fx:
                self.eigenfx_lst.append(CEigenFX_meta(seg.eigen_fx))
                
                
        
        self.segseg_list: List[Seg_meta] = [Seg_meta(segseg) for segseg in kl_list.segseg_list]
        
        # 走势/中枢?
        # _tmpZsLst= [ZS_meta(zs) for zs in kl_list.zs_list]
        self.zs_lst: List[ZS_meta] =  [ZS_meta(zs) for zs in kl_list.zs_list]
        cprint("走势/中枢***************",Fore.RED)
        # print(  _tmpZsLst  )
       
        # fo echarts  
        self.ZsAreas = self.GET_ZsArea_echarts(   self.zs_lst ) 
        
        self.segzs_lst: List[ZS_meta] = [ZS_meta(segzs) for segzs in kl_list.segzs_list]
        
        self.bs_point_lst: List[CBS_Point_meta] = [CBS_Point_meta(bs_point, is_seg=False) for bs_point in kl_list.bs_point_lst]
        self.seg_bsp_lst: List[CBS_Point_meta] = [CBS_Point_meta(seg_bsp, is_seg=True) for seg_bsp in kl_list.seg_bs_point_lst]

    def  GET_ZsArea_echarts(self, kl_list_zs_list):
         ZsAreas=[];
         cprint("走势/中枢?", Fore.RED)
        #  print(self.zs_lst)
         # print every element in the list
         for xzs in kl_list_zs_list:
            print( type(xzs.begin_kl  ) )
            print( vars(xzs) )
            print( xzs.begin_kl.time.__str__() )
            print( xzs.end_kl.time.__str__())
            tmp= { "is_sure": xzs.is_sure, "start": [xzs.begin_kl.time.__str__(), xzs.low], "end": [xzs.end_kl.time.__str__(), xzs.high] }             
            ZsAreas.append(tmp)
         return ZsAreas
   
          
    def  GET_SegPoints_echarts(self, kl_list_seg_list):
         echart_SegPoints=[]
         print(type(kl_list_seg_list))
         for seg in kl_list_seg_list:
            tmpSeg=Seg_meta_echarts(seg)
            point1={ "date": tmpSeg.begin_x, "value":tmpSeg.begin_y}
            point2={ "date": tmpSeg.end_x, "value":tmpSeg.end_y}
            
            if not echart_SegPoints:
                echart_SegPoints.append(point1)
                echart_SegPoints.append(point2)
            else:
                # print("List is not empty")
                if  echart_SegPoints[-1]==point1:
                    echart_SegPoints.append(point2)
                else:
                    echart_SegPoints.append(point1)
                    echart_SegPoints.append(point2)        
                    
            
         
        #  return BiPoints
         _SegPoints  = [[d['date'].__str__(), d['value']] for d in echart_SegPoints ]
         return _SegPoints     
        
        
        
    
    def  GET_BiPoints_echarts(self, kl_list_bi_list):
        bi_orginal_list =  []
        for xxxbi in kl_list_bi_list:
            
            point1={}
            point2={}

            if xxxbi._CBi__dir ==BI_DIR.UP:
                point1={ "date":xxxbi._CBi__begin_klc.time_end, "value": xxxbi._CBi__begin_klc.low  }
                point2={ "date":xxxbi._CBi__end_klc.time_end, "value":xxxbi._CBi__end_klc.high }
            else:   
                point1={ "date":xxxbi._CBi__begin_klc.time_end, "value": xxxbi._CBi__begin_klc.high  }
                point2={ "date":xxxbi._CBi__end_klc.time_end, "value":xxxbi._CBi__end_klc.low }
                
                
            # bi_orginal_list    
            
            if not bi_orginal_list:
                bi_orginal_list.append(point1)
                bi_orginal_list.append(point2)
            else:
                # print("List is not empty")
                if  bi_orginal_list[-1]==point1:
                      bi_orginal_list.append(point2)
                else:
                    bi_orginal_list.append(point1)
                    bi_orginal_list.append(point2)        
        
        # cprint("最后数组 178",Fore.RED)
        # print(  self.bi_orginal_list)      

        BiPoints  = [[d['date'].__str__(), d['value']] for d in bi_orginal_list ]
        return BiPoints

    
    
    
         
         
        
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


class Cklc_meta:
    def __init__(self, klc: CKLine):
        self.high = klc.high
        self.low = klc.low
        self.begin_idx = klc.lst[0].idx
        self.end_idx = klc.lst[-1].idx
        self.type = klc.fx if klc.fx != FX_TYPE.UNKNOWN else klc.dir

        self.klu_list = list(klc.lst)


class Bi_meta:
    def __init__(self, bi: CBi):
        self.idx = bi.idx
        self.dir = bi.dir
        self.type = bi.type
        self.begin_x = bi.get_begin_klu().idx
        self.end_x = bi.get_end_klu().idx
        self.begin_y = bi.get_begin_val()
        self.end_y = bi.get_end_val()
        self.id_sure = bi.is_sure


class Seg_meta:
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





class Seg_meta_echarts:
    def __init__(self, seg: CSeg):
        if type(seg.start_bi) == CBi:
            # cprint("类型是CBi",Fore.RED)
            self.begin_x = seg.start_bi.get_begin_klu()
            self.begin_y = seg.start_bi.get_begin_val()
            self.end_x = seg.end_bi.get_end_klu()
            self.end_y = seg.end_bi.get_end_val()
        else:
            assert type(seg.start_bi) == CSeg
            # cprint("类型是CSeg",Fore.RED)
            self.begin_x = seg.start_bi.start_bi.get_begin_klu()
            self.begin_y = seg.start_bi.start_bi.get_begin_val()
            self.end_x = seg.end_bi.end_bi.get_end_klu()
            self.end_y = seg.end_bi.end_bi.get_end_val()
        self.dir = seg.dir
        self.is_sure = seg.is_sure

        self.has_tl = False
        self.tl_y0 = None
        self.tl_y1 = None
        self.tl_x0 = None
        self.tl_x1 = None
        # .__str__()
        self.begin_x=self.begin_x.time.__str__()
        self.end_x=self.end_x.time.__str__()
        
        
        # print( self.begin_x)
        # print( self.begin_y) 
        # print( self.end_x)
        # print( self.end_y)




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


class ZS_meta:
    def __init__(self, zs: CZS):
        self.low = zs.low
        self.high = zs.high
    #   for echarts
        self.begin_kl = zs.begin
        self.begin = zs.begin.idx
        self.end = zs.end.idx
    #   for echarts
        self.end_kl = zs.end
        self.w = self.end - self.begin
        self.h = self.high - self.low
        self.is_sure = zs.is_sure
        self.sub_zs_lst = [ZS_meta(t) for t in zs.sub_zs_lst]
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

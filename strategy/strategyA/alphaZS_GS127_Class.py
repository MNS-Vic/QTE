''' 
1 替换output为return
2 替换n ame为self,n ame
3 替换所有的DF_变量为self.DF_
4 初始化emtpy，ind函数
'''

from apitool import *
import pandas as pd
import numpy as np

class AlphasZS_GS127(object):
    def __init__(self,open_,high_,low_,close_,vol_,amount_,opt_,vwap_):
        self.open=open_#保留一个格式用于其它因子DataFrame调整
        self.high = high_
        self.low = low_
        self.close = close_
        self.vol= vol_
        self.opt=opt_
        self.amount = amount_    
        self.vwap=vwap_      
        self.empty=lambda n:open_.applymap(lambda x:n)
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~自定义alpha~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def alphaZS_GS1(self,name = 'alphaZS_GS1',len1=10,maxbacklength=12):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alpha=vneg_(corr_((vdelta_(vlog_(vol_), 1)), (vdiv_(vsub_(close_,open_),open_)), len1))
        return  [name,alpha.round(num_round)]    
    def alphaZS_GS2(self,name = 'alphaZS_GS2',maxbacklength=2):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alpha=vneg_(vdelta_(vdiv_(vsub_(vsub_(close_, low_), vsub_(high_, close_)), vsub_(high_, low_)), 1))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS3(self,name = 'alphaZS_GS3',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alpha=tsmax_(corr_(high_, vol_, len1),len1)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS4(self,name = 'alphaZS_GS4',len1=10,maxbacklength=33):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alpha=tsargmin_(mean3_(mean3_(low_, ret_, stddev_(ret_, len1)), ret_, stddev_(ret_, len1)), len1)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS5(self,name = 'alphaZS_GS5',len1=10,maxbacklength=31):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #         
        alpha=vdiv_((decaylinear_(corr_((vwap_), sma2_(vol_,len1),len1), len1)),(decaylinear_(vdelta_(vadd_(div_(close_,2),div_(vwap_,2)), 3), len1)))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS6(self,name = 'alphaZS_GS6',len1=10,maxbacklength=21):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #       
        alpha=vneg_((vadd_(vadd_(stddev_(abs(vsub_(close_, open_)),len1),vsub_(close_,open_)),corr_(close_, open_,len1))))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS7(self,name = 'alphaZS_GS7',len1=10,maxbacklength=12):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vdiv_(tssum_(max_(vsub_(high_,delay_(close_,1)),0),len1),tssum_(max_(vsub_(delay_(close_,1),low_),0),len1))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS8(self,name = 'alphaZS_GS8',maxbacklength=None):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vsub_(vsub_(wma2_(vol_,13,2),wma2_(vol_,27,2)),wma2_(vsub_(wma2_(vol_,13,2),wma2_(vol_,27,2)),10,2))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS9(self,name = 'alphaZS_GS9',len1=10,maxbacklength=51):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vneg_(vmul_((vsub_(close_,max_(close_, 5))),(corr_((sma2_(vol_, len1)), low_, len1))))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS10(self,name = 'alphaZS_GS10',len1=10,maxbacklength=21):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vneg_(vpower_((vsub_(high_, tsmin_(high_, len1))),(corr_((vwap_), (sma2_(vol_,len1)), len1))))
        return  [name,alpha.round(num_round)]

    def alphaZS_GS11(self,name = 'alphaZS_GS11', maxbacklength=None):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=wma2_(vmul_(vsub_(mean2_(high_,low_),mean2_(delay_(high_,1),delay_(low_,1))),vdiv_(vsub_(high_,low_),vol_)),15,2)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS12(self,name = 'alphaZS_GS12',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=stddev_(tsrank_(low_, len1), len1)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS13(self,name = 'alphaZS_GS13',len1=10,maxbacklength=11):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vdelta_(vsub_(high_, close_), len1)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS14(self,name = 'alphaZS_GS14',len1=3,maxbacklength=12):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=clear_by_cond_(tsmin_(delay_(vol_, 1), len1), stddev_(tsrank_(delay_(tsrank_(delay_(vwap_, 1), len1), len1), len1*2), len1*2), tsrank_(delay_(vwap_, len1), len1))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS15(self,name = 'alphaZS_GS15',len1=10,maxbacklength=11):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=tsargmin_(vsub_(close_, high_), len1)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS16(self,name = 'alphaZS_GS16',len1=10,maxbacklength=11):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=stddev_((vol_), len1)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS17(self,name = 'alphaZS_GS17',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=tsmax_(corr_(close_, vol_, len1), len1)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS18(self,name = 'alphaZS_GS18',len1=6,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=tsmax_(corr_(vol_, high_, len1), len1)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS19(self,name = 'alphaZS_GS19',len1=10,maxbacklength=11):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=tsmax_(vdiv_(close_, high_), len1)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS20(self,name = 'alphaZS_GS20',len1=10,maxbacklength=21):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=tssum_(vadd_(clear_by_cond_(delay_(close_,1), close_, max_(high_,delay_(close_,1))), clear_by_cond_(close_, delay_(close_,1), min_(low_,delay_(close_,1)))), len1)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS21(self,name = 'alphaZS_GS21',len1=10,maxbacklength=41):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vneg_(tsmax_(corr_(tsrank_(vol_, len1), tsrank_(high_, len1), len1), len1))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS22(self,name = 'alphaZS_GS22',len1=10,maxbacklength=12):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vneg_((sign_(vdelta_((vadd_(mul_(open_, 0.85), mul_(high_, 0.15))),len1))))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS23(self,name = 'alphaZS_GS23',len1=10,maxbacklength=21):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vmul_(vadd_((tsmax_(vsub_(vwap_, close_), len1)), (tsmin_(vsub_(vwap_, close_), len1))), (vdelta_(vol_, 3)))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS24(self,name = 'alphaZS_GS24',len1=10,maxbacklength=12):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=tssum_(vmul_(vdiv_(vsub_(vsub_(close_,low_),vsub_(high_,close_)),vsub_(high_,low_)),vol_),len1)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS25(self,name = 'alphaZS_GS25',len1=10,maxbacklength=12):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vsub_(close_, delay_(close_,len1))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS26(self,name = 'alphaZS_GS26',len1=5,maxbacklength=21):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=if_then_else_(stddev_(vwap_, 1), delay_(sma2_(high_, len1), len1), if_then_else_(vwap_, high_, stddev_(vwap_, 1), open_), vdelta_(close_, len1))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS27(self,name = 'alphaZS_GS27',len1=4,maxbacklength=11):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vadd_(clear_by_cond_(close_, vwap_, vadd_(vadd_(vdelta_(close_, len1), vol_), vol_)), (vol_))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS28(self,name = 'alphaZS_GS28',len1=4,maxbacklength=21):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=(tsargmin_(tsargmax_(low_, len1), len1))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS29(self,name = 'alphaZS_GS29',len1=3,maxbacklength=15):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=tsargmin_(vdelta_(high_, len1), len1)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS30(self,name = 'alphaZS_GS30',len1=4,maxbacklength=11):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=tsmax_(vsub_(close_, vwap_), len1)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS31(self,name = 'alphaZS_GS31',len1=5,maxbacklength=11):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=decaylinear_(vdiv_(vwap_, close_), len1)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS32(self,name = 'alphaZS_GS32',len1=5,maxbacklength=11):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=tssum_(vadd_(clear_by_cond_(close_, delay_(close_,1), vol_), clear_by_cond_(delay_(close_,1), close_, vneg_(vol_))), len1)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS33(self,name = 'alphaZS_GS33',len1=4,maxbacklength=101):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vadd_(tsrank_(decaylinear_(corr_(low_, sma2_(vol_,len1*2), len1), len1),len1), tsrank_(decaylinear_(vdelta_((vwap_),len1), len1*3),len1*4))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS34(self,name = 'alphaZS_GS34',len1=10,maxbacklength=111):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vmul_((vdelta_((vadd_(mul_(close_, 0.6), mul_(open_, 0.4))), 1)), (corr_(vwap_, sma2_(vol_,len1*10), len1)))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS35(self,name = 'alphaZS_GS35',len1=3,maxbacklength=51):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=min_((decaylinear_(vsub_(vadd_(mean2_(high_, low_), high_), vadd_(vwap_, high_)), len1*2)),(decaylinear_(corr_(mean2_(high_, low_), sma2_(vol_,len1*7), len1), len1*2)))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS36(self,name = 'alphaZS_GS36',len1=10,maxbacklength=12):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vdiv_(vsub_(close_, delay_(close_,len1)), delay_(close_,len1))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS37(self,name = 'alphaZS_GS37',len1=10,maxbacklength=11):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=corr_(high_, vdiv_(vwap_, close_), len1)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS38(self,name = 'alphaZS_GS38',len1=4,maxbacklength=12):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=tsmin_(tsrank_(vol_, len1), len1)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS39(self,name = 'alphaZS_GS39',len1=5,maxbacklength=11):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vdelta_(vsub_(close_, vwap_), len1)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS40(self,name = 'alphaZS_GS40',len1=6,maxbacklength=21):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=clear_by_cond_(vdelta_(vsub_(low_, vol_), 2*len1), vmul_(vol_, open_), tsargmin_(vmul_(vwap_, close_), len1))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS41(self,name = 'alphaZS_GS41',maxbacklength=1):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=(vdiv_(close_, vwap_))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS42(self,name = 'alphaZS_GS42',len1=10,maxbacklength=11):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=(stddev_(vol_, len1))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS43(self,name = 'alphaZS_GS43',len1=10,maxbacklength=11):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=tsmin_(vdiv_(close_, vwap_), len1)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS44(self,name = 'alphaZS_GS44',len1=10,maxbacklength=101):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vdiv_(vsub_(mean3_(high_,low_,close_),sma2_(mean3_(high_,low_,close_),len1)),mul_(sma2_(abs(vsub_(close_,sma2_(mean3_(high_,low_,close_),len1))),len1),0.015))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS45(self,name = 'alphaZS_GS45',maxbacklength=None):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vdiv_(wma2_(max_(vsub_(close_,delay_(close_,1)),0),12,1),wma2_(abs(vsub_(close_,delay_(close_,1))),12,1))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS46(self,name = 'alphaZS_GS46',len1=10,maxbacklength=21):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=tssum_(vadd_(clear_by_cond_(close_, delay_(close_,1), vol_), clear_by_cond_(delay_(close_,1), close_, vneg_(vol_))),len1)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS47(self,name = 'alphaZS_GS47',len1=10,maxbacklength=41):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vmul_(tsrank_(vdiv_(vol_, sma2_(vol_,2*len1)), 2*len1), tsrank_(vneg_(vdelta_(close_, len1)),len1))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS48(self,name = 'alphaZS_GS48',len1=10,maxbacklength=41):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vneg_(vadd_((decaylinear_(vdelta_(vwap_, len1), len1*2)), tsrank_(decaylinear_(vdiv_(vsub_(vadd_(mul_(low_, 0.9), mul_(low_, 0.1)), vwap_),vsub_(open_, mean2_(high_,low_))), len1*3), len1*2)))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS49(self,name = 'alphaZS_GS49',len1=20,maxbacklength=21):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=stddev_(vol_,len1)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS50(self,name = 'alphaZS_GS50',maxbacklength=11):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vmul_(vmul_(vneg_((vsub_(open_, delay_(high_, 1)))), (vsub_(open_, delay_(close_, 1)))), (vsub_(open_, delay_(low_, 1))))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS51(self,name = 'alphaZS_GS51',maxbacklength=101):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vdiv_(wma2_(vsub_(high_,low_),10,2),wma2_(wma2_(vsub_(high_,low_),10,2),10,2))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS52(self,name = 'alphaZS_GS52',maxbacklength=None):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vsub_(wma2_(vdiv_(vmul_(vol_,vsub_(vsub_(close_,low_),vsub_(high_,close_))),vsub_(high_,low_)),11,2),wma2_(vdiv_(vmul_(vol_,vsub_(vsub_(close_,low_),vsub_(high_,close_))),vsub_(high_,low_)),4,2))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS53(self,name = 'alphaZS_GS53',len1=10,maxbacklength=21):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=(vmul_((delay_(vdiv_(vsub_(high_, low_), vdiv_(tssum_(close_, len1), len1)), 2)), ((vol_))) / vdiv_(vdiv_(vsub_(high_, low_), vdiv_(tssum_(close_, len1), len1)), (vsub_(vwap_, close_))))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS54(self,name = 'alphaZS_GS54',len1=10,maxbacklength=21):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vdiv_(vsub_(close_, vwap_), decaylinear_((tsmax_(close_, len1)),2))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS55(self,name = 'alphaZS_GS55',maxbacklength=101):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vdiv_(vmul_(sma2_(vsub_(ret_,wma2_(vdiv_(vsub_(close_,delay_(close_,1)),delay_(close_,1)),61,2)),20),vsub_(ret_,wma2_(ret_,61,2))),wma2_(vmul_(vsub_(ret_,vsub_(ret_,wma2_(ret_,61,2))),vsub_(ret_,vsub_(ret_,wma2_(ret_,61,2)))),61,2))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS56(self,name = 'alphaZS_GS56',maxbacklength=1):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vmul_(mean3_(close_,high_,low_),vol_)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS57(self,name = 'alphaZS_GS57',len1=5,maxbacklength=51):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vneg_(max_((decaylinear_(vdelta_(vwap_, 5), len1)), (decaylinear_(vneg_(vdiv_(vdelta_(vadd_(mul_(open_, 0.15), mul_(low_,0.85)),2), vadd_(mul_(open_, 0.15), mul_(low_, 0.85)))), len1))))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS58(self,name = 'alphaZS_GS58',maxbacklength=21):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vdiv_(open_, delay_(close_,1))-1
        return  [name,alpha.round(num_round)]
    def alphaZS_GS59(self,name = 'alphaZS_GS59',len1=3,maxbacklength=11):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vneg_(tssum_((corr_((high_), (vol_), len1)), len1))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS60(self,name = 'alphaZS_GS60',len1=5,maxbacklength=21):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vadd_(tsmin_(((vlog_(tssum_(tsmin_(((vneg_((vdelta_(close_, 5))))), len1), 1)))), 5),tsrank_(delay_(vneg_(ret_), 5), len1))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS61(self,name = 'alphaZS_GS61',maxbacklength=101):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vsub_(vsub_(high_,wma2_(close_,15,2)),vsub_(low_,wma2_(close_,15,2)))/close_
        return  [name,alpha.round(num_round)]
    def alphaZS_GS62(self,name = 'alphaZS_GS62',len1=10,maxbacklength=12):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=(vmul_(vmul_(vmul_(vneg_(ret_), sma2_(vol_,len1)), vwap_), vsub_(high_, close_)))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS63(self,name = 'alphaZS_GS63',len1=10,maxbacklength=11):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vdiv_(vneg_(vmul_(vsub_(low_, close_), vmul_(vmul_(vmul_(open_, open_),vmul_(open_, open_)),open_))), vmul_(vsub_(close_, high_), vmul_(vmul_(vmul_(close_, close_),vmul_(close_, close_)),close_)))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS64(self,name = 'alphaZS_GS64',len1=10,maxbacklength=21):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=add_(vneg_(tsargmax_(high_,len1)),20)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS65(self,name = 'alphaZS_GS65',maxbacklength=2):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=(vneg_(vmul_(vneg_(sub_(vdiv_(open_, close_),1)), vneg_(sub_(vdiv_(open_, close_),1)))))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS66(self,name = 'alphaZS_GS66',len1=10,maxbacklength=31):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=corr_((vdiv_(vsub_(close_, tsmin_(low_, len1)), vsub_(tsmax_(high_, len1), tsmin_(low_,len1)))), (vol_), len1)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS67(self,name = 'alphaZS_GS67',len1=6,maxbacklength=13):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vsign_(mean3_(ret_, max_(ret_, tssum_(open_, len1)), mean3_(ret_, max_(ret_, open_), ret_)))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS68(self,name = 'alphaZS_GS68',len1=5,maxbacklength=11):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vdelta_(clear_by_cond_(close_, high_, clear_by_cond_(close_, high_, tsmin_(tsmin_(low_, len1), len1))), 1)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS69(self,name = 'alphaZS_GS69',len1=2,maxbacklength=5):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vsub_(vwap_, decaylinear_(close_, len1))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS70(self,name = 'alphaZS_GS70',len1=5,maxbacklength=11):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        # alpha=decaylinear_(corr_(vmul_(vol_, vmul_(vol_, vmul_(vmul_(vol_, vmul_(vol_, vmul_(vol_, vol_))), vol_))), high_, len1), len1*2)
        alpha = decaylinear_(corr_(vmul_(vol_, vol_), high_, len1), len1 * 2)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS71(self,name = 'alphaZS_GS71',len1=10,maxbacklength=21):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vsub_(tsargmin_(vdiv_(close_, vwap_), len1), stddev_(vol_, len1))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS72(self,name = 'alphaZS_GS72',maxbacklength=11):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vmul_(if_then_else_(vdiv_(low_, vdiv_(high_, vdiv_(vdiv_(open_, vdiv_(high_, vdiv_(vdiv_(high_, vol_), vol_))), vol_))), high_, vdiv_(vsub_(low_, delay_(high_, 5)), close_), low_), vdiv_(vdiv_(open_, vdiv_(high_, vdiv_(open_, vdiv_(high_, vdiv_(vdiv_(high_, vol_), vol_))))), vdiv_(vdiv_(high_, vdiv_(wma2_(low_, 3, (5)), vol_)), vdiv_(open_, vdiv_(high_, vdiv_(vdiv_(open_, vol_), vol_))))))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS73(self,name = 'alphaZS_GS73',len1=10,maxbacklength=31):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=corr_(div_(vol_, 8), vadd_(vol_, tsrank_(vwap_, len1)), len1)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS74(self,name = 'alphaZS_GS74',len1=6,maxbacklength=101):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vpower_(tsargmin_(close_, len1), mean2_(mul_(mean2_(mul_(mean2_(mean2_(mul_(mean2_(mean2_(mean2_(mul_(mean2_(ret_, ret_), len1), high_), ret_), ret_), len1), mean2_(mul_(mean2_(mean2_(mul_(mean2_(ret_, ret_), len1), high_), ret_), len1), high_)), ret_), len1), high_), len1), high_))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS75(self,name = 'alphaZS_GS75',len1=5,maxbacklength=101):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=tsargmin_(tsmin_(tsmin_(tsmin_(tsmin_(high_, (len1)), (((len1)))), (len1)), (((len1)))), ((len1)))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS76(self,name = 'alphaZS_GS76',len1=5,maxbacklength=51):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=min_(tssum_(vdelta_(vdelta_(ret_, 2), (len1)), ((len1))), tssum_(vol_, len1))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS77(self,name = 'alphaZS_GS77',len1=5,maxbacklength=41):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=tsargmin_(mean2_(high_, tsrank_(add_(high_, 4), len1)), (len1))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS78(self,name = 'alphaZS_GS78',len1=5,maxbacklength=21):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=corr_(tsmax_(ret_, len1), mean3_(ret_, mean3_(close_, open_, ret_), ret_), len1)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS79(self,name = 'alphaZS_GS79',len1=2,maxbacklength=11):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=stddev_((vol_), (len1))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS80(self,name = 'alphaZS_GS80',maxbacklength=11):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=clear_by_cond_(tsargmin_(vlog_(close_), 1), clear_by_cond_(vwap_, open_, vwap_), mul_(ret_, 2))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS81(self,name = 'alphaZS_GS81',maxbacklength=11):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vdelta_(vol_, (3))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS82(self,name = 'alphaZS_GS82',len1=10,maxbacklength=31):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=mul_(tsmax_(tsmax_(ret_, len1), len1), ((6)))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS83(self,name = 'alphaZS_GS83',len1=10,maxbacklength=11):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=stddev_(((add_(ret_, 6))), len1)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS84(self,name = 'alphaZS_GS84',maxbacklength=11):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=delay_(vadd_(vol_, vol_), (2))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS85(self,name = 'alphaZS_GS85',len1=5,maxbacklength=101):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=sma2_(wma2_(tsargmax_(low_, len1), 8, 8), (1))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS86(self,name = 'alphaZS_GS86',len1=5,maxbacklength=11):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=tsmin_(vdiv_(vwap_, close_), (len1))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS87(self,name = 'alphaZS_GS87',len1=10,maxbacklength=101):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vneg_(min_(min_(vol_, mul_(vsign_(corr_(vwap_, min_(min_(vol_, mul_(vsign_(corr_(vwap_, high_, len1)), len1)), mul_(vsign_(corr_(vwap_, high_, len1)), 10)), len1)), 3)), mul_(vwap_, 3)))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS88(self,name = 'alphaZS_GS88',len1=10,maxbacklength=12):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=tsargmin_(vmul_(div_(open_, 9), vmul_(div_(open_, 9), vwap_)), ((len1)))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS89(self,name = 'alphaZS_GS89',len1=10,maxbacklength=101):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=wma2_(corr_(vol_, vwap_, len1), (8), ((3)))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS90(self,name = 'alphaZS_GS90',maxbacklength=2):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vsub_(add_(vwap_, 7), if_then_else_(vwap_, clear_by_cond_(vwap_, open_, close_), close_, close_))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS91(self,name = 'alphaZS_GS91',len1=5,maxbacklength=15):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=decaylinear_((tsargmin_(ret_, (len1))), (len1*2))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS92(self,name = 'alphaZS_GS92',maxbacklength=2):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=if_then_else_(max_(low_, close_), if_then_else_(vol_, ret_, high_, high_), ret_, max_(open_, open_))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS93(self,name = 'alphaZS_GS93',maxbacklength=101):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=wma2_(vsub_(close_, vwap_), (8), (5))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS94(self,name = 'alphaZS_GS94',len1=5,maxbacklength=101):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=wma2_(vdelta_(vmul_(low_, ret_), (len1)), (10), 10)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS95(self,name = 'alphaZS_GS95',len1=3,maxbacklength=11):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=mean2_(tsargmax_(vsub_(open_, ret_), len1), div_(ret_, 10))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS96(self,name = 'alphaZS_GS96',len1=5,maxbacklength=11):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=max_(tsrank_(open_, len1), if_then_else_(vwap_, close_, high_, (vsub_(ret_, vwap_))))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS97(self,name = 'alphaZS_GS97',len1=5,maxbacklength=11):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vabs_(decaylinear_(ret_, len1))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS98(self,name = 'alphaZS_GS98',maxbacklength=101):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=wma2_(vdiv_(high_, close_), ((8)), 4)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS99(self,name = 'alphaZS_GS99',len1=10,maxbacklength=21):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vdiv_(tsrank_(open_, len1), tsmax_(ret_, len1))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS100(self,name = 'alphaZS_GS100',len1=5,maxbacklength=11):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=mean2_(max_(vol_, vabs_(tsargmin_(low_, (len1)))), vlog_(vlog_(ret_)))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS101(self,name = 'alphaZS_GS101',len1=5,maxbacklength=21):

        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alpha=clear_by_cond_(vabs_(tsrank_(vabs_(tsrank_(ret_, len1*2)), len1*2)), tsmax_(vol_, len1), vdelta_((decaylinear_(vwap_, len1)), len1))
        return  [name,alpha.round(num_round)]

    def alphaZS_GS102(self,name = 'alphaZS_GS102',len1=5,maxbacklength=11):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=clear_by_cond_(tsrank_(low_, len1), tsargmin_(low_, len1), tsargmin_(vwap_, len1))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS103(self,name = 'alphaZS_GS103',len1=5,maxbacklength=11):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=corr_(clear_by_cond_(tssum_(decaylinear_(vdiv_(ret_, low_), 1), len1), add_(vneg_(mean2_(max_(open_, add_(tsargmax_(ret_, ((len1))), 4)), vdelta_(ret_, 5))), 7), close_), add_(add_(tsargmax_(ret_, ((len1))), 4), 8), (len1))
        return  [name,alpha.round(num_round)]

    def alphaZS_GS104(self, name = 'alphaZS_GS104', len1=5, maxbacklength=21):

        if maxbacklength==None:maxbacklength=len(self.close)
        open_ = self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_ = self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_ = self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]
        amount_ = self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]
        ret_=close_.pct_change().round(num_round)
        alpha =tsrank_(decaylinear_(ret_, (len1)), (len1*2))
        return [name, alpha.round(num_round)]

    def alphaZS_GS105(self, name = 'alphaZS_GS105', len1=10, maxbacklength=21):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=tsrank_(corr_(close_, vol_, len1), ((len1)))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS106(self,name = 'alphaZS_GS106',len1=10,maxbacklength=101):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=if_then_else_(mean3_(close_, close_, if_then_else_(vol_, low_, low_, vwap_)), wma2_(low_, 7, 2), corr_(vwap_, vlog_(vol_), len1), decaylinear_(open_, len1))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS107(self,name = 'alphaZS_GS107',len1=5,maxbacklength=31):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=decaylinear_(corr_(vsign_(ret_), stddev_(low_, len1), len1*2),len1)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS108(self,name = 'alphaZS_GS108',len1=5,maxbacklength=11):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=delay_(vdiv_(vwap_, close_), len1)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS109(self,name = 'alphaZS_GS109',len1=10,maxbacklength=11):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=tsrank_(vdiv_(low_, div_(close_, 3)), len1)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS110(self,name = 'alphaZS_GS110',len1=4,maxbacklength=15):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=decaylinear_(tsrank_(ret_, (len1)), (len1*2))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS111(self,name = 'alphaZS_GS111',len1=5,maxbacklength=11):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=tsargmin_(open_, (len1))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS112(self,name = 'alphaZS_GS112',len1=5,maxbacklength=21):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=clear_by_cond_(tsargmin_(vwap_, len1), clear_by_cond_(vwap_, open_, vlog_(close_)), mul_(ret_, 2))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS113(self,name = 'alphaZS_GS113',len1=5,maxbacklength=21):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=decaylinear_(corr_(high_, vol_, (len1)), ((len1*2)))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS114(self,name = 'alphaZS_GS114',len1=5,maxbacklength=21):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=sma2_(vdiv_(vwap_, close_), (len1))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS115(self,name = 'alphaZS_GS115',len1=2,maxbacklength=16):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=decaylinear_(tsargmax_(vsub_(open_, vwap_), (len1)), len1*4)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS116(self,name = 'alphaZS_GS116',len1=3,maxbacklength=51):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=(tsrank_(tsrank_(sma2_(ret_, len1), len1*3), len1*3))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS117(self,name = 'alphaZS_GS117',len1=10,maxbacklength=21):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=mean2_(vdiv_(vwap_, tsrank_(vol_, len1)), vneg_(close_))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS118(self,name = 'alphaZS_GS118',len1=10,maxbacklength=101):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=wma2_(sma2_(corr_(close_, low_, (len1)), (len1)), ((9)), (3))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS119(self,name = 'alphaZS_GS119',maxbacklength=101):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=mean2_(wma2_(wma2_(vneg_(close_), 7, 5), 7, 6), tsmax_(low_, (((5)))))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS120(self,name = 'alphaZS_GS120',maxbacklength=101):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=tsrank_(min_(wma2_(wma2_(min_(ret_, wma2_(vadd_(ret_, open_), (((7))), 5)), (7), 5), (7), 5), wma2_(high_, (7), 5)), 5)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS121(self,name = 'alphaZS_GS121',len1=3,maxbacklength=11):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=clear_by_cond_(vsub_(ret_, low_), mean2_(vol_, open_), sma2_(vol_, len1))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS122(self,name = 'alphaZS_GS122',len1=4,maxbacklength=11):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=tsmin_(tsrank_(vwap_, len1), (len1))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS123(self,name = 'alphaZS_GS123',maxbacklength=1):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vadd_(low_, if_then_else_(close_, high_, high_, vneg_(close_)))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS124(self,name = 'alphaZS_GS124',len1=10,maxbacklength=12):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=tsargmin_(open_, len1)
        return  [name,alpha.round(num_round)]
    def alphaZS_GS125(self,name = 'alphaZS_GS125',maxbacklength=101):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vdiv_(vmul_(sma2_(vsub_(ret_,wma2_(vdiv_(vsub_(close_,delay_(close_,1)),delay_(close_,1)),61,2)),20),vsub_(ret_,wma2_(ret_,61,2))),wma2_(vmul_(vsub_(ret_,vsub_(ret_,wma2_(ret_,61,2))),vsub_(ret_,vsub_(ret_,wma2_(ret_,61,2)))),61,2))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS126(self,name = 'alphaZS_GS126',len1=10,maxbacklength=21):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vdiv_(tssum_(max_(vsub_(high_,delay_(close_,1)),0),len1),tssum_(max_(vsub_(delay_(close_,1),low_),0),len1))
        return  [name,alpha.round(num_round)]
    def alphaZS_GS127(self,name = 'alphaZS_GS127',len1=3,maxbacklength=51):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alpha=vadd_(min_(((vlog_(tssum_(tsmin_(((vneg_((vdelta_(close_, 5))))), len1*2), len1)))), 5),tsrank_(delay_(vneg_(ret_), 6), len1*2))
        return  [name,alpha.round(num_round)]
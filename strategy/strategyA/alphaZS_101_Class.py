''' 
1 替换output为return
2 替换n ame为self,n ame
3 替换所有的DF_变量为self.DF_
4 初始化emtpy，ind函数
'''

from apitool import *
import pandas as pd
import numpy as np

class AlphasZS_YOY(object):
    def __init__(self,open_,high_,low_,close_,vol_,amount_,opt_,vwap_):
        #函数与self,name的对应表    mya.open = self.open
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
    def alphaZS_YOY1(self,name = 'alphaZS_YOY1',len1=15,maxbacklength=141):
        '''
        ???
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  (tsargmax_(np.power(if_(ret_ < 0, std_(ret_, len1*2), close_), 2), len1)) - 0.5
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY2(self,name = 'alphaZS_YOY2',len1=5,maxbacklength=11):
        '''
        刻画成交量变动幅度与当日股价涨跌关系，反映市场多空分歧
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  -1 * (corr_((delta_(log_(vol_), 2)), ((close_ - open_)/open_), len1))
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY3(self,name = 'alphaZS_YOY3',len1=10,maxbacklength=11):
        '''
        刻画当日开盘价与成交量关系，反映市场多空情绪
        '''
        alpha = -1 * (corr_((open_), (vol_), len1))
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY4(self,name = 'alphaZS_YOY4',len1=10,maxbacklength=11):
        '''
        最低价排名情况变动，反映市场情绪
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  -1*tsrank_((low_), len1)
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY5(self,name = 'alphaZS_YOY5',len1=10,maxbacklength=12):
        '''
        开盘价与10天内均价均价差排名*收盘价与均价差排名，反映当天内市场情绪
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  ((open_ - sum_(vwap_, len1)/len1)) * (-1 * abs_((close_ - vwap_)))
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY6(self,name = 'alphaZS_YOY6',len1=10,maxbacklength=11):
        '''
        与alphaZS_YOY3类似.
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  -1 * (corr_(open_, vol_, len1))
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY7(self,name = 'alphaZS_YOY7',len1=20,maxbacklength=22):
        pass
        '''
        当日成交量与收盘价变动情况，反映市场热度
        '''
        # if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  if_(mean_(vol_, len1)<vol_, -1 * tsrank_(abs_(delta_(close_, 7)), len1) * sign_(delta_(close_, 7)), -1)
        # #------------output---------------------
        # return [name,alpha.round(num_round)]
    
    def alphaZS_YOY8(self,name = 'alphaZS_YOY8',len1=5,maxbacklength=21):
        '''
        近5天收益率及开盘价乘积的变化，反映中短期市场热度
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  -1 * (delta_(sum_(open_, len1)*sum_(ret_, len1), len1*2))
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY9(self,name = 'alphaZS_YOY9',len1=5,maxbacklength=11):
        pass
        '''
        5天内的涨跌情况
        '''
        # if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  -1*(if_(0<tsmin_(delta_(close_,1),len1), delta_(close_, 1), if_(tsmax_(delta_(close_, 1), len1), delta_(close_, 1), -1*(delta_(close_, 1)))))
        # #------------output---------------------
        # return [name,alpha.round(num_round)]
    
    def alphaZS_YOY10(self,name = 'alphaZS_YOY10',len1=5,maxbacklength=16):
        '''
        与alphaZS_YOY9类似。
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  (if_(tsmin_(delta_(close_, 1), len1), delta_(close_, 1), if_(tsmax_(delta_(close_, 1), len1), delta_(close_, 1), -1*delta_(close_, 1))))
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY11(self,name = 'alphaZS_YOY11',len1=4,maxbacklength=11):
        '''
        三天内的均价与收盘价价差情况，反映短期内股价异动
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  ((tsmax_(vwap_ - close_, len1)) + (tsmin_(vwap_ - close_, len1))) * (delta_(vol_, len1))
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY12(self,name = 'alphaZS_YOY12',len1=10,maxbacklength=11):
        pass
        '''
        成交量变化与股价变化的关系
        '''
        # if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  -1 * sign_(delta_(vol_, 1)) * delta_(close_, 1)
        # #------------output---------------------
        # return [name,alpha.round(num_round)]
    
    def alphaZS_YOY13(self,name = 'alphaZS_YOY13',len1=5,maxbacklength=11):
        '''
        收盘价与成交量相关性
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  -1 * (cov_((close_), (vol_), len1))
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY14(self,name = 'alphaZS_YOY14',len1=10,maxbacklength=11):
        pass
        '''
        收益变化与价量相关系数乘积
        '''
        # if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  -1 * (delta_(ret_, 3)) * cov_(open_, vol_, len1)
        # #------------output---------------------
        # return [name,alpha.round(num_round)]
    
    def alphaZS_YOY15(self,name = 'alphaZS_YOY15',len1=3,maxbacklength=11):
        '''
        最高价与成交量的相关性排名
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  -1 * sum_((corr_((high_), (vol_), len1)), len1)
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY16(self,name = 'alphaZS_YOY16',len1=5,maxbacklength=11):
        '''
        与alphaZS_YOY13类似。
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  -1 * (cov_((high_), (vol_), len1))
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY17(self,name = 'alphaZS_YOY17',len1=5,maxbacklength=21):
        '''
        成交量变化、收盘价变化及差价变化的情况。
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  -1 * (tsrank_(close_, len1*4)) * (delta_(delta_(close_, 1), 1)) * (tsrank_(vol_/mean_(vol_, len1*2), len1))
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY18(self,name = 'alphaZS_YOY18',len1=5,maxbacklength=11):
        '''
        刻画股价波动
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  -1 * (std_(abs_(close_ - open_), len1) + close_ + open_ + corr_(close_, open_, len1*2))
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY19(self,name = 'alphaZS_YOY19',len1=10,maxbacklength=101):
        pass
        '''
        当日收盘价变化与过去一年收益的情况，刻画年线趋势
        '''
        # if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  sign_(delta_(close_, 7)) * (1 + (1 + sum_(ret_, len1*10)))
        # #------------output---------------------
        # return [name,alpha.round(num_round)]
    
    def alphaZS_YOY20(self,name = 'alphaZS_YOY20',len1=10,maxbacklength=11):
        '''
        刻画当日开盘市场情绪
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  -1 * (open_ - delay_(high_, 1)) * (open_ - delay_(close_, 1)) * (open_ - delay_(low_, 1))
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY21(self,name = 'alphaZS_YOY21',len1=4,maxbacklength=41):
        pass
        '''
        价格通道区间突破因子
        '''
        # if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  if_(mean_(close_,len1*4)+std_(close_,len1*4)<mean_(close_,len1),-1, if_(mean_(close_,len1)<mean_(close_,len1*4)-std_(close_,len1*4),1,if_(1<vol_/mean_(vol_,len1*4),1,-1)))
        # #------------output---------------------
        # return [name,alpha.round(num_round)]
    
    def alphaZS_YOY22(self,name = 'alphaZS_YOY22',len1=5,maxbacklength=11):
        '''
        价量相关性变化与股价波动
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  -1 * delta_(corr_(high_, vol_, len1), len1) * (std_(close_, len1*2))
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY23(self,name = 'alphaZS_YOY23',len1=10,maxbacklength=21):
        '''
        高点突破20日高价线
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  if_(mean_(high_, len1) < high_, -1*delta_(high_,2), 0)
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY24(self,name = 'alphaZS_YOY24',len1=20,maxbacklength=41):
        '''
        100天均线涨幅是否过5%
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  if_(delta_(mean_(close_,len1),len1)/delay_(close_,len1)<=0.05, -1*(close_-tsmin_(close_, len1)), -1*delta_(close_,3))
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY25(self,name = 'alphaZS_YOY25',len1=10,maxbacklength=11):
        '''
        一锅乱炖
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  (-1*ret_*mean_(vol_,len1)*vwap_*(high_ - close_))
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY26(self,name = 'alphaZS_YOY26',len1=10,maxbacklength=None):
        '''
        成交量与高价的相关性，反映短期内个股趋势
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  -1 * tsmax_(corr_(tsrank_(vol_, len1), tsrank_(high_, len1), len1), len1)
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY27(self,name = 'alphaZS_YOY27',len1=10,maxbacklength=21):
        '''
        找出价量相关性最高的票,2018.06
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  if_(1.5<(sum_(corr_((vol_), (vwap_), len1), 2)/2.0), -1, 1)
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY28(self,name = 'alphaZS_YOY28',len1=10,maxbacklength=101):
        '''
        ???
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  scale_(corr_(mean_(vol_.fillna(0),len1), low_.fillna(0), len1) + (high_.fillna(0) + low_.fillna(0))/2 - close_.fillna(0))
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY29(self,name = 'alphaZS_YOY29',len1=10,maxbacklength=21):
        '''
        ???
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  min_(prod_(((scale_(log_(sum_(tsmin_(((-1*(delta_(close_ - 1, 5)))),len1),1))))),1),empty_(5)) + tsrank_(delay_(-1*ret_, len1), 5)
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY30(self,name = 'alphaZS_YOY30',len1=10,maxbacklength=21):
        '''
        近期涨跌情况与成交量变化，短期市场热度。
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  (1.0-(sign_(delta_(close_,1)) + sign_(delay_(close_,1) - delay_(close_,2)) + sign_(delay_(close_,2) - delay_(close_,3))))*sum_(vol_,len1)/sum_(vol_,len1*2).replace(0,np.nan)
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY31(self,name = 'alphaZS_YOY31',len1=10,maxbacklength=41):
        '''
        价格变化程度，计算逻辑混乱
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  (((decaylinear_(-1*((delta_(close_,len1))), len1)))) + (-1*delta_(close_, 3)) + sign_(scale_(corr_(mean_(vol_,len1*2), low_, len1*2)))
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY32(self,name = 'alphaZS_YOY32',len1=5,maxbacklength=121):
        '''
        当天股价与此前价格的比较，
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  scale_(mean_(close_,len1*2) - close_) + 20 * scale_(corr_(vwap_, delay_(close_, len1), len1*10))
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY33(self,name = 'alphaZS_YOY33',maxbacklength=11):
        '''
        当日市场情绪，越小越热
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  (open_/close_ - 1)
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY34(self,name = 'alphaZS_YOY34',len1=2,maxbacklength=11):
        '''
        刻画收益与价格波动情况
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  (1-(std_(ret_, len1)/std_(ret_, len1*2)) + 1 - (delta_(close_, 1)))
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY35(self,name = 'alphaZS_YOY35',len1=10,maxbacklength=31):
        '''
        成交量，收益，以及股价在一段时间内的情况
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  tsrank_(vol_, len1*2) * (1 - tsrank_(close_ + high_ - low_, len1)) * (1 - tsrank_(ret_, len1*2))
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY36(self,name = 'alphaZS_YOY36',len1=5,maxbacklength=41):
        '''
        多个指标结合
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  2.21*(corr_(close_-open_,delay_(vol_,1),len1*3))+0.7*(open_-close_)+\
                0.73*(tsrank_(delay_(-1*ret_,6),len1))+(abs_(corr_(vwap_,mean_(vol_,len1*4),len1)))+\
                0.6*((mean_(close_,len1*4)-open_)*(close_-open_))
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY37(self,name = 'alphaZS_YOY37',len1=10,maxbacklength=121):
        '''
        股价波动变化与收盘价的相关性，刻画长+短期趋势
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  (corr_(delay_(open_ - close_, 1), close_, len1*10)) + (open_ - close_)
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY38(self,name = 'alphaZS_YOY38',len1=10,maxbacklength=11):
        '''
        当日股价涨跌与10日内趋势结合判断指标
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  -1*(tsrank_(close_, len1)) * (close_/open_)
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY39(self,name = 'alphaZS_YOY39',len1=10,maxbacklength=121):
        '''
        中长期指标结合，价格变化、量能变化、年内收益情况排名
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  (delta_(close_,len1)*(1-(decaylinear_(vol_/mean_(vol_,len1).replace(0,np.nan), len1)))) * (1 + (sum_(ret_, len1*10)))
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY40(self,name = 'alphaZS_YOY40',len1=10,maxbacklength=13):
        '''
        高价波动与价量关系，刻画市场短期趋势
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  -1*(std_(high_,len1)) * corr_(high_,vol_,len1)
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY41(self,name = 'alphaZS_YOY41',maxbacklength=1):
        pass
        '''
        当日股价波动与均价的关系，反映多空力量
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  -1*(sqrt_(high_ * low_) - vwap_)
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY42(self,name = 'alphaZS_YOY42',maxbacklength=1):
        pass
        '''
        当日收盘情况，一定程度上反映股价短期趋势
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  1.0*(vwap_ - close_)/(vwap_+close_)
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY43(self,name = 'alphaZS_YOY43',len1=7,maxbacklength=31):
        '''
        量价突破
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  1.0*tsrank_(1.0*vol_/mean_(vol_, 2*len1).replace(0,np.nan), 2*len1) * tsrank_(-1.0*delta_(close_,7), len1)
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY44(self,name = 'alphaZS_YOY44',len1=5,maxbacklength=11):
        '''
        量价相关
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  -1.0*corr_(high_, (vol_), len1)
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY45(self,name = 'alphaZS_YOY45',len1=4,maxbacklength=101):
        '''
        量价指标
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  -1*(mean_(delay_(close_,len1),len1*5)) * corr_(close_,vol_,len1)*(corr_(sum_(close_,len1),sum_(close_,len1*4),len1))
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY46(self,name = 'alphaZS_YOY46',maxbacklength=31):
        '''
        近期与前期股价变动情况比较。
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  if_(2.5<close_+delay_(close_,20)-2*delay_(close_,10), -1.0, if_(0>close_+delay_(close_,20)-2*delay_(close_,10), 1.0, -1.0*delta_(close_,1)))
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY47(self,name = 'alphaZS_YOY47',len1=5,maxbacklength=16):
        '''
        成交量与价格变动
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  (1-close_)*vol_/mean_(vol_,len1).replace(0,np.nan) * (high_*(high_-close_)/mean_(high_,len1).replace(0,np.nan)) - (vwap_-delay_(vwap_,len1))
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY48(self,name = 'alphaZS_YOY48',len1=2,maxbacklength=11):
        '''
        
        '''
        pass
        #if maxbacklength==None:maxbacklength=len(self.close)
        # open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        # low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        # vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        # ret_=close_.pct_change().round(num_round)
        # #  
        #
        # alpha =  self.indn_(corr_(delta_(close_, 1), delta_(delay_(close_, 1), len1), 250), 'SecondIndustryCode') / sum_(np.power(delta_(close_, 1)/delay_(close_, 1), 2), 250).replace(0,np.nan)
        #------------output---------------------
        #return [name,alpha.round(num_round)]
    
    def alphaZS_YOY49(self,name = 'alphaZS_YOY49',len1=10,maxbacklength=31):
        '''
        与alphaZS_YOY46类似。
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  -1*(if_(-1>close_+delay_(close_,len1*2)-2*delay_(close_,len1), 1.0, -1.0*delta_(close_,1)))
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY50(self,name = 'alphaZS_YOY50',len1=5,maxbacklength=21):
        '''
        量价关系
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  -1*tsmax_((corr_((vol_), (vwap_), len1)), len1)
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY51(self,name = 'alphaZS_YOY51',maxbacklength=101):
        '''
        与alphaZS_YOY46、49类似
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  -1*(if_(-0.5>close_+delay_(close_,20)-2*delay_(close_,10), 1.0, -1.0*delta_(close_,1)))
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY52(self,name = 'alphaZS_YOY52',len1=10,maxbacklength=211):
        '''
        多指标结合
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  -1*delta_(tsmin_(low_, len1), 5)*(sum_(ret_, len1*20)-sum_(ret_,len1))*tsrank_(vol_,len1)
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY53(self,name = 'alphaZS_YOY53',len1=10,maxbacklength=11):
        '''
        股价波动变化
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  -1*delta_((2*close_-low_-high_)/(close_-low_).replace(0,np.nan), len1)
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY54(self,name = 'alphaZS_YOY54',len1=5,maxbacklength=1):
        '''
        ???
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  -1*(low_-close_)*np.power(open_/close_, len1) / (low_-high_).replace(0,np.nan) 
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY55(self,name = 'alphaZS_YOY55',len1=15,maxbacklength=401):
        '''
        价格变化与量能关系
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  -1*corr_(((close_-tsmin_(low_,len1*2))/(tsmax_(high_,len1*2)-tsmin_(low_,len1*2)).replace(0,np.nan)), (vol_), len1)
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY56(self,name = 'alphaZS_YOY56',len1=10,maxbacklength=11):
        pass
        '''
        包含市值指标
        '''

        # #------------output---------------------
        # return [name,alpha.round(num_round)]
    
    def alphaZS_YOY57(self,name = 'alphaZS_YOY57',len1=10,maxbacklength=31):
        '''
        股价突破，短期趋势
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  -1 * (close_-vwap_)/decaylinear_((tsargmax_(close_,len1*2)), 2).replace(0,np.nan)
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY58(self,name = 'alphaZS_YOY58',len1=4,maxbacklength=21):
        '''
        
        '''
        pass
        #if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  -1 * tsrank_(decaylinear_(corr_(self.indn_(vwap_, 'SectorCode'), vol_, len1), len1*2), len1)
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY59(self,name = 'alphaZS_YOY59',len1=10,maxbacklength=11):
        '''
        
        '''
        pass
        #  
        #
        # alpha =  -1*tsrank_(decaylinear_(corr_(self.indn_(vwap_, 'FirstIndustryCode'), vol_, len1), 16), 8)
        #------------output---------------------
        #return [name,alpha.round(num_round)]
    
    def alphaZS_YOY60(self,name = 'alphaZS_YOY60',len1=10,maxbacklength=21):
        '''
        量能变化与股价波动
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  -1 * (2*scale_(((2*close_-low_-high_)/(high_-low_).replace(0,np.nan)*vol_)) - scale_((tsargmax_(close_,len1))))
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY61(self,name = 'alphaZS_YOY61',len1=10,maxbacklength=211):
        '''
        量价关系
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  if_((vwap_ - tsmin_(vwap_,len1)) < (corr_(vwap_, mean_(vol_, len1*10), len1)), 1, -1)
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY62(self,name = 'alphaZS_YOY62',len1=10,maxbacklength=11):
        pass
        '''
        
        '''	  
        #------------output---------------------
    #    return [name,alpha.round(num_round)]
        
    def alphaZS_YOY63(self,name = 'alphaZS_YOY63',len1=10,maxbacklength=11):
        '''
        
        '''
        pass
        #------------output---------------------
        #return [name,alpha.round(num_round)]
    
    def alphaZS_YOY64(self,name = 'alphaZS_YOY64',len1=10,maxbacklength=101):
        '''
        价量关系
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  if_((corr_(sum_(open_*0.18+low_*0.82, len1), sum_(mean_(vol_,len1*5), len1), len1))<(delta_((high_+low_)/2*0.18+vwap_*0.82, 4)), -1, 1)
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY65(self,name = 'alphaZS_YOY65',len1=10,maxbacklength=101):
        '''
        与alphaZS_YOY64类似
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  if_((corr_(open_*0.01+vwap_*0.99, sum_(mean_(vol_,len1*5),len1), len1)) < (open_-tsmin_(open_,len1)), -1, 1)
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY66(self,name = 'alphaZS_YOY66',len1=7,maxbacklength=51):
        '''
        ???
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  -1* ((decaylinear_(delta_(vwap_,4), len1)) + tsrank_(decaylinear_((low_-vwap_)/(open_-(high_+low_)/2).replace(0,np.nan), len1*2), len1))
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY67(self,name = 'alphaZS_YOY67',len1=10,maxbacklength=11):
        pass
        # #------------output---------------------
        # return [name,alpha.round(num_round)]
    
    def alphaZS_YOY68(self,name = 'alphaZS_YOY68',len1=7,maxbacklength=101):
        '''
        
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  if_(tsrank_(corr_((high_), (mean_(vol_,len1*2)), len1),len1*2)<(delta_(close_*0.52+low_*0.48, 1)), -1, 1)
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY69(self,name = 'alphaZS_YOY69',len1=10,maxbacklength=11):
        '''
        
        '''
        pass
        #------------output---------------------
        #return [name,alpha.round(num_round)]
    
    def alphaZS_YOY70(self,name = 'alphaZS_YOY70',len1=15,maxbacklength=61):
        pass
    
    def alphaZS_YOY71(self,name = 'alphaZS_YOY71',len1=14,maxbacklength=None):
        '''
        ???
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  max_(tsrank_(decaylinear_(corr_(tsrank_(close_,len1), tsrank_(mean_(vol_,len1*5), len1*2), len1*2), len1), len1*4), \
                tsrank_(decaylinear_((np.power(low_+open_-2*vwap_, 2)), len1*4), len1))
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY72(self,name = 'alphaZS_YOY72',len1=14,maxbacklength=801):
        '''
        与alphaZS_YOY71类似
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  -1*((decaylinear_(corr_((high_+low_)/2, mean_(vol_,len1*4), len1*2), len1*2)) / (decaylinear_(corr_(tsrank_(vwap_,len1*2), tsrank_(vol_, len1*2), len1*2), len1)))
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY73(self,name = 'alphaZS_YOY73',len1=3,maxbacklength=51):
        '''
        与alphaZS_YOY71类似???
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  -1 * max_((decaylinear_(delta_(vwap_, 5), len1)), tsrank_(decaylinear_(-1*delta_(open_*0.15+low_*0.85, 2)/(open_*0.15+low_*0.85).replace(0,np.nan), len1), len1*5))
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY74(self,name = 'alphaZS_YOY74',len1=10,maxbacklength=61):
        '''
        ???
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  if_((corr_(close_, sum_(mean_(vol_,len1*3), len1*2), len1)) < (corr_((high_*0.03+vwap_*0.97), (vol_), len1)), -1, 1)
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY75(self,name = 'alphaZS_YOY75',len1=4,maxbacklength=121):
        '''
        与alphaZS_YOY74类似
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  if_((corr_(vwap_, vol_, len1)) < (corr_((low_), (mean_(vol_,len1*10)), len1*3)), 1, -1)
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY76(self,name = 'alphaZS_YOY76',len1=10,maxbacklength=11):
        pass
    
    def alphaZS_YOY77(self,name = 'alphaZS_YOY77',len1=4,maxbacklength=101):
        '''
        类似
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  -1*(min_((decaylinear_((high_+low_)/2 - vwap_, len1*5)), (decaylinear_(corr_((high_+low_)/2, mean_(vol_,len1*10), len1), len1*2))))
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY78(self,name = 'alphaZS_YOY78',len1=7,maxbacklength=51):
        pass
        '''
        ????
        '''
        # if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  np.power((corr_(sum_(low_*0.35+vwap_*0.65, len1*3), sum_(mean_(vol_, len1*5), len1*3), len1)), (corr_((vwap_), (vol_), len1)))
        # #------------output---------------------
        # return [name,alpha.round(num_round)]
    
    def alphaZS_YOY79(self,name = 'alphaZS_YOY79',len1=10,maxbacklength=11):
        '''
    
        '''
        pass

    
    def alphaZS_YOY80(self,name = 'alphaZS_YOY80',len1=10,maxbacklength=11):
        '''
    
        '''
        pass

    
    def alphaZS_YOY81(self,name = 'alphaZS_YOY81',len1=4,maxbacklength=121):
        '''
        
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  if_((log_(prod_((np.power((corr_(vwap_, sum_(mean_(vol_,len1*2), len1*10), len1*2)), len1)), len1*4))) < (corr_((vwap_), (vol_), len1)), -1, 1)
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY82(self,name = 'alphaZS_YOY82',len1=10,maxbacklength=11):
        '''
    
        '''
        pass
    
    def alphaZS_YOY83(self,name = 'alphaZS_YOY83',len1=5,maxbacklength=11):
        '''
    
        '''
        pass
        #if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  (delay_((high_-low_)/mean_(close_,len1), 2)) * ((vol_)) / (high_-low_).replace(0,np.nan) * mean_(close_, len1) * (vwap_ - close_)
        #------------output---------------------
        #return [name,alpha.round(num_round)]
    
    def alphaZS_YOY84(self,name = 'alphaZS_YOY84',len1=5,maxbacklength=31):
        '''
    
        '''
        # if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  np.power(tsrank_(vwap_ - tsmax_(vwap_, len1), len1*2), delta_(close_, len1))
        # #------------output---------------------
        # return [name,alpha.round(num_round)]
    
    def alphaZS_YOY85(self,name = 'alphaZS_YOY85',len1=4,maxbacklength=41):
        '''
    
        '''
        # if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  np.power((corr_(high_*0.88 + close_*0.12, mean_(vol_, len1*6), len1*2)), (corr_(tsrank_((high_+low_)/2, len1), tsrank_(vol_,len1*3),len1*2)))
        # #------------output---------------------
        # return [name,alpha.round(num_round)]
    
    def alphaZS_YOY86(self,name = 'alphaZS_YOY86',len1=5,maxbacklength=51):
        '''
    
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  if_(tsrank_(corr_(close_, sum_(mean_(vol_,len1*4), len1*2), len1), len1*3) < (close_ - vwap_), -1, 1)
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY87(self,name = 'alphaZS_YOY87',len1=10,maxbacklength=11):
        '''
    
        '''
        pass

    
    def alphaZS_YOY88(self,name = 'alphaZS_YOY88',len1=10,maxbacklength=11):
        '''
        
        '''
        # if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  (decaylinear_((open_)+(low_)-(high_)-(close_),len1))
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY89(self,name = 'alphaZS_YOY89',len1=10,maxbacklength=11):
        '''
    
        '''
        pass

    
    def alphaZS_YOY90(self,name = 'alphaZS_YOY90',len1=10,maxbacklength=11):
        '''
    
        '''
        pass

    
    def alphaZS_YOY91(self,name = 'alphaZS_YOY91',len1=10,maxbacklength=11):
        '''
    
        '''
        pass

    
    def alphaZS_YOY92(self,name = 'alphaZS_YOY92',len1=6,maxbacklength=61):
        '''
    
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  min_(tsrank_(decaylinear_(if_((high_+low_)/2+close_ < low_+open_, 1, -1), len1*2), len1*3), \
            tsrank_(decaylinear_(corr_((low_), (mean_(vol_,len1*4)), len1), len1), len1))
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY93(self,name = 'alphaZS_YOY93',len1=10,maxbacklength=11):
        '''
    
        '''
        pass

    
    def alphaZS_YOY94(self,name = 'alphaZS_YOY94',len1=10,maxbacklength=101):
        '''
    
        '''
        # if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  -1 * np.power((vwap_-tsmin_(vwap_,len1)), tsrank_(corr_(tsrank_(vwap_, len1*2), tsrank_(mean_(vol_,len1*6), 4), len1*2), 3))
        # #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY95(self,name = 'alphaZS_YOY95',len1=10,maxbacklength=201):
        '''
        
        '''
        # if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  if_((open_ - tsmin_(open_, len1)) < tsrank_((np.power(corr_(sum_((high_+low_)/2, len1*2), sum_(mean_(vol_, len1*4), len1*2), len1), 5)), 12), 1, -1)
        # #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY96(self,name = 'alphaZS_YOY96',len1=4,maxbacklength=None):
        '''
    
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  -1 * max_(tsrank_(decaylinear_(corr_((vwap_), (vol_), len1), len1), len1*2),\
                tsrank_(decaylinear_(tsargmax_(corr_(tsrank_(close_, len1*2), tsrank_(mean_(vol_,len1*5), len1), len1), len1*3), len1*3), len1*3))
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY97(self,name = 'alphaZS_YOY97',len1=10,maxbacklength=11):
        '''
    
        '''
        pass

    
    def alphaZS_YOY98(self,name = 'alphaZS_YOY98',len1=5,maxbacklength=201):
        '''
    
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  (decaylinear_(corr_(vwap_, sum_(mean_(vol_,len1), len1*5), len1), len1+2)) - \
                (decaylinear_(tsrank_(tsargmin_(corr_((open_), (mean_(vol_,len1*3)), len1*4), len1*2), len1+2), len1+3))
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY99(self,name = 'alphaZS_YOY99',len1=6,maxbacklength=101):
        pass
        '''
    
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  if_((corr_(sum_((high_+low_)/2, len1*3), sum_(mean_(vol_,len1*10), len1*3), len1+3)) < (corr_(low_, vol_, len1)), -1, 1)
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
    def alphaZS_YOY100(self,name = 'alphaZS_YOY100',len1=10,maxbacklength=11):
        '''
    
        '''
        pass

    
    def alphaZS_YOY101(self,name = 'alphaZS_YOY101',maxbacklength=1):
        '''
        实体线/振幅
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        #
        alpha =  (close_ - open_) / (high_ - low_).replace(0,np.nan)
        #------------output---------------------
        return [name,alpha.round(num_round)]
    
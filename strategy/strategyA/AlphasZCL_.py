# -*- coding: utf-8 -*-
"""
Created on Thu Nov 11 11:13:48 2021

注意一下几个因子，实盘结果差异
cumsum:10,16,17,18,19,20；10，18,34计算太慢，注释
16,19,34,replace(np.nan,0)
kalman:34

@author: zhouchenglin
"""

from apitool import *
import pandas as pd
import numpy as np
import time

class AlphasZCL_(object):
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
        self.empty=lambda n:oldempty_(n,open_)
        
    # def alphaZ_1(self,name = 'alphaZ_1',len1=60,maxbacklength=61):
    #     alpha = (self.close - mean_(self.close,len1))/self.close
    #     return [name,alpha.round(num_round)]
    # 对所有分母的0值做个替换.replace(0,np.nan);a/b.replace(0,np.nan)
    # def alphaZS_Bef1(self,name = 'alphaZS_Bef1',len1=60,maxbacklength=61):
    #     if maxbacklength==None:maxbacklength=len(self.close)
    #     open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
    #     low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
    #     vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
    #     #
    #     alpha = std_(amount_, len1)
    #     return [name,alpha.round(num_round)]
    
    def alphaZ_1(self,name = 'alphaZ_1',opt1=12,opt2=26,opt3=9,maxbacklength=None):
        # Indicator Seasons, Elder’s Concept,Indicator Seasons, Colby’s Variation,macd
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        ema1=close_.ewm(span=opt1).mean() #快线
        ema2=close_.ewm(span=opt2).mean() #慢线
        dif=ema1-ema2
        dea=dif.ewm(span=opt3).mean()
        a3=dif-dea#macdh
        fa=pd.DataFrame()
        fa=a3*0
        fa[( a3>0)*( a3>a3.shift(1))]=1

        fa[(a3<0)*( a3<a3.shift(1))]=-1
        # f=( a3>0)*( a3>a3.shift(1)-(a3<0)*( a3<a3.shift(1))  
        return [name,fa.round(num_round)]
    
    def alphaZ_2(self,name = 'alphaZ_2',opt1=12,len1=60,maxbacklength=None):
        # Inertia indicator
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 
        
        S=std_(close_,len1)#10日偏差
        dp=close_.diff(1)
        dp01=dp>=0
        U=S*dp01
        a1=U.ewm(span=opt1).mean() #
        a2=S.ewm(span=opt1).mean() #
        
        rsv=100*a1/a2.replace(0,np.nan)
        
        fa2=rsv.rolling(opt1).mean() #LR平滑，这里先用移动平均
        fa=(fa2>50)*1-1*(fa2<50)

        return [name,fa.round(num_round)]
    
    def alphaZ_3(self,name = 'alphaZ_3',opt1=5,opt2=12,maxbacklength=20):
        # Line Oscillator
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]
        
        lo=close_.rolling(opt1).mean()-close_.rolling(opt2).mean()
        return [name,lo.round(num_round)]
    
    def alphaZ_4(self,name = 'alphaZ_4',maxbacklength=20):
        # Price Volume Rank
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]
        
        dp=close_.diff()
        dv=vol_.diff()
        pvr=(dp>=0) * (dv>=0)*1+(dp>=0) * (dv<0)*2+(dp<0) * (dv>=0)*4+(dp<0) * (dv<0)*3
        return [name,pvr.round(num_round)]
    
    # def alphaZ_5(self,name = 'alphaZ_5',maxbacklength=20):
    #     # Pivot Points
    #     if maxbacklength==None:maxbacklength=len(self.close)
    #     open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
    #     low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
    #     vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]
        
    #     pp=(high_+low_+close_)/3
    #     s1=pp*2-high_
    #     r1=pp*2-low_
    #     s2=pp-(high_-low_)
    #     r2=pp+(high_-low_)
    #     return [name,pp.round(num_round),s1.round(num_round),r1.round(num_round),s2.round(num_round),r2.round(num_round)]
    def alphaZ_5_1(self,name = 'alphaZ_5_1',maxbacklength=20):
        # Pivot Points
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]
        
        pp=(high_+low_+close_)/3
        s1=pp*2-high_
        r1=pp*2-low_
        s2=pp-(high_-low_)
        r2=pp+(high_-low_)
        return [name,pp.round(num_round)]
    def alphaZ_5_2(self,name = 'alphaZ_5_2',maxbacklength=20):
        # Pivot Points
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]
        
        pp=(high_+low_+close_)/3
        s1=pp*2-high_
        r1=pp*2-low_
        s2=pp-(high_-low_)
        r2=pp+(high_-low_)
        return [name,s1.round(num_round)]
    def alphaZ_5_3(self,name = 'alphaZ_5_3',maxbacklength=20):
        # Pivot Points
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]
        
        pp=(high_+low_+close_)/3
        s1=pp*2-high_
        r1=pp*2-low_
        s2=pp-(high_-low_)
        r2=pp+(high_-low_)
        return [name,r1.round(num_round)]
    def alphaZ_5_4(self,name = 'alphaZ_5_4',maxbacklength=20):
        # Pivot Points
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]
        
        pp=(high_+low_+close_)/3
        s1=pp*2-high_
        r1=pp*2-low_
        s2=pp-(high_-low_)
        r2=pp+(high_-low_)
        return [name,s2.round(num_round)]
    def alphaZ_5_5(self,name = 'alphaZ_5_5',maxbacklength=20):
        # Pivot Points
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]
        
        pp=(high_+low_+close_)/3
        s1=pp*2-high_
        r1=pp*2-low_
        s2=pp-(high_-low_)
        r2=pp+(high_-low_)
        return [name,r2.round(num_round)]
    
    
    
    
    
    def alphaZ_6(self,name = 'alphaZ_6',opt1=12,opt2=26,opt3=9,maxbacklength=None):
        # macdh
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        ema1=close_.ewm(span=opt1).mean() #快线
        ema2=close_.ewm(span=opt2).mean() #慢线
        dif=ema1-ema2
        dea=dif.ewm(span=opt3).mean()
        macdh=dif-dea#macdh
        return [name,macdh.round(num_round)]
    def alphaZ_7(self,name = 'alphaZ_7',opt1=14,maxbacklength=20):
        # Intraday Momentum Index
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 
        
        up=close_-open_
        dw=open_-close_
        up=up*(up>0)
        dw=dw*(dw>0)
        up=up+up.shift(1)
        dw=dw+dw.shift(1)
        imi=up.rolling(opt1).sum()/(up.rolling(opt1).sum()+dw.rolling(opt1).sum()).replace(0,np.nan)
        imi=imi*100
        return [name,imi.round(num_round)]
    def alphaZ_7_2(self,name = 'alphaZ_7_2',opt1=14,maxbacklength=20):
        # Intraday Momentum Index -11
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]
        
        aa=AlphasZCL_(open_,high_,low_,close_,vol_,amount_,opt_,vwap_)
        fa=aa.alphaZ_7(name = 'alphaZ_7',maxbacklength=maxbacklength,opt1=opt1)
        imif=(fa[1]-50)/50
        return [name,imif.round(num_round)]
    def alphaZ_8(self,name = 'alphaZ_8',len1=14,maxbacklength=20):
        # RSI
        if maxbacklength==None:maxbacklength=len(self.close)
        # open_=self.open[-maxbacklength:];
        # high_=self.high[-maxbacklength:]
        # low_=self.low[-maxbacklength:];
        close_=self.close[-maxbacklength:]
        # vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 
        
        dp=close_.diff(1)
        dp01=dp>=0
        
        a1=dp*dp01
        a2=(dp-a1).abs()
        rs=a1.rolling(len1).mean()/a2.rolling(len1).mean().replace(0,np.nan)
        rsi=100*rs/(1+rs)
        return [name,rsi.round(num_round)]
    def alphaZ_8_2(self,name = 'alphaZ_8_2',len1=14,maxbacklength=20):
        # RSI---11
        if maxbacklength==None:maxbacklength=len(self.close)
        # open_=self.open[-maxbacklength:];
        # high_=self.high[-maxbacklength:]
        # low_=self.low[-maxbacklength:];
        close_=self.close[-maxbacklength:]
        # vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 
        
        dp=close_.diff(1)
        dp01=dp>=0
        
        a1=dp*dp01
        a2=(dp-a1).abs()
        rs=a1.rolling(len1).mean()/a2.rolling(len1).mean().replace(0,np.nan)
        rsi=(100*rs/(1+rs)-50)/50
        return [name,rsi.round(num_round)]
    def alphaZ_9(self,name = 'alphaZ_9',len1=10,opt1=14,maxbacklength=None):
        # RVI,
        '''
        RVIorig = 100*( EMA[W14] of U)/( EMA[W14] of S)
        RVI = (RVIorig of highs + RVIorig of lows)/2, where
        S = Stddev (10 days) - 为期10天的标准偏差;
        U = S, 如果目前的价格比前一时期的价格高;
        U = 0, 如果目前的价格比前一时期的价格低;
        EMA (w14) = 14天期间指数移动平均线;
        RVIorig of highs - 相对活力指数高点;
        RVIorig of low - 相对活力指数低点.
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 
        
        S=std_(close_,len1)#10日偏差
        dp=close_.diff(1)
        dp01=dp>=0
        U=S*dp01
        a1=U.ewm(span=opt1).mean() #
        a2=abs(S).ewm(span=opt1).mean() #
        
        rsv=100*a1/a2.replace(0,np.nan)
        return [name,rsv.round(num_round)]
    def alphaZ_9_2(self,name = 'alphaZ_9_2',len1=10,opt1=14,maxbacklength=None):
        # RVI,-11
        '''
        RVIorig = 100*( EMA[W14] of U)/( EMA[W14] of S)
        RVI = (RVIorig of highs + RVIorig of lows)/2, where
        S = Stddev (10 days) - 为期10天的标准偏差;
        U = S, 如果目前的价格比前一时期的价格高;
        U = 0, 如果目前的价格比前一时期的价格低;
        EMA (w14) = 14天期间指数移动平均线;
        RVIorig of highs - 相对活力指数高点;
        RVIorig of low - 相对活力指数低点.
        '''
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 
        
        S=std_(close_,len1)#10日偏差
        dp=close_.diff(1)
        dp01=dp>=0
        U=S*dp01
        a1=U.ewm(span=opt1).mean() #
        a2=abs(S).ewm(span=opt1).mean() #
        
        rsv=100*a1/a2.replace(0,np.nan)
        rsv=(rsv-50)/50
        return [name,rsv.round(num_round)]  
    # def alphaZ_10(self,name = 'alphaZ_10',opt1=55,opt2=34,maxbacklength=None):
    #     # Klinger  Volume Oscillator (KVO)
    #     if maxbacklength==None:maxbacklength=len(self.close)
    #     open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
    #     low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
    #     vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 
        
    #     def cumsum2(df):
    #         df2=df.abs()
    #         d01=(df>=0)*1-1*(df<0)
    #         rs=df*0
    #         for i in range(1,len(df)):
    #             rs.iloc[i]=df2.iloc[i]+df2.iloc[i-1]
    #             if i>1:
    #                 j=i-2
    #                 while d01.iloc[j]==d01.iloc[i]:
    #                     rs.iloc[i]=rs.iloc[i]+df2.iloc[j]
    #                     if j>2:j-=1
    #                     else: break
    #         return rs
    #     ftp=high_+low_+close_
    #     dm=high_-low_
    #     cm=dm*0
    #     dp=ftp.diff(1)
    #     dp01=(dp>=0)*1-1*(dp<0)
    #     # cm=dm.rolling(5).sum()
    #     cm=(dm*dp01).apply(cumsum2)
    #     # for i in range(cm.index[1],cm.index[0]+len(cm)):
    #     #     cm.iloc[i]=dm.iloc[i]+dm.iloc[i-1]
    #     #     if i-cm.index[0]>=2:
    #     #         j=i-2
    #     #         while dp01.iloc[j]==dp01.iloc[i]:
    #     #             cm.iloc[i]=cm.iloc[i]+dm.iloc[j]
    #     #             j-=1
    #     vf=(2*dm/cm.replace(0,np.nan)-1).abs()*vol_*dp01*100
    #     kvo=vf.ewm(span=opt2).mean()-vf.ewm(span=opt1).mean()
    #     return [name,kvo.round(num_round)]

    def alphaZ_11(self,name = 'alphaZ_11',maxbacklength=20):
        # market facilitation index
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 
        

        mfi=(high_-low_)/vol_

        return [name,mfi.round(num_round)]
    def alphaZ_12(self,name = 'alphaZ_12',opt1=9,opt2=3,maxbacklength=None):
        # mass index
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 
        

        m9=(high_-low_).ewm(span=opt1).mean()
        m99=m9.ewm(span=opt1).mean()
        mi=m9/m99.replace(0,np.nan)
        mi=mi.rolling(opt2).sum()

        return [name,mi.round(num_round)] 
    def alphaZ_13(self,name = 'alphaZ_13',maxbacklength=20):
        # median price
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 
        
        mp=(high_+low_)*0.5
        return [name,mp.round(num_round)] 
    def alphaZ_14(self,name = 'alphaZ_14',opt1=12,maxbacklength=20):
        # Momentum index
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 
        
        mi=close_/close_.shift(opt1).replace(0,np.nan)*100
        return [name,mi.round(num_round)] 
    def alphaZ_15(self,name = 'alphaZ_15',opt1=14,maxbacklength=20):
        # Money flow index
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 
        
        ftp=(close_+high_+low_)/3
        mf=ftp*vol_
        dp=ftp.diff(1)
        dp01=dp>=0
        
        a1=mf*dp01
        a2=(mf-a1)
        rs=a1.rolling(opt1).mean()/a2.rolling(opt1).mean().replace(0,np.nan)
        mfi=100*rs/(1+rs)
        return [name,mfi.round(num_round)] 
    def alphaZ_15_2(self,name = 'alphaZ_15_2',opt1=14,maxbacklength=20):
        # Money flow index -11
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 
        
        ftp=(close_+high_+low_)/3
        mf=ftp*vol_
        dp=ftp.diff(1)
        dp01=dp>=0
        
        a1=mf*dp01
        a2=(mf-a1)
        rs=a1.rolling(opt1).mean()/a2.rolling(opt1).mean().replace(0,np.nan)
        mfi=100*rs/(1+rs)
        mfi=(mfi-50)/50
        return [name,mfi.round(num_round)] 
    def alphaZ_16(self,name = 'alphaZ_16',maxbacklength=None):
        # negative volume index,矩阵计算有问题
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 
        
        nvi=close_*0
        nvi.iloc[0]=1000
        temp=(close_-close_.shift(1))/close_.shift(1).replace(0,np.nan)#涨幅
        dv=vol_.diff(1) #成交量变化
        dv01=dv<0 #小于0
        for i  in range(1,len(nvi)):
            nvi.iloc[i]=(nvi.iloc[i-1]*(~dv01.iloc[i])+nvi.iloc[i-1]*((1-temp.iloc[i]).replace(np.nan,0))*(dv01.iloc[i]))

        return [name,nvi.round(num_round)] 
    # def alphaZ_16_v2(self,name = 'alphaZ_16_v2',maxbacklength=201,opt1=14):
    #     # negative volume index,矩阵计算有问题
    #     if maxbacklength==None:maxbacklength=len(self.close)
    #     open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
    #     low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
    #     vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 
        
    #     nvi=close_*0
    #     nvi.iloc[0]=1000
    #     temp=(close_-close_.shift(1))/close_.shift(1).replace(0,np.nan)#涨幅
    #     dv=vol_.diff(1) #成交量变化
    #     dv01=dv<0 #小于0

    #     nvi=nvi.apply(lambda x,y,z:x*y+x*(1-z)*(~y),nvi.shift(1),dv01,temp)
    #                   # nvi.iloc[i-1]*dv01.iloc[i]+nvi.iloc[i-1]*(1-temp.iloc[i])*(~dv01.iloc[i]))

    #     return [name,nvi.round(num_round)] 

    def alphaZ_17(self,name = 'alphaZ_17',maxbacklength=None):
        # OBV
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 

        dp=close_.diff(1)
        # dp01=(dp>0)*1+(dp==0)*0-(dp<0)*1
        dp010=np.sign(dp)
        obv=close_*0
        obv=(vol_*dp010).cumsum()
        return [name,obv.round(num_round)]
    # def alphaZ_18(self,name = 'alphaZ_18',af=2,maxbacklength=18):
    #     # Parabolic Time/Price System,SAR
    #     if maxbacklength==None:maxbacklength=len(self.close)
    #     open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
    #     low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
    #     vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 
        
    #     af=af/100;
    #     af=min(af,1)
    #     afmax=min(af*10,1)
    #     def func18(close_,high_,low_,af,afmax):
    #         import random
    #         dp=close_.diff(1)
    #         dp010=(dp>=0)*1-(dp<0)*1
    #         position=close_*0
    #         position.iloc[0]=random.choice([1, -1])#初始头寸方向可以手动指定dp010.iloc[0]
    #         entrybar=0
    #         sar=close_*0
    #         ehl=close_*0
    #         psar=close_*0
    #         sar.iloc[0]=high_.iloc[0]*(position.iloc[0]==1)+low_.iloc[0]*(position.iloc[0]==-1)
    #         ehl.iloc[0]=sar.iloc[0]
    #         af0=af
    #         for i in range(1,len(dp)):
                
    #             if position.iloc[i-1]==1:
    #                 if low_.iloc[i]<sar.iloc[i-1]: 
    #                     position.iloc[i]=-1*position.iloc[i-1]
    #                     entrybar=i
    #                     af0=af
    #                     ehl.iloc[i]=low_.iloc[i]
    #                     psar.iloc[i]=ehl.iloc[i-1]
    #                     sar.iloc[i]=(ehl.iloc[i]-psar.iloc[i])*af0+psar.iloc[i]
    #                 if low_.iloc[i]>=sar.iloc[i-1]:
    #                     # af1=af*(i-entrybar+1)
    #                     af1=af0
    #                     af1=min(af1,afmax)
    #                     position.iloc[i]=position.iloc[i-1]
    #                     # entrybar=i
    #                     ehl.iloc[i]=high_[entrybar:i+1].max()
    #                     if ehl.iloc[i]>ehl.iloc[i-1]:
    #                         af0=af0+af
    #                         af1=min(af0,afmax)
    #                     psar.iloc[i]=sar.iloc[i-1]
    #                     sar.iloc[i]=(ehl.iloc[i]-psar.iloc[i])*af1+psar.iloc[i]
    #             if position.iloc[i-1]==-1:
    #                 if high_.iloc[i]>sar.iloc[i-1]: 
    #                     position.iloc[i]=-1*position.iloc[i-1]
    #                     entrybar=i
    #                     af0=af
    #                     ehl.iloc[i]=high_.iloc[i]
    #                     psar.iloc[i]=ehl.iloc[i-1]
    #                     sar.iloc[i]=(ehl.iloc[i]-psar.iloc[i])*af0+psar.iloc[i]
    #                 if high_.iloc[i]<=sar.iloc[i-1]:
    #                     # af1=af*(i-entrybar+1)
    #                     af1=af0
    #                     af1=min(af1,afmax)
    #                     position.iloc[i]=position.iloc[i-1]
    #                     # entrybar=i
    #                     ehl.iloc[i]=low_[entrybar:i+1].min()
    #                     if ehl.iloc[i]<ehl.iloc[i-1]:
    #                         af0=af0+af
    #                         af1=min(af0,afmax)
    #                     psar.iloc[i]=sar.iloc[i-1]
    #                     sar.iloc[i]=(ehl.iloc[i]-psar.iloc[i])*af1+psar.iloc[i]
    #         return [sar,position]
    #     sar=close_*0
    #     position=close_*0
    #     for i in close_.columns:
    #         a=func18(close_[i], high_[i], low_[i], af, afmax)#AlphasZCL_.func18
    #         sar[i]=a[0]
    #         position[i]=a[1]
    #     return [name,sar.round(num_round)]
        
    def alphaZ_19(self,name = 'alphaZ_19',maxbacklength=None):
        # positive volume index
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 
        
        pvi=close_*0
        pvi.iloc[0]=1000
        temp=(close_-close_.shift(1))/close_.shift(1).replace(0,np.nan)#涨幅
        dv=vol_.diff(1) #成交量变化
        dv01=dv>0 #小于0
        for i  in range(1,len(pvi)):
            pvi.iloc[i]=(pvi.iloc[i-1]*(~dv01.iloc[i])+pvi.iloc[i-1]*((1+temp.iloc[i]).replace(np.nan,0))*(dv01.iloc[i]))

        return [name,pvi.round(num_round)] 
    def alphaZ_20(self,name = 'alphaZ_20',maxbacklength=None):
        # PVT
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 

        dp=close_.diff(1)/close_.shift(1).replace(0,np.nan)
        # dp01=(dp>0)*1+(dp==0)*0-(dp<0)*1
        # dp010=np.sign(dp)
        pvt=close_*0
        pvt=(vol_*dp).cumsum()
        return [name,pvt.round(num_round)] 
    # def alphaZ_21(self,name = 'alphaZ_21',opt1=14,maxbacklength=20):
    #     # Price channel,双输出
    #     if maxbacklength==None:maxbacklength=len(self.close)
    #     open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
    #     low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
    #     vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 

    #     HL=high_.shift().rolling(opt1).max()# excluding today
    #     LL=low_.shift().rolling(opt1).min()
    #     return [name,HL.round(num_round),LL.round(num_round)] 
    def alphaZ_21_1(self,name = 'alphaZ_21_1',opt1=14,maxbacklength=20):
        # Price channel,双输出
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 

        HL=high_.shift().rolling(opt1).max()# excluding today
        LL=low_.shift().rolling(opt1).min()
        return [name,HL.round(num_round)] 
    def alphaZ_21_2(self,name = 'alphaZ_21_2',opt1=14,maxbacklength=20):
        # Price channel,双输出
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 

        HL=high_.shift().rolling(opt1).max()# excluding today
        LL=low_.shift().rolling(opt1).min()
        return [name,LL.round(num_round)] 
    def alphaZ_22(self,name = 'alphaZ_22',opt1=12,opt2=26,maxbacklength=None):
        # Price Osillator
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 

        ma1=close_.ewm(span=opt1).mean() #快线
        ma2=close_.ewm(span=opt2).mean() #慢线
        osi=(ma1-ma2)/ma2*100
        return [name,osi.round(num_round)] 
    def alphaZ_23(self,name = 'alphaZ_23',opt1=12,maxbacklength=20):
        # Price Ratio-Of-Change
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 

        roc=(close_-close_.shift(opt1))/close_.shift(opt1).replace(0,np.nan)*100
        return [name,roc.round(num_round)] 
    # def alphaZ_24(self,name ='alphaZ_24',opt1=14,maxbacklength=20):
    #     # Projection Bands
    #     if maxbacklength==None:maxbacklength=len(self.close)
    #     open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
    #     low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
    #     vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 
    #     hslop=high_.rolling(opt1).apply(lambda x: np.polyfit(range(len(x)), x, 1)[0])
    #     lslop=low_.rolling(opt1).apply(lambda x: np.polyfit(range(len(x)), x, 1)[0])
        
    #     up=close_*np.nan
    #     dw=close_*np.nan
    #     k=range(-opt1+1,1)
    #     k=pd.DataFrame(k)
    #     k=-k
    #     names = close_.columns
    #     kk=pd.DataFrame()
    #     for i in names:
    #         kk[i] = k.iloc[:,0]
        
    #     for i in range(opt1,len(close_)):
    #         Cup=high_[i-opt1+1:i+1].reset_index(drop=True)+hslop.iloc[i]*kk
    #         up.iloc[i]=Cup.max()
    #         Cdw=low_[i-opt1+1:i+1].reset_index(drop=True)+lslop.iloc[i]*kk
    #         dw.iloc[i]=Cdw.min()
    #     return [name,up.round(num_round),dw.round(num_round)] 
    
    def alphaZ_24_1(self,name ='alphaZ_24_1',opt1=14,maxbacklength=20):
        # Projection Bands
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 
        hslop=high_.rolling(opt1).apply(lambda x: np.polyfit(range(len(x)), x, 1)[0])
        lslop=low_.rolling(opt1).apply(lambda x: np.polyfit(range(len(x)), x, 1)[0])
        
        up=close_*np.nan
        dw=close_*np.nan
        k=range(-opt1+1,1)
        k=pd.DataFrame(k)
        k=-k
        names = close_.columns
        kk=pd.DataFrame()
        for i in names:
            kk[i] = k.iloc[:,0]
        
        for i in range(opt1,len(close_)):
            Cup=high_[i-opt1+1:i+1].reset_index(drop=True)+hslop.iloc[i]*kk
            up.iloc[i]=Cup.max()
            Cdw=low_[i-opt1+1:i+1].reset_index(drop=True)+lslop.iloc[i]*kk
            dw.iloc[i]=Cdw.min()
        return [name,up.round(num_round)] 
    def alphaZ_24_2(self,name ='alphaZ_24_2',opt1=14,maxbacklength=20):
        # Projection Bands
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 
        hslop=high_.rolling(opt1).apply(lambda x: np.polyfit(range(len(x)), x, 1)[0])
        lslop=low_.rolling(opt1).apply(lambda x: np.polyfit(range(len(x)), x, 1)[0])
        
        up=close_*np.nan
        dw=close_*np.nan
        k=range(-opt1+1,1)
        k=pd.DataFrame(k)
        k=-k
        names = close_.columns
        kk=pd.DataFrame()
        for i in names:
            kk[i] = k.iloc[:,0]
        
        for i in range(opt1,len(close_)):
            Cup=high_[i-opt1+1:i+1].reset_index(drop=True)+hslop.iloc[i]*kk
            up.iloc[i]=Cup.max()
            Cdw=low_[i-opt1+1:i+1].reset_index(drop=True)+lslop.iloc[i]*kk
            dw.iloc[i]=Cdw.min()
        return [name,dw.round(num_round)] 
    
    def alphaZ_25(self,name ='alphaZ_25',opt1=14,maxbacklength=20):
        # Projection Osillation
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 
        hslop=high_.rolling(opt1).apply(lambda x: np.polyfit(range(len(x)), x, 1)[0])
        lslop=low_.rolling(opt1).apply(lambda x: np.polyfit(range(len(x)), x, 1)[0])
        
        up=close_*np.nan
        dw=close_*np.nan
        k=range(-opt1+1,1)
        k=pd.DataFrame(k)
        k=-k
        names = close_.columns
        kk=pd.DataFrame()
        for i in names:
            kk[i] = k.iloc[:,0]
        
        for i in range(opt1,len(close_)):
            Cup=high_[i-opt1+1:i+1].reset_index(drop=True)+hslop.iloc[i]*kk
            up.iloc[i]=Cup.max()
            Cdw=low_[i-opt1+1:i+1].reset_index(drop=True)+lslop.iloc[i]*kk
            dw.iloc[i]=Cdw.min()
        POsi=(close_-dw)/(up-dw)*100#0~100
        return [name,POsi.round(num_round)] 
    def alphaZ_25_2(self,name ='alphaZ_25_2',opt1=14,maxbacklength=20):
        # Projection Osillation -11
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 
        hslop=high_.rolling(opt1).apply(lambda x: np.polyfit(range(len(x)), x, 1)[0])
        lslop=low_.rolling(opt1).apply(lambda x: np.polyfit(range(len(x)), x, 1)[0])
        
        up=close_*np.nan
        dw=close_*np.nan
        k=range(-opt1+1,1)
        k=pd.DataFrame(k)
        k=-k
        names = close_.columns
        kk=pd.DataFrame()
        for i in names:
            kk[i] = k.iloc[:,0]
        
        for i in range(opt1,len(close_)):
            Cup=high_[i-opt1+1:i+1].reset_index(drop=True)+hslop.iloc[i]*kk
            up.iloc[i]=Cup.max()
            Cdw=low_[i-opt1+1:i+1].reset_index(drop=True)+lslop.iloc[i]*kk
            dw.iloc[i]=Cdw.min()
        POsi=(close_-dw)/(up-dw)*100#0~100
        POsi=(POsi-50)/50
        return [name,POsi.round(num_round)] 
    def alphaZ_26(self,name ='alphaZ_26',periods=10, smoothing=5,maxbacklength=None):
        # Polarized Fractal Efficiency (PFE)
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 
        
        N=periods;M=smoothing
        
        p1=(close_-close_.shift(N))**2+N**2
        p2=sqrt_(p1)
        a=close_-close_.shift(1)
        aa=sqrt_(a**2+1)
        p3=aa.rolling(N).sum()
        p=1*p2/p3
        p=p*(close_.diff()>=0)-p*(close_.diff()<0)
        pfe=p.ewm(span=M).mean()

        return [name,pfe.round(num_round)] 
    def alphaZ_27(self,name ='alphaZ_27',opt1=14,maxbacklength=20):
        # Linear Regression Slope
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 
        
        slop=close_.rolling(opt1).apply(lambda x: np.polyfit(range(len(x)), x, 1)[0])
        return [name,slop.round(num_round)] 
    def alphaZ_28(self,name ='alphaZ_28',opt1=14,maxbacklength=20):
        # Linear Regression intercept
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 
        
        intercept=close_.rolling(opt1).apply(lambda x: np.polyfit(range(len(x)), x, 1)[1])
        return [name,intercept.round(num_round)] 
      
    def alphaZ_29(self,name ='alphaZ_29',opt1=14,maxbacklength=20):
        # Linear Regression angle
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 
        
        slop=close_.rolling(opt1).apply(lambda x: np.polyfit(range(len(x)), x, 1)[0])
        angle = np.arctan(slop)
        return [name,angle.round(num_round)] 
    def alphaZ_29_2(self,name ='alphaZ_29_2',opt1=14,maxbacklength=20):
        # Linear Regression angle -11
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 
        
        slop=close_.rolling(opt1).apply(lambda x: np.polyfit(range(len(x)), x, 1)[0])
        angle = np.arctan(slop)
        angle =(angle)/np.pi*2
        return [name,angle.round(num_round)] 
    def alphaZ_30(self,name ='alphaZ_30',opt1=14,maxbacklength=20):
        # Linear Regression 
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 
        
        slop=close_.rolling(opt1).apply(lambda x: np.polyfit(range(len(x)), x, 1)[0])
        intercept=close_.rolling(opt1).apply(lambda x: np.polyfit(range(len(x)), x, 1)[1])
        lr=slop*(opt1-1)+intercept
        return [name,lr.round(num_round)] 
    def alphaZ_31(self,name ='alphaZ_31',opt1=14,opt2=1,maxbacklength=20):
        # Linear Regression forecast
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 
        
        slop=close_.rolling(opt1).apply(lambda x: np.polyfit(range(len(x)), x, 1)[0])
        intercept=close_.rolling(opt1).apply(lambda x: np.polyfit(range(len(x)), x, 1)[1])
        lrf=slop*(opt1+opt2-1)+intercept
        return [name,lrf.round(num_round)] 

    # def alphaZ_32(self,name ='alphaZ_32',opt1=20,opt2=10,M=2,maxbacklength=21):
    #     #  Keltner Channel
    #     if maxbacklength==None:maxbacklength=len(self.close)
    #     open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
    #     low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
    #     vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 
        
    #     kcm=close_.ewm(span=opt1).mean()
    #     TR=max_(high_,close_.shift())-min_(low_,close_.shift())
    #     ATR=TR.rolling(opt2).mean()
    #     up=kcm+M*ATR
    #     dw=kcm-M*ATR
    #     return [name,up.round(num_round),dw.round(num_round)] 
    def alphaZ_32_1(self,name ='alphaZ_32_1',opt1=20,opt2=10,M=2,maxbacklength=None):
        #  Keltner Channel
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 
        
        kcm=close_.ewm(span=opt1).mean()
        TR=max_(high_,close_.shift())-min_(low_,close_.shift())
        ATR=TR.rolling(opt2).mean()
        up=kcm+M*ATR
        dw=kcm-M*ATR
        return [name,up.round(num_round)]
    def alphaZ_32_2(self,name ='alphaZ_32_2',opt1=20,opt2=10,M=2,maxbacklength=None):
        #  Keltner Channel
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 
        
        kcm=close_.ewm(span=opt1).mean()
        TR=max_(high_,close_.shift())-min_(low_,close_.shift())
        ATR=TR.rolling(opt2).mean()
        up=kcm+M*ATR
        dw=kcm-M*ATR
        return [name,dw.round(num_round)]    
    # def alphaZ_33(self,name ='alphaZ_33',opt1=30,opt2=20,M=1,maxbacklength=31):
    #     #  Kirshenbaum Bands
    #     if maxbacklength==None:maxbacklength=len(self.close)
    #     open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
    #     low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
    #     vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 
        
    #     def func33(df):
    #         coefs, residual, _, _, _ = np.polyfit(range(len(df)),df, 1, full=True)
    #         stderr=residual/len(df)
    #         stderr=np.sqrt(stderr)
    #         return stderr
    #     ema=close_.ewm(span=opt1).mean()
    #     std=close_.rolling(opt2).apply(func33)
    #     up=ema+M*std
    #     dw=ema-M*std
    #     return [name,up.round(num_round),dw.round(num_round)]
    def alphaZ_33_1(self,name ='alphaZ_33_1',opt1=30,opt2=20,M=1,maxbacklength=None):
        #  Kirshenbaum Bands
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 
        
        def func33(df):
            coefs, residual, _, _, _ = np.polyfit(range(len(df)),df, 1, full=True)
            stderr=residual/len(df)
            stderr=np.sqrt(stderr)
            return stderr
        ema=close_.ewm(span=opt1).mean()
        std=close_.rolling(opt2).apply(func33)
        up=ema+M*std
        dw=ema-M*std
        return [name,up.round(num_round)]
    def alphaZ_33_2(self,name ='alphaZ_33_2',opt1=30,opt2=20,M=1,maxbacklength=None):
        #  Kirshenbaum Bands
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 
        
        def func33(df):
            coefs, residual, _, _, _ = np.polyfit(range(len(df)),df, 1, full=True)
            stderr=residual/len(df)
            stderr=np.sqrt(stderr)
            return stderr
        ema=close_.ewm(span=opt1).mean()
        std=close_.rolling(opt2).apply(func33)
        up=ema+M*std
        dw=ema-M*std
        return [name,dw.round(num_round)]
    # def alphaZ_34(self,name ='alphaZ_34',opt1=10,maxbacklength=None):
    #     #  Kalman filter
    #     if maxbacklength==None:maxbacklength=len(self.close)
    #     open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
    #     low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
    #     vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:] 
        
    #     std_=close_.rolling(opt1).std()
    #     std=std_.mean()
        
    #     from pykalman import KalmanFilter
    #     def Kalman1D(observations,observation_covariance=1,transition_covariance=0.1,transition_matrix = 1):
    #         # To return the smoothed time series data
    #         # observation_covariance=1，观测偏差
    #         # transition_covariance=0.1,预测偏差
    #         # transition_matrix = 1,向前依赖系数
    #         initial_value_guess = observations.iloc[0]
    #         # initial_value_guess
    #         kf = KalmanFilter(
    #                 initial_state_mean=initial_value_guess,#正态分布均值
    #                 initial_state_covariance=observation_covariance,#正太方差，正太随机确定初值
    #                 observation_covariance=observation_covariance,
    #                 transition_covariance=transition_covariance,
    #                 transition_matrices=transition_matrix
    #             )
    #         pred_state, state_cov = kf.smooth(observations.replace(np.nan,0))
    #         return pred_state
    #     kalf=close_*0
        
    #     for i in close_.columns:
    #         observation_covariance=std[i]
    #         transition_covariance=std[i]
    #         transition_matrix=1
    #         kalf[i]=Kalman1D(close_[i].replace(np.nan,0),observation_covariance,transition_covariance,transition_matrix)

    #     return [name,kalf.round(num_round)]



    
if __name__ == '__main__':
    pass
''' 
1 替换output为return
2 替换n ame为self,n ame
3 替换所有的DF_变量为self.DF_
4 初始化emtpy，ind函数
'''

from apitool import *
import pandas as pd
import numpy as np
class AlphasZS_FH(object):
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
    def alphaZS_FH1(self,name = 'alphaZS_FH1',len1=100,maxbacklength=102):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        #
        alpha = 100*(log_(tsmax_(high_, len1)) - log_(tsmin_(low_, len1))) / sum_(abs_(log_(close_) - log_(delay_(close_, 1))), len1)
        return [name,alpha.round(num_round)]
    
    def alphaZS_FH2(self,name = 'alphaZS_FH2',maxbacklength=1):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        #
        alpha = (high_-close_)
        return [name,alpha.round(num_round)]
    
    def alphaZS_FH3(self,name = 'alphaZS_FH3',maxbacklength=1):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        #
        alpha = (close_-low_)
        return [name,alpha.round(num_round)]
    
    def alphaZS_FH4(self,name = 'alphaZS_FH4',maxbacklength=1):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        #
        alpha = (high_-max_(close_,open_))
        return [name,alpha.round(num_round)]  
    
    def alphaZS_FH5(self,name = 'alphaZS_FH5',maxbacklength=1):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        #
        alpha=(min_(close_,open_)-low_)
        return [name,alpha.round(num_round)]    
    def alphaZS_FH7(self,name = 'alphaZS_FH7',maxbacklength=None):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        #
        TR = max_(delay_(close_, 1), high_) - min_(delay_(close_, 1), low_)
        alpha = ema_(TR, 5) / ema_(TR, 10)
        return [name,alpha.round(num_round)]        
    def alphaZS_FH8(self,name = 'alphaZS_FH8',maxbacklength=3):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        #
        alpha = sign_(close_ - open_) * 4 + sign_(delay_(close_ - open_, 1)) * 3 + sign_(delay_(close_ - open_, 2))* 2 + sign_(delay_(close_ - open_, 4))
        return [name,alpha.round(num_round)]
    def alphaZS_FH9(self,name = 'alphaZS_FH9',len1=60,maxbacklength=61):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        #
        alpha = (close_ - mean_(close_,len1))
        return [name,alpha.round(num_round)]   
    def alphaZS_FH10(self,name = 'alphaZS_FH10',len1=10,maxbacklength=11):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        #
        alpha = (close_ - mean_(close_, len1))
        return [name,alpha.round(num_round)]
    def alphaZS_FH12(self,name = 'alphaZS_FH12',len1=20,maxbacklength=21):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        #
        alpha = (ema_(close_, len1) + 2*std_(close_, len1) )
        return [name,alpha.round(num_round)]   
    def alphaZS_FH13(self,name = 'alphaZS_FH13',len1=20,maxbacklength=21):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        #
        alpha = (ema_(close_, len1) - 2*std_(close_, len1) )
        return [name,alpha.round(num_round)]        
    def alphaZS_FH14(self,name = 'alphaZS_FH14',len1=20,maxbacklength=21):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        #
        alpha = (close_ - ema_(close_, len1) + 2*std_(close_, len1)) / (4*std_(close_, len1)) 
        return [name,alpha.round(num_round)]   
    def alphaZS_FH21(self,name = 'alphaZS_FH21',len1=20,maxbacklength=21):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        #
        alpha = (amount_ - delay_(amount_, len1))/amount_.replace(0, np.nan)
        return [name,alpha.round(num_round)]
    def alphaZS_FH23(self,name = 'alphaZS_FH23',len1=60,maxbacklength=61):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        #

        alpha=tsmax_(high_, len1)/close_
        return [name,alpha.round(num_round)]   
    def alphaZS_FH24(self,name = 'alphaZS_FH24',len1=60,maxbacklength=61):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        #
        alpha = tsmin_(low_, len1)
        alpha=alpha/close_
        return [name,alpha.round(num_round)]
    def alphaZS_FH25(self,name = 'alphaZS_FH25',len1=60,maxbacklength=61):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        #
        alpha = (close_ - tsmin_(low_, len1)) / (tsmax_(high_,len1) - tsmin_(low_,len1)).replace(0, np.nan)
        return [name,alpha.round(num_round)]
    def alphaZS_FH32(self,name = 'alphaZS_FH32',maxbacklength=1):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        #
        alpha = (high_ - max_(close_, open_)) / (abs_(close_ - open_)).replace(0, np.nan)
        return [name,alpha.round(num_round)]
    def alphaZS_FH34(self,name = 'alphaZS_FH34',len1=120,maxbacklength=121):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        #
        alpha = tshighmdd_(high_, len1) - tslowmdd_(low_, len1)
        alpha=alpha/close_
        return [name,alpha.round(num_round)]
    
    def alphaZS_FH35(self,name = 'alphaZS_FH35',len1=120,maxbacklength=121):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        #
        alpha = tshighmdd_(high_, len1) + tslowmdd_(low_, len1)
        alpha=alpha/close_
        return [name,alpha.round(num_round)]     
    def alphaZS_FH38(self,name = 'alphaZS_FH38',len1=120,maxbacklength=121):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        #
        alpha = ema_((high_ - low_)/close_, len1)
        return [name,alpha.round(num_round)]
    def alphaZS_FH43(self,name = 'alphaZS_FH43',len1=12,maxbacklength=13):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        #
        alpha = sum_(tsmax_(high_, len1) - tsmin_(low_, len1), len1)
        return [name,alpha.round(num_round)]
    def alphaZS_FH54(self,name = 'alphaZS_FH54',maxbacklength=1):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        #
        alpha = (high_ - max_(close_, open_) + min_(close_, open_) - low_) / (high_ - low_).replace(0, np.nan)
        return [name,alpha.round(num_round)]
    def alphaZS_FH58(self,name = 'alphaZS_FH58',len1=120,maxbacklength=121):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        #
        alpha = (amount_ - mean_(amount_, len1))/(std_(amount_, len1)).replace(0, np.nan)
        return [name,alpha.round(num_round)]
    def alphaZS_FH62(self,name = 'alphaZS_FH62',len1=5,maxbacklength=61):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        #
        delay=len1
        temp=(tsmax_(close_, delay)-close_)<=(close_-tsmin_(close_, delay))
        flag=2*temp-1
        net=tsmax_(close_, delay)- tsmin_(close_, delay)
        tot=sum_(delta_(close_,1).abs(),delay)
        nt=net/tot
        avg=mean_(nt,delay*5)
        std=std_(nt,delay*5)
        alpha=(((nt>=avg+1.5*std)*flag).replace(0,-10)+10*(nt<avg)).replace(-10,np.nan)
        return [name,alpha.round(num_round)]            
    def alphaZS_FH68(self,name = 'alphaZS_FH68',len1=50,maxbacklength=61):   
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        #
        '''
        area1=Summation(close[1]-hp[1],cl)/Summation(abs(close[1]-hp[1]),cl)
        取area值
        '''
        hp_=tsmax_(close_, len1)
        area=sum_(close_-hp_,len1)/sum_(abs_(close_-hp_),len1)
        alpha=area
        return [name,alpha.round(num_round)]
    def alphaZS_FH69(self,name = 'alphaZS_FH69',len1=50,maxbacklength=61):   
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]    
        #
        '''
        vpin
        '''
        deltp=(np.log(close_/close_.shift()))*10000
        std= deltp.rolling(len1).std()
        temp=pd.DataFrame(norm.cdf(deltp/std),index=close_.index)
        vb=(temp*vol_).rolling(len1).sum()
        vs=vol_.rolling(len1).sum()-vb
        alpha=(vb-vs).abs().rolling(len1).sum()/vol_.rolling(len1).sum().rolling(len1).sum()

        return [name,alpha.round(num_round)]
       
       
       
       
       
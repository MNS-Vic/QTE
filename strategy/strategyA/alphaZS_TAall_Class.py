''' 
1 替换output为return
2 替换n ame为self,n ame
3 替换所有的DF_变量为self.DF_
4 初始化emtpy，ind函数
'''

from apitool import *
import pandas as pd
import numpy as np
class AlphasZS_TAall(object):
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
    def alphaZS_TAall1(self,name = 'alphaZS_TAall1',len1=50,maxbacklength=101):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #
        alpha = (close_-open_).rolling(len1).mean()
        return [name,alpha.round(num_round)]
    def alphaZS_TAall5(self,name = 'alphaZS_TAall5',len1=20,maxbacklength=31):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #
        tr=max_(max_((high_-low_),abs(delay_(close_,1)-high_)),abs(delay_(close_,1)-low_))
        atr= mean_(tr,len1).replace(0.0,np.nan)
        RWIH=(high_-tsmin_(low_,len1))/atr
        RWIL=( tsmax_(high_,len1)-low_)/atr
        flag= 1 if RWIH>RWIL else -1
        alpha = RWIH if flag==1 else -1*RWIL
        return [name,alpha.round(num_round)]
    def alphaZS_TAall6(self,name = 'alphaZS_TAall6',len1=5,maxbacklength=61):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #
        tr=max_(max_((high_-low_),abs(delay_(close_,1)-high_)),abs(delay_(close_,1)-low_))
        atr= mean_(tr,len1).replace(0.0,np.nan)
        f=atr
        g= if_(close_>delay_(close_,1),f/close_.diff().replace(0,np.nan),f)       
        h=min_(g,len1)
        i=max_(g,len1)
        j=if_(i>h,(g-h)/(i-h).replace(0,np.nan),g-h)
        alpha=mean_(j,len1)
        return [name,alpha.round(num_round)]        
    def alphaZS_TAall8(self,name = 'alphaZS_TAall8',len1=7,maxbacklength=41):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #
        lc=delay_(close_,len1)       
        alpha = mean_(max_(close_-lc,0*close_),len1)/mean_(abs(close_-lc),len1)
        return [name,alpha.round(num_round)]
    def alphaZS_TAall9(self,name = 'alphaZS_TAall9',maxbacklength=3):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #
        alpha = open_/close_ - 1
        return [name,alpha.round(num_round)]
    def alphaZS_TAall10(self,name = 'alphaZS_TAall10',len1 = 5,maxbacklength=16):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #       
        U=mean_(if_(delta_(close_,1)>0,delta_(close_,1),0*close_),len1)      
        alpha = U/mean_(abs(delta_(close_,1)),len1)-0.5
        return [name,alpha.round(num_round)]     
    def alphaZS_TAall11(self,name = 'alphaZS_TAall11',len1=50,maxbacklength=101):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #
        co=close_-open_
        hl=high_-low_
        V1=[co+2*delay_(co,1)+2*delay_(co,2)+delay_(co,3)]/6
        V2=[hl+2*delay_(hl,1)+2*delay_(hl,2)+delay_(hl,3)]/6
        S1=sum_(V1,len1)
        S2=sum_(V2,len1)
        alpha = S1/S2 
        return [name,alpha.round(num_round)]
    def alphaZS_TAall21(self,name = 'alphaZS_TAall21',len1=10,maxbacklength=101):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #
        temp1=mean_(mean_(close_-(tsmax_(high_,len1)+tsmin_(low_,len1))/2,len1),len1)
        temp2=mean_(mean_(tsmax_(high_,len1)-tsmin_(low_,len1),len1),len1)/2
        
        alpha = temp1/temp2.replace(0,np.nan)
        return [name,alpha.round(num_round)]
    def alphaZS_TAall22(self,name = 'alphaZS_TAall22',len1=5,maxbacklength=16):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #
        g=(close_-tsmin_(low_,len1))
        h=(tsmax_(high_,len1)-tsmin_(low_,len1))
        i=sum_(g,len1)
        j=sum_(h,len1)
        d=i/j.replace(0,np.nan)
        alpha=mean_(d,len1)
        return [name,alpha.round(num_round)]     
    def alphaZS_TAall23(self,name = 'alphaZS_TAall23',maxbacklength=4):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #
        alpha = close_.shift()-close_+0.5*(close_.shift()-open_.shift())+0.25*(close_-open_)
        return [name,alpha.round(num_round)]
    def alphaZS_TAall24(self,name = 'alphaZS_TAall24',len1=20,maxbacklength=101):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #
        temp1=mean_(close_,len1)
        temp2=mean_(temp1,len1)
        temp3=mean_(temp2,len1)
        alpha = (3*temp1-3*temp2+temp3)-1
        return [name,alpha.round(num_round)]        
    def alphaZS_TAall25(self,name = 'alphaZS_TAall25',len1=10,maxbacklength=101):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #
        temp1=mean_(mean_(close_-(tsmax_(high_,len1)+tsmin_(low_,len1))/2,len1),len1)
        temp2=mean_(mean_(tsmax_(high_,len1)-tsmin_(low_,len1),len1),len1)/2
        
        alpha = temp1/temp2.replace(0,np.nan)
        return [name,alpha.round(num_round)]
    def alphaZS_TAall30(self,name = 'alphaZS_TAall30',len1=10,maxbacklength=61):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #       
        temp= mean_( mean_( mean_(close_,len1),len1 ),len1 )
        alpha =temp/delay_(temp,1).replace(0,np.nan)-1
        return [name,alpha.round(num_round)]  
    def alphaZS_TAall37(self,name = 'alphaZS_TAall37',len1=10,maxbacklength=51):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #
        temp=mean_( high_-low_,len1)       
        alpha = temp/delay_(temp,len1).replace(0,np.nan)-1
        return [name,alpha.round(num_round)]
    def alphaZS_TAall39(self,name = 'alphaZS_TAall39',len1=10,maxbacklength=51):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #     
        alpha = mean_(vol_,len1)/mean_(vol_,len1*2).replace(0,np.nan)-1
        return [name,alpha.round(num_round)]  
    def alphaZS_TAall40(self,name = 'alphaZS_TAall40',len1=5,maxbacklength=16):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #
        alpha = vol_/delay_(vol_,len1)
        return [name,alpha.round(num_round)]
    def alphaZS_TAall41(self,name = 'alphaZS_TAall41',len1=10,maxbacklength=51):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #
        AD= if_(close_>close_.shift(),close_-min_(close_.shift(),low_),if_(close_<close_.shift(),close_-max_(close_.shift(),high_),0))
        alpha = AD+AD.shift()
        return [name,alpha.round(num_round)]  
    def alphaZS_TAall42(self,name = 'alphaZS_TAall42',len1=10,maxbacklength=101):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        alpha = (tsmax_(high_,len1)-close_)/(tsmax_(high_,len1)-tsmin_(low_,len1)).replace(0,np.nan)
        return [name,alpha.round(num_round)]
   
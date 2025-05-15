''' 
1 替换output为return
2 替换n ame为self,n ame
3 替换所有的DF_变量为self.DF_
4 初始化emtpy，ind函数
5 替换return a lpha 为return [n ame,a lpha.round(num_round)]
'''

from apitool import *
import pandas as pd
import numpy as np

class AlphasZS_PDF(object): 
    def __init__(self,open_,high_,low_,close_,vol_,amount_,opt_,vwap_):
        #函数与self,name的对应表    mya.open = self.open
        self.open=open_#保留一个格式用于其它因子DataFrame调整
        self.high = high_
        self.low = low_
        self.close = close_
        self.vol=vol_
        self.opt=opt_
        self.amount = amount_    
        self.vwap=vwap_      
        self.empty=lambda n:open_.applymap(lambda x:n)
        #
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~自定义alphaZS_PDF~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def alphaZS_PDF1(self,name='alphaZS_PDF1',len1=10,maxbacklength=12):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #    
        volnew = log_(vol_) # vol的nan填充为1
        rank1=(delta_(volnew,1))
        price_=(close_/open_-1)
        rank2=(price_)
        alphaZS_PDF=- rank1.rolling(len1).corr(rank2)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]
    
    def alphaZS_PDF2(self,name='alphaZS_PDF2',maxbacklength=3):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        temp_=((close_-low_)-(high_-close_))/(high_-low_).replace(0,np.nan)
        alphaZS_PDF=-1*delta_(temp_,1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]   
        
    def alphaZS_PDF3(self,name='alphaZS_PDF3',len1=10,maxbacklength=12):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        condition_= close_==close_.shift(1)
        true_=self.empty(0)[-maxbacklength:]
        false_=close_-if_(close_>close_.shift(1),min_(low_,close_.shift(1)),max_(high_,close_.shift(1)))
        temp=if_(condition_,true_,false_)
        alphaZS_PDF=sum_(temp,len1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]
    
    def alphaZS_PDF4(self,name='alphaZS_PDF4',len1=10,maxbacklength=102):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        true2_=self.empty(1)[-maxbacklength:]
        false2_=-1*self.empty(1)[-maxbacklength:]
        condition2_=(vol_/mean_(vol_,len1).replace(0,np.nan)>=1) 
        true1_=self.empty(1)[-maxbacklength:]
        false1_=if_(condition2_,true2_,false2_)       
        condition1_=sum_(close_,len1)/len1<(sum_(close_,len1*4)/len1/4-std_(close_,len1*4)) 
        condition_=(sum_(close_,len1*4)/len1/4+std_(close_,len1*4))<sum_(close_,len1)/len1
        true_=-1*self.empty(1)[-maxbacklength:]
        false_=if_(condition1_,true1_,false1_)
        alphaZS_PDF=if_(condition_,true_,false_)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]
    
    def alphaZS_PDF5(self,name='alphaZS_PDF5',len1=10,maxbacklength=152):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #
        temp=corr_(tsrank_(vol_,len1),tsrank_(high_,len1),len1)
        alphaZS_PDF=-1*tsmax_(temp,len1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]    
    
    def alphaZS_PDF6(self,name='alphaZS_PDF6',maxbacklength=5):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #
        alphaZS_PDF=(-1*sign_(delta_(open_*0.85+high_*0.15,4)))
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]    
    def alphaZS_PDF7(self,name='alphaZS_PDF7',maxbacklength=15):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #
        alphaZS_PDF=((max_(vwap_-close_,self.empty(3)[-maxbacklength:]))+(min_(vwap_-close_,self.empty(3)[-maxbacklength:])))*(delta_(vol_,3))
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]      
    def alphaZS_PDF8(self,name='alphaZS_PDF8',maxbacklength=5):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #
        alphaZS_PDF=( -1*(delta_( (high_+low_)/2*0.2+vwap_*0.8,4) ))
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]   
    def alphaZS_PDF9(self,name='alphaZS_PDF9',maxbacklength=200):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #
        alphaZS_PDF=sma_(  ((high_+low_)/2- (delay_(high_,1)+delay_(low_,1))/2)*(high_-low_)/vol_.replace(0,np.nan),7,2 )
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]   
    def alphaZS_PDF10(self,name='alphaZS_PDF10',len1=20,maxbacklength=102):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #
        alphaZS_PDF=(max_(  if_( ret_<0,std_(ret_,len1),close_*close_),self.empty(5)[-maxbacklength:])   )
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]      
    def alphaZS_PDF11(self,name='alphaZS_PDF11',len1=10,maxbacklength=12):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #
        alphaZS_PDF=sum_( ((close_-low_)-(high_-close_))/(high_-low_).replace(0,np.nan)*vol_,len1)    
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    def alphaZS_PDF12(self,name='alphaZS_PDF12',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #    
        alphaZS_PDF=(open_-sum_(vwap_,len1)/len1)*(-1*(abs_(close_-vwap_)))
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]     
    def alphaZS_PDF13(self,name='alphaZS_PDF13',maxbacklength=1):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #
        alphaZS_PDF=sqrt_(high_*low_)-vwap_    
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]      
    def alphaZS_PDF14(self,name='alphaZS_PDF14',len1=10,maxbacklength=12):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        df=close_
        alphaZS_PDF=df.rolling(len1).apply(lambda x: (x[-1]/x[0]-1)*100)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]
    def alphaZS_PDF15(self,name='alphaZS_PDF15',maxbacklength=2):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #
        alphaZS_PDF=open_/delay_(close_,1) - 1
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]
    def alphaZS_PDF16(self,name='alphaZS_PDF16',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #
        alphaZS_PDF=-1*tsmax_((corr_((vol_),(vwap_),len1)),len1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]
    def alphaZS_PDF17(self,name='alphaZS_PDF17',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #
        pass
       # temp1=delta_(close_,5)
       # temp2=(vwap_-tsmax_(vwap_,15))
       # alphaZS_PDF=callback(temp2,temp1,lambda x,y:x**y)
       # #------------output---------------------
       # return [name,alphaZS_PDF.round(num_round)]    
    def alphaZS_PDF18(self,name='alphaZS_PDF18',len1=10,maxbacklength=12):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #
        alphaZS_PDF=close_/delay_(close_,len1)    
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]    
    def alphaZS_PDF19(self,name='alphaZS_PDF19',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #
        alphaZS_PDF=if_( close_<delay_(close_,len1),close_/delay_(close_,len1)-1,if_( close_==delay_(close_,len1),self.empty(0)[-maxbacklength:],1-close_/delay_(close_,len1)   ))    
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]        
    def alphaZS_PDF20(self,name='alphaZS_PDF20',len1=10,maxbacklength=12):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #
        alphaZS_PDF=(close_/delay_(close_,len1)-1)*100
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]           
    def alphaZS_PDF21(self,name='alphaZS_PDF21',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        '''
        b1=corr*std_y/std_x
        '''
        pass
    #    df=mean_(close_,6)
    #    alphaZS_PDF=df.rolling(6).apply(lambda x: (np.corrcoef(x,range(1,6+1))[0][1])*np.std(range(1,6+1))/np.std(x) )
        #------------output---------------------
    #    return [name,alphaZS_PDF.round(num_round)]        
    def alphaZS_PDF22(self,name='alphaZS_PDF22',len1=10,maxbacklength=None):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #
        alphaZS_PDF=sma_( (close_/mean_(close_,len1)-1)-delay_(close_/mean_(close_,len1)-1,3),12,1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]    
    def alphaZS_PDF23(self,name='alphaZS_PDF23',len1=10,maxbacklength=None):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #
        alphaZS_PDF=100*sma_( if_(close_>delay_(close_,1),std_(close_,len1),self.empty(0)[-maxbacklength:]),20,1 ) \
        / ( sma_( if_(close_>delay_(close_,1),std_(close_,len1),self.empty(0)[-maxbacklength:]),20,1 )+sma_( if_(close_<=delay_(close_,1),std_(close_,len1),self.empty(0)[-maxbacklength:]),20,1 ) )
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]     
    def alphaZS_PDF24(self,name='alphaZS_PDF24',len1=10,maxbacklength=200):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #
        alphaZS_PDF=sma_(close_-delay_(close_,len1),5,1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]     
    def alphaZS_PDF25(self,name='alphaZS_PDF25',len1=5,maxbacklength=200):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #
        alphaZS_PDF=((-1*( ( delta_(close_,len1)*(  1-( decaylinear_((vol_/mean_(vol_,len1).replace(0,np.nan)),len1) )  ))))*(1+(sum_(ret_,len1)) ) )
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]         
    def alphaZS_PDF26(self,name='alphaZS_PDF26',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #
        alphaZS_PDF=(sum_(close_,len1)/7-close_)+(corr_(vwap_,delay_(close_,len1),len1))
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]     
    def alphaZS_PDF27(self,name='alphaZS_PDF27',len1=10,maxbacklength=100):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #    
        alphaZS_PDF=100*wma_( (close_/delay_(close_,3)-1)+ (close_/delay_(close_,6)-1),len1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]       
    def alphaZS_PDF28(self,name='alphaZS_PDF28',len1=10,maxbacklength=500):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #
        alphaZS_PDF= 3*sma_( ( close_-tsmin_(low_,len1))/(tsmax_(high_,len1)-tsmin_(low_,len1)).replace(0,np.nan)*100,3,1 )-2*  \
        sma_(sma_( ( close_-tsmin_(low_,len1))/(tsmax_(high_,len1)-tsmin_(low_,len1)).replace(0,np.nan)*100,3,1 ),3,1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]      
    def alphaZS_PDF29(self,name='alphaZS_PDF29',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #    
        alphaZS_PDF=(close_-delay_(close_,len1))/delay_(close_,len1)*vol_
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    def alphaZS_PDF30(self,name='alphaZS_PDF30',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        pass
    #    alphaZS_PDF=wma_(regresi_(close_/delay_(close_,1)))
    def alphaZS_PDF31(self,name='alphaZS_PDF31',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF=(close_-mean_(close_,len1))/mean_(close_,len1)*100
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    def alphaZS_PDF32(self,name='alphaZS_PDF32',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF=-1*sum_((corr_((high_),(vol_),len1)),len1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    def alphaZS_PDF33(self,name='alphaZS_PDF33',len1=5,maxbacklength=222):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        alphaZS_PDF=((((-1*tsmin_(low_,len1))+delay_(tsmin_(low_,len1),len1))*( ( (sum_(ret_,len1*10)-sum_(ret_,len1))/len1*10)))*tsrank_(vol_,len1))
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]     
    def alphaZS_PDF34(self,name='alphaZS_PDF34',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #   
        alphaZS_PDF=mean_(close_,len1)/close_
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]         
    def alphaZS_PDF35(self,name='alphaZS_PDF35',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #    
        alphaZS_PDF= -1*min_( ( decaylinear_( delta_(open_,1),len1)),( decaylinear_( corr_(vol_,open_*0.65+open_*0.35,len1),len1)) )
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]      
    def alphaZS_PDF36(self,name='alphaZS_PDF36',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #      
        alphaZS_PDF= (sum_(corr_( (vol_),(vwap_),len1),len1)  )  
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]       
    def alphaZS_PDF37(self,name='alphaZS_PDF37',len1=10,maxbacklength=42):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #      
        alphaZS_PDF=-1*(  sum_(open_,len1)*sum_(ret_,len1)-delay_( sum_(open_,len1)*sum_(ret_,len1),len1) )
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    def alphaZS_PDF38(self,name='alphaZS_PDF38',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        alphaZS_PDF=if_( sum_(high_,len1)/len1<high_,-1*delta_(high_,2),self.empty(0)[-maxbacklength:] )
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    def alphaZS_PDF39(self,name='alphaZS_PDF39',len1=5,maxbacklength=402):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        alphaZS_PDF=(decaylinear_(delta_(close_,2),len1))-(decaylinear_(corr_(vwap_*0.3+open_*0.7,sum_(mean_(vol_,len1*10),len1),len1),len1) )
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    def alphaZS_PDF40(self,name='alphaZS_PDF40',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #      
        alphaZS_PDF=100*sum_( if_(close_>delay_(close_,1),vol_,self.empty(0)[-maxbacklength:]),len1 )/sum_( if_(close_<=delay_(close_,1),vol_,self.empty(0)[-maxbacklength:]),len1 ).replace(0,np.nan)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]      
    def alphaZS_PDF41(self,name='alphaZS_PDF41',maxbacklength=42):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        
        #    
        alphaZS_PDF=-1*( max_( delta_(vwap_,3),self.empty(5)[-maxbacklength:]))
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]    
    def alphaZS_PDF42(self,name='alphaZS_PDF42',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #
        alphaZS_PDF=(-1*( std_(high_,len1)))*corr_(high_,vol_,len1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]      
    def alphaZS_PDF43(self,name='alphaZS_PDF43',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #           
        alphaZS_PDF=sum_( if_(close_>delay_(close_,1),vol_,if_(close_<delay_(close_,1),-1*vol_,self.empty(0)[-maxbacklength:])),len1  )
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]       
    def alphaZS_PDF44(self,name='alphaZS_PDF44',len1=5,maxbacklength=222):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #     
        alphaZS_PDF=tsrank_(decaylinear_(corr_(low_,mean_(vol_,len1),len1),len1),len1)+tsrank_(decaylinear_(delta_(vwap_,len1),len1),len1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]     
    def alphaZS_PDF45(self,name='alphaZS_PDF45',len1=5,maxbacklength=122):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #      
        alphaZS_PDF=( delta_( close_*0.6+open_*0.4 ,1) )*(corr_(vwap_,mean_(vol_,len1*10),len1))
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]      
    def alphaZS_PDF46(self,name='alphaZS_PDF46',len1=3,maxbacklength=30):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #
        alphaZS_PDF=(mean_(close_,len1)+mean_(close_,len1*2)+mean_(close_,len1*4)+mean_(close_,len1*6))/(4*close_) 
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]     
    def alphaZS_PDF47(self,name='alphaZS_PDF47',len1=10,maxbacklength=None):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #
        alphaZS_PDF=sma_( 100*(tsmax_(high_,len1)-close_)/ (tsmax_(high_,len1)-tsmin_(low_,len1)).replace(0,np.nan),9,1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]   
    def alphaZS_PDF48(self,name='alphaZS_PDF48',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #
        alphaZS_PDF=-1*( sign_(close_-delay_(close_,1))) + sign_(delay_(close_,1)-delay_(close_,2)) + \
        sign_( delay_(close_,2)-delay_(close_,3) )
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]   
    def alphaZS_PDF49(self,name='alphaZS_PDF49',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #
        temp1= sum_(  if_( high_+low_>=delay_(high_,1)+delay_(low_,1),self.empty(0)[-maxbacklength:],max_( abs_(high_-delay_(high_,1)),abs_(low_-delay_(low_,1)) )  ),len1  )
        temp2=sum_(  if_( high_+low_<=delay_(high_,1)+delay_(low_,1),self.empty(0)[-maxbacklength:],max_( abs_(high_-delay_(high_,1)),abs_(low_-delay_(low_,1)) )  ),len1  )
        alphaZS_PDF=temp1/(temp1+temp2).replace(0,np.nan)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]   
    def alphaZS_PDF50(self,name='alphaZS_PDF50',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #
        temp1=sum_(  if_( high_+low_>=delay_(high_,1)+delay_(low_,1),self.empty(0)[-maxbacklength:],max_( abs_(high_-delay_(high_,1)),abs_(low_-delay_(low_,1)) )  ),len1  )
        temp2=sum_(  if_( high_+low_<=delay_(high_,1)+delay_(low_,1),self.empty(0)[-maxbacklength:],max_( abs_(high_-delay_(high_,1)),abs_(low_-delay_(low_,1)) )  ),len1  )
        alphaZS_PDF=(temp2-temp1)/(temp1+temp2).replace(0,np.nan)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)] 
    def alphaZS_PDF51(self,name='alphaZS_PDF51',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #
        temp1=sum_(  if_( high_+low_>=delay_(high_,1)+delay_(low_,1),self.empty(0)[-maxbacklength:],max_( abs_(high_-delay_(high_,1)),abs_(low_-delay_(low_,1)) )  ),len1  )
        temp2=sum_(  if_( high_+low_<=delay_(high_,1)+delay_(low_,1),self.empty(0)[-maxbacklength:],max_( abs_(high_-delay_(high_,1)),abs_(low_-delay_(low_,1)) )  ),len1  )
        alphaZS_PDF=temp2/(temp1+temp2).replace(0,np.nan)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    def alphaZS_PDF52(self,name='alphaZS_PDF52',len1=10,maxbacklength=102):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #    
        alphaZS_PDF=100*sum_( max_(self.empty(0)[-maxbacklength:],high_-delay_( (high_+low_+close_)/3,1) ),len1)/sum_( max_(self.empty(0)[-maxbacklength:],delay_( (high_+low_+close_)/3,1) )-low_,len1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]      
    def alphaZS_PDF53(self,name='alphaZS_PDF53',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #        
        alphaZS_PDF=count_(close_>delay_(close_,1),len1)/len1*100
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]       
    def alphaZS_PDF54(self,name='alphaZS_PDF54',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #      
        alphaZS_PDF=-1*( std_(abs_(close_-open_),len1)+close_-open_+corr_(close_,open_,len1) )
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]      
    def alphaZS_PDF55(self,name='alphaZS_PDF55',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass    
        # alphaZS_PDF=sum_( 16*( close_ -delay_(close_,1)+(close_-open_)/2+delay_(close_,1)-delay_(open_,1) )/(( 
        #        if_( abs_(high_-delay_(close_,1))>abs_(low_-delay_(close_,1)) &   abs_(high_-delay_(close_,1))>abs_(high_-delay_(low_,1))  ,
               
        #        )
    def alphaZS_PDF56(self,name='alphaZS_PDF56',len1=10,maxbacklength=52):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #      
        temp=( ( corr_( sum_( (high_+low_)/2,len1 ),sum_(mean_(vol_,len1),len1),len1)))
        alphaZS_PDF=( open_-tsmin_(open_,len1))< (temp*temp*temp*temp*temp)  
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]          
    def alphaZS_PDF57(self,name='alphaZS_PDF57',len1=10,maxbacklength=202):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        alphaZS_PDF=sma_( close_-tsmin_(low_,len1)/( tsmax_(high_,len1)-tsmin_(low_,len1)).replace(0,np.nan)*100,3,1 )
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]    
    def alphaZS_PDF58(self,name='alphaZS_PDF58',len1=10,maxbacklength=12):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        alphaZS_PDF=count_(close_>delay_(close_,1),len1)/len1*100
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]    
    def alphaZS_PDF59(self,name='alphaZS_PDF59',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        alphaZS_PDF=sum_(   if_(close_==delay_(close_,1), self.empty(0)[-maxbacklength:],close_-if_( close_>delay_(close_,1),min_(low_,delay_(close_,1)),max_(high_,delay_(close_,1)))  ) , len1 )
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]   
    def alphaZS_PDF60(self,name='alphaZS_PDF60',len1=10,maxbacklength=12):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        alphaZS_PDF=sum_( ((close_-low_)-(high_-close_))/(high_-low_).replace(0,np.nan)*vol_,len1)    
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    def alphaZS_PDF61(self,name='alphaZS_PDF61',len1=5,maxbacklength=122):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #  
        alphaZS_PDF=-1*max_( (decaylinear_(delta_(vwap_,1),len1)),(decaylinear_((corr_(low_,mean_(vol_,len1),len1)),len1)) )
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    def alphaZS_PDF62(self,name='alphaZS_PDF62',len1=10,maxbacklength=12):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #     
        alphaZS_PDF=-1*corr_(high_,(vol_),len1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]      
    def alphaZS_PDF63(self,name='alphaZS_PDF63',len1=10,maxbacklength=None):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #      
        alphaZS_PDF=100*sma_(max_(close_-delay_(close_,1),self.empty(0)[-maxbacklength:]),6,1)/sma_(abs_(close_-delay_(close_,1)),6,1).replace(0,np.nan)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]
    def alphaZS_PDF64(self,name='alphaZS_PDF64',len1=15,maxbacklength=222):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        #
        alphaZS_PDF=-1*max_( (decaylinear_(corr_((vwap_),(vol_),len1),len1)),(decaylinear_(max_(corr_((close_),(mean_(vol_,len1)),len1),self.empty(0.3) ),len1)) )
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]
    def alphaZS_PDF65(self,name='alphaZS_PDF65',len1=10,maxbacklength=12):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF=mean_(close_,len1)/close_
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]    
    def alphaZS_PDF66(self,name='alphaZS_PDF66',len1=10,maxbacklength=12):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF=(close_-mean_(close_,len1))/mean_(close_,len1)*100
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]       
    
    # ----------------------------------------------------20180428---------------------------------------------------------------------
    def alphaZS_PDF67(self,name = 'alphaZS_PDF67',len1=10,maxbacklength=None):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = sma_(max_(close_ - delay_(close_, 1), self.empty(0)[-maxbacklength:]), 24, 1)/sma_(abs_(close_ - delay_(close_, 1)), 24, 1).replace(0,np.nan) * 100
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)] 
    
    def alphaZS_PDF68(self,name = 'alphaZS_PDF68',len1=10,maxbacklength=202):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = sma_(((high_+close_)/2 - (delay_(high_, 1)+delay_(low_,1))/2)*(high_-low_).replace(0,np.nan)/vol_, 15, 2)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF69(self,name = 'alphaZS_PDF69',len1=10,maxbacklength=62):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        DTM_ = if_(open_ <= delay_(open_, 1), 0, max_(high_-open_, open_-delay_(open_, 1)))
        DBM_ = if_(open_ >= delay_(open_, 1), 0, max_(open_-low_, open_-delay_(open_, 1)))
        alphaZS_PDF = if_(sum_(DTM_, 20)>sum_(DBM_,len1), (sum_(DTM_, len1)-sum_(DBM_,len1))/sum_(DTM_,len1).replace(0,np.nan),  \
            if_(sum_(DTM_, len1)==sum_(DBM_,len1), 0, (sum_(DTM_, len1)-sum_(DBM_,len1))/sum_(DBM_,len1).replace(0,np.nan)))
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF70(self,name = 'alphaZS_PDF70',len1=10,maxbacklength=12):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = std_(amount_, len1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF71(self,name = 'alphaZS_PDF71',len1=10,maxbacklength=12):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = (close_ - mean_(close_, len1))/mean_(close_, len1)*100
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF72(self,name = 'alphaZS_PDF72',len1=10,maxbacklength=None):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = sma_((tsmax_(high_, len1) - close_)/(tsmax_(high_, len1) - tsmin_(low_, len1)).replace(0,np.nan)*100, 15, 1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF73(self,name = 'alphaZS_PDF73',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = (decaylinear_(corr_(vwap_, mean_(vol_, 30), 4), 3)) - tsrank_(decaylinear_(decaylinear_(corr_(close_, vol_, 10), 16), 4), 5) 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF74(self,name = 'alphaZS_PDF74',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = (corr_(sum_(low_*0.35 + vwap_*0.65, 20), sum_(mean_(vol_,40), 20), 7)) + (corr_((vwap_), (vol_), 6))
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF75(self,name = 'alphaZS_PDF75',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF76(self,name = 'alphaZS_PDF76',len1=10,maxbacklength=42):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = std_(abs_(close_/delay_(close_, 1) - 1)/vol_.replace(0,np.nan), len1)/mean_(abs_(close_/delay_(close_, 1) - 1)/vol_.replace(0,np.nan), len1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF77(self,name = 'alphaZS_PDF77',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF78(self,name = 'alphaZS_PDF78',len1=10,maxbacklength=42):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = ((high_+low_+close_)/3 - ma_((high_+low_+close_)/3, len1))/(0.015*mean_(abs_(close_ - mean_((high_+low_+close_)/3, len1)), len1))
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF79(self,name = 'alphaZS_PDF79',maxbacklength=202):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = sma_(max_(close_ - delay_(close_, 1), self.empty(0)[-maxbacklength:]), 12, 1)/sma_(abs_(close_ - delay_(close_, 1)), 12, 1).replace(0,np.nan)*100
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF80(self,name = 'alphaZS_PDF80',len1=10,maxbacklength=70):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = (vol_ - delay_(vol_, len1))/(delay_(vol_, len1)).replace(0,np.nan)*100
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF81(self,name = 'alphaZS_PDF81',maxbacklength=202):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = sma_(vol_, 21, 2)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF82(self,name = 'alphaZS_PDF82',len1=10,maxbacklength=None):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = sma_((tsmax_(high_, len1) - close_)/(tsmax_(high_, len1)-tsmin_(low_, len1)).replace(0,np.nan)*100, 20, 1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF83(self,name = 'alphaZS_PDF83',len1=10,maxbacklength=12):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = -1*(cov_((high_), (vol_), len1))
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF84(self,name = 'alphaZS_PDF84',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = sum_(if_(close_ > delay_(close_,1), vol_, if_(close_ < delay_(close_,1), -vol_, 0)), len1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF85(self,name = 'alphaZS_PDF85',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = tsrank_(vol_/mean_(vol_,20).replace(0,np.nan), 20) * tsrank_(-1*delta(close_,7), 8)
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF86(self,name = 'alphaZS_PDF86',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF87(self,name = 'alphaZS_PDF87',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF88(self,name = 'alphaZS_PDF88',len1=10,maxbacklength=12):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = (close_ - delay_(close_,len1))/delay_(close_,len1)*100
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF89(self,name = 'alphaZS_PDF89',maxbacklength=None):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = 2*(sma_(close_,13,2) - sma_(close_,27,2) - sma_(sma_(close_,13,2)-sma_(close_,27,2),10,2))
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]
    
    def alphaZS_PDF90(self,name = 'alphaZS_PDF90',len1=10,maxbacklength=12):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = -1*(corr_((vwap_), (vol_), len1))
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]
    
    def alphaZS_PDF91(self,name = 'alphaZS_PDF91',len1=15,maxbacklength=122):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = -1*(close_ - max_(close_, self.empty(5)[-maxbacklength:])) * (corr_(mean_(vol_,len1), low_, len1))
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF92(self,name = 'alphaZS_PDF92',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF93(self,name = 'alphaZS_PDF93',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = sum_(if_(open_>=delay_(open_,1), 0, max_(open_-low_, open_-delay_(open_,1))), len1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF94(self,name = 'alphaZS_PDF94',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = sum_(if_(close_>delay_(close_,1), vol_, if_(close_<delay_(close_,1), -vol_, 0)), len1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF95(self,name = 'alphaZS_PDF95',len1=10,maxbacklength=12):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = std_(amount_, len1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF96(self,name = 'alphaZS_PDF96',len1=10,maxbacklength=202):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = sma_(sma_((close_ - tsmin_(low_, len1))/(tsmax_(high_, len1) - tsmin_(low_, len1)).replace(0,np.nan)*100, 3, 1), 3, 1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF97(self,name = 'alphaZS_PDF97',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = std_(vol_, len1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF98(self,name = 'alphaZS_PDF98',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF99(self,name = 'alphaZS_PDF99',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = -1*(cov_((close_), (vol_), len1))
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]
    
    def alphaZS_PDF100(self,name = 'alphaZS_PDF100',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = std_(vol_, len1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]
    
    def alphaZS_PDF101(self,name = 'alphaZS_PDF101',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF102(self,name = 'alphaZS_PDF102',maxbacklength=None):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = sma_(max_(vol_ - delay_(vol_, 1), self.empty(0)[-maxbacklength:]), 6, 1)/sma_(abs_(vol_ - delay_(vol_, 1)), 6, 1).replace(0,np.nan)*100
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF103(self,name = 'alphaZS_PDF103',len1=10,maxbacklength=12):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = tsargmin_(low_, len1) * 5
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF104(self,name = 'alphaZS_PDF104',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF105(self,name = 'alphaZS_PDF105',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF106(self,name = 'alphaZS_PDF106',len1=10,maxbacklength=12):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = close_ - delay_(close_, len1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF107(self,name = 'alphaZS_PDF107',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF108(self,name = 'alphaZS_PDF108',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF109(self,name = 'alphaZS_PDF109',maxbacklength=202):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = sma_(high_ - low_, 10, 2)/sma_(sma_(high_-low_, 10, 2), 10, 2).replace(0,np.nan)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]
    
    def alphaZS_PDF110(self,name = 'alphaZS_PDF110',len1=10,maxbacklength=202):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = sum_(max_(self.empty(0)[-maxbacklength:], high_ - delay_(close_,1)), len1)/(sum_(max_(self.empty(0)[-maxbacklength:], delay_(close_, 1) - low_), len1)).replace(0,np.nan)*100
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]
    
    def alphaZS_PDF111(self,name = 'alphaZS_PDF111',maxbacklength=202):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = sma_(vol_*(2*close_ - high_ - low_)/(high_ - low_).replace(0,np.nan), 11, 2) - sma_(vol_*(2*close_ - high_ - low_)/(high_ - low_).replace(0,np.nan), 4, 2)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF112(self,name = 'alphaZS_PDF112',len1=10,maxbacklength=202):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        temp1 = sum_(if_(close_ - delay_(close_,1)>0, close_ - delay_(close_, 1), 0), len1)
        temp2 = sum_(if_(close_ - delay_(close_,1)<0, abs_(close_ - delay_(close_, 1)), 0), len1)
        alphaZS_PDF = (temp1-temp2)/(temp1+temp2).replace(0,np.nan)*100
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF113(self,name = 'alphaZS_PDF113',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF114(self,name = 'alphaZS_PDF114',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF115(self,name = 'alphaZS_PDF115',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF116(self,name = 'alphaZS_PDF116',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF117(self,name = 'alphaZS_PDF117',len1=10,maxbacklength=42):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = tsrank_(vol_, len1) * (1- tsrank_(close_+high_-low_, len1)) * (1- tsrank_(ret_, len1))
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF118(self,name = 'alphaZS_PDF118',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = sum_(high_ - open_, len1)/(sum_(open_ - low_, len1)).replace(0,np.nan)*100
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF119(self,name = 'alphaZS_PDF119',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]
    
    def alphaZS_PDF120(self,name = 'alphaZS_PDF120',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]
    
    def alphaZS_PDF121(self,name = 'alphaZS_PDF121',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF122(self,name = 'alphaZS_PDF122',maxbacklength=202):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = sma_(sma_(sma_(log_(close_), 13, 2), 13, 2), 13, 2)/delay_(sma_(sma_(sma_(log_(close_), 13, 2), 13, 2), 13, 2), 1) - 1
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF123(self,name = 'alphaZS_PDF123',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF124(self,name = 'alphaZS_PDF124',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF125(self,name = 'alphaZS_PDF125',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF126(self,name = 'alphaZS_PDF126',maxbacklength=1):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = (close_ + high_ + low_)/3
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF127(self,name = 'alphaZS_PDF127',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = mean_()
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF128(self,name = 'alphaZS_PDF128',len1=10,maxbacklength=12):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = 100 - (100/(1+sum_(if_(delta_(high_+low_+close_, 1)>0, (high_+low_+close_)/3*vol_, 0), len1) \
            /sum_(if_(delta_(high_+low_+close_, 1)<0, (high_+low_+close_)/3*vol_, 0), len1)))
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF129(self,name = 'alphaZS_PDF129',len1=10,maxbacklength=12):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = sum_(if_(close_ - delay_(close_, 1) < 0, abs_(close_ - delay_(close_, 1)), 0), len1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]
    
    def alphaZS_PDF130(self,name = 'alphaZS_PDF130',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]
    
    def alphaZS_PDF131(self,name = 'alphaZS_PDF131',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF132(self,name = 'alphaZS_PDF132',len1=10,maxbacklength=12):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = mean_(amount_, len1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF133(self,name = 'alphaZS_PDF133',len1=10,maxbacklength=12):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = tsargmax_(high_, len1)*5 - tsargmin_(low_, len1)*5
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF134(self,name = 'alphaZS_PDF134',len1=10,maxbacklength=12):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = (close_/delay_(close_, len1) - 1)*vol_
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF135(self,name = 'alphaZS_PDF135',len1=10,maxbacklength=None):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = sma_(delay_(close_/delay_(close_, len1), 1), 20, 1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF136(self,name = 'alphaZS_PDF136',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF137(self,name = 'alphaZS_PDF137',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # cond1 = if_(16*(close_ - delay_(close_, 1) + (close_ - open_)/2 + delay_(close_, 1) - delay_(open_, 1))/abs_(high_ - delay_(close_, 1)) \
        #         > abs_(low_ - delay_(close_, 1)), 1, 0)
        # cond2 = if_(abs_(high_ - delay_(close_, 1)) > abs_(high_ - delay_(low_, 1)), abs_(high_ - delay_(close_, 1))+abs_(low_ - delay_(close_, 1))/2 \
        #       + abs_(delay_(close_, 1) - delay_(open_, 1))/4, if_(abs_(low_ - delay_(close_, 1))>abs_(high_ - delay_(low_, 1)), 1, 0))
        # cond3 = if_(abs_(low_ - delay_(close_, 1))>abs_(high_ - delay_(close_, 1)), abs_(low_ - delay_(close_, 1)) + abs_(high_ - delay_(close_, 1))/2 \
        #       + abs_(delay_(close_, 1) - delay_(open_, 1))/4, abs_(high_ - delay_(low_, 1)))
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF138(self,name = 'alphaZS_PDF138',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF139(self,name = 'alphaZS_PDF139',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]
    
    def alphaZS_PDF140(self,name = 'alphaZS_PDF140',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]
    
    def alphaZS_PDF141(self,name = 'alphaZS_PDF141',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = -1*(corr_((high_), (mean_(vol_, len1)), len1))
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF142(self,name = 'alphaZS_PDF142',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF143(self,name = 'alphaZS_PDF143',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF144(self,name = 'alphaZS_PDF144',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = sumif_(abs_(close_/delay_(close_, 1)-1)/amount_*100000, len1, close_ < delay_(close_, 1)) / count_(close_ < delay_(close_, 1), len1).replace(0,np.nan)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF145(self,name = 'alphaZS_PDF145',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = (mean_(vol_, len1) - mean_(vol_, len1*2))/mean_(vol_ ,len1).replace(0,np.nan) * 100
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF146(self,name = 'alphaZS_PDF146',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = mean_((close_ - delay_(close_, 1))/delay_(close_, 1) - sma_((close_ - delay_(close_, 1))/delay_(close_, 1), 61, 2), 20) * \
        #         ((close_ - delay_(close_, 1))/delay_(close_, 1) - sma_((close_ - delay_(close_, 1))/delay_(close_, 1), 61, 2)) \
        #         / sma_((close_ - delay_(close_, 1))/delay_(close_, 1) - , 61, 2)
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF147(self,name = 'alphaZS_PDF147',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF148(self,name = 'alphaZS_PDF148',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF149(self,name = 'alphaZS_PDF149',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]
    
    def alphaZS_PDF150(self,name = 'alphaZS_PDF150',maxbacklength=1):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = (close_ + high_ + low_)/3*vol_
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]
    
    def alphaZS_PDF151(self,name = 'alphaZS_PDF151',len1=10,maxbacklength=None):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = sma_(close_ - delay_(close_, len1), 20, 1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF152(self,name = 'alphaZS_PDF152',len1=10,maxbacklength=None):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = sma_(mean_(delay_(sma_(delay_(close_/delay_(close_, 9), 1), 9, 1), 1), len1) - mean_(delay_(sma_(delay_(close_/delay_(close_, len1), 1), 9,1), 1),len1), 9, 1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF153(self,name = 'alphaZS_PDF153',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = (mean_(close_, len1) + mean_(close_, 6) + mean_(close_, 12) + mean_(close_, 24))/4
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF154(self,name = 'alphaZS_PDF154',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF155(self,name = 'alphaZS_PDF155',maxbacklength=None):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = sma_(vol_, 13, 2) - sma_(vol_, 27, 2) - sma_(sma_(vol_,13,2) - sma_(vol_,27,2), 10, 2)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF156(self,name = 'alphaZS_PDF156',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF157(self,name = 'alphaZS_PDF157',len1=10,maxbacklength=202):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = min_(prod_(((log_(sum_(tsmin_(((-1*(delta_(close_ - 1, 5)))), len1), 1)))), 1), self.empty(5)[-maxbacklength:]) + tsrank_(delay_(-1*ret_, 6), len1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF158(self,name = 'alphaZS_PDF158',maxbacklength=202):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = ((high_ - sma_(close_, 15, 2)) - (low_ - sma_(close_, 15, 2)))/ close_
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF159(self,name = 'alphaZS_PDF159',len1=6,maxbacklength=300):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = ((close_ - sum_(min_(low_, delay_(close_, 1)), len1))/sum_(max_(high_, delay_(close_, 1)) - min_(low_, delay_(close_, 1)), len1).replace(0,np.nan)*len1*2*24 + \
                (close_ - sum_(min_(low_, delay_(close_, 1)), len1*2))/sum_(max_(high_, delay_(close_, 1)) - min_(low_, delay_(close_, 1)), len1*2).replace(0,np.nan)*len1*24 + \
                (close_ - sum_(min_(low_, delay_(close_, 1)), len1*4))/sum_(max_(high_, delay_(close_, 1)) - min_(low_, delay_(close_, 1)), len1*4).replace(0,np.nan)*len1*24)*100/(len1*12+len1*24+len1*2*24)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]
    
    def alphaZS_PDF160(self,name = 'alphaZS_PDF160',len1=10,maxbacklength=None):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = sma_(if_(close_<=delay_(close_, 1), std_(close_, len1), 0), 20, 1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]
    
    def alphaZS_PDF161(self,name = 'alphaZS_PDF161',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = mean_(max_(max_(high_ - low_, abs_(delay_(close_, 1) - high_)), abs_(delay_(close_, 1) - low_)),len1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF162(self,name = 'alphaZS_PDF162',maxbacklength=None):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = (sma_(max_(close_ - delay_(close_, 1), self.empty(0)[-maxbacklength:]), 12, 1)/sma_(abs_(close_ - delay_(close_, 1)), 12, 1).replace(0,np.nan)*100 - \
                min_(sma_(max_(close_ - delay_(close_, 1), self.empty(0)[-maxbacklength:]), 12, 1)/sma_(abs_(close_ - delay_(close_, 1)), 12, 1).replace(0,np.nan)*100, self.empty(12)[-maxbacklength:])) /  \
                (max_(sma_(max_(close_ - delay_(close_, 1), self.empty(0)[-maxbacklength:]),12, 1)/sma_(abs_(close_ - delay_(close_, 1)), 12, 1).replace(0,np.nan)*100, self.empty(12)[-maxbacklength:] -    \
                min_(sma_(max_(close_ - delay_(close_, 1), self.empty(0)[-maxbacklength:]), 12, 1)/sma_(abs_(close_ - delay_(close_, 1)), 12, 1).replace(0,np.nan)*100, self.empty(12)[-maxbacklength:])))
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF163(self,name = 'alphaZS_PDF163',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF164(self,name = 'alphaZS_PDF164',maxbacklength=None):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = sma_((if_(close_ > delay_(close_, 1), self.empty(1)[-maxbacklength:]/(close_ - delay_(close_, 1)).replace(0,np.nan), 1) - \
                min_(if_(close_ > delay_(close_, 1), self.empty(1)[-maxbacklength:]/(close_ - delay_(close_, 1)).replace(0,np.nan), 1), self.empty(12)[-maxbacklength:]))/((high_ - low_)).replace(0,np.nan)*100, 13, 2)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF165(self,name = 'alphaZS_PDF165',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF166(self,name = 'alphaZS_PDF166',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = -20*np.power(19, 1.5)*sum_(close_/delay_(close_, 1) - 1 - mean_(close_/delay_(close_, 1)-1, 20), 20) \
        #         / np.power(19*18*sum_(close_/delay_(close_,1), 20), 2)
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF167(self,name = 'alphaZS_PDF167',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = sum_(if_(close_ - delay_(close_, 1) > 0, close_ - delay_(close_, 1), 0), len1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF168(self,name = 'alphaZS_PDF168',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = -1*vol_/mean_(vol_, len1).replace(0,np.nan)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF169(self,name = 'alphaZS_PDF169',maxbacklength=202):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = sma_(mean_(delay_(sma_(close_ - delay_(close_, 1), 9, 1), 1), 12) - mean_(delay_(sma_(close_ - delay_(close_, 1), 9, 1), 1), 26), 10, 1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]
    
    def alphaZS_PDF170(self,name = 'alphaZS_PDF170',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = (1/close_)*vol_/mean_(vol_,len1).replace(0,np.nan)*(high_*(high_-close_))/sum_(high_,len1).replace(0,np.nan)/len1 - (vwap_ - delay_(vwap_,5))
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]
    
    def alphaZS_PDF171(self,name = 'alphaZS_PDF171',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF172(self,name = 'alphaZS_PDF172',len1=10,maxbacklength=202):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        LD = delay_(low_, 1) - low_
        HD = high_ - delay_(high_, 1)
        TR = max_(max_(high_ - low_, abs_(high_ - delay_(close_, 1))), abs_(low_ - delay_(close_, 1)))
        HD0 = max_(HD, self.empty(0)[-maxbacklength:])
        LD0 = max_(LD, self.empty(0)[-maxbacklength:])
        x1 = sum_(if_(LD > HD0, LD, self.empty(0)[-maxbacklength:]), 14)*100/(sum_(TR, len1)).replace(0,np.nan)
        x2 = sum_(if_(HD > LD0, HD, self.empty(0)[-maxbacklength:]), 14)*100/(sum_(TR, len1)).replace(0,np.nan)
        alphaZS_PDF = mean_(abs_(x1 - x2)/ (x1+ x2).replace(0,np.nan)*100, len1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF173(self,name = 'alphaZS_PDF173',maxbacklength=None):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = 3*sma_(close_, 13, 2) - 2*sma_(sma_(close_, 13, 2), 13, 2) + sma_(sma_(sma_(log_(close_), 13, 2), 13, 2), 13, 2)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF174(self,name = 'alphaZS_PDF174',len1=10,maxbacklength=None):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = sma_(if_(close_>delay_(close_, 1), std_(close_, len1), 0), 20, 1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF175(self,name = 'alphaZS_PDF175',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = mean_(max_(max_(high_-low_, abs_(delay_(close_, 1) - high_)), abs_(delay_(close_, 1) - low_)), len1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF176(self,name = 'alphaZS_PDF176',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF177(self,name = 'alphaZS_PDF177',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = tsargmax_(high_, len1)*5
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF178(self,name = 'alphaZS_PDF178',maxbacklength=2):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = (close_ - delay_(close_, 1))/delay_(close_, 1)*vol_
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF179(self,name = 'alphaZS_PDF179',len1=10,maxbacklength=42):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = (corr_(vwap_, vol_, len1)) * (corr_((low_), (mean_(vol_, len1)), len1))
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]
    
    def alphaZS_PDF180(self,name = 'alphaZS_PDF180',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]
    
    def alphaZS_PDF181(self,name = 'alphaZS_PDF181',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = sum_(close_/delay_(close_, 1) - 1 - mean_(close_ - delay_(close_, 1), 20))
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF182(self,name = 'alphaZS_PDF182',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF183(self,name = 'alphaZS_PDF183',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF184(self,name = 'alphaZS_PDF184',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF185(self,name = 'alphaZS_PDF185',len1=2,maxbacklength=10):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = (-1*np.power(1-open_/close_, len1))
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF186(self,name = 'alphaZS_PDF186',len1=10,maxbacklength=302):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        LD = delay_(low_, 1) - low_
        HD = high_ - delay_(high_, 1)
        TR = max_(max_(high_ - low_, abs_(high_ - delay_(close_, 1))), abs_(low_ - delay_(close_, 1)))
        HD0 = max_(HD, self.empty(0)[-maxbacklength:])
        LD0 = max_(LD, self.empty(0)[-maxbacklength:])
        x1 = sum_(if_(LD > HD0, LD, self.empty(0)[-maxbacklength:]), len1)*100/(sum_(TR, len1)).replace(0,np.nan)
        x2 = sum_(if_(HD > LD0, HD, self.empty(0)[-maxbacklength:]), len1)*100/(sum_(TR, len1)).replace(0,np.nan)
        alphaZS_PDF1 = mean_(abs_(x1 - x2)/ (x1+ x2).replace(0,np.nan)*100, len1)
        alphaZS_PDF2 = delay_(mean_(abs_(x1 - x2)/ (x1+ x2).replace(0,np.nan)*100, len1),len1)
        alphaZS_PDF = (alphaZS_PDF1 + alphaZS_PDF2)/2.0
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF187(self,name = 'alphaZS_PDF187',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = sum_(if_(open_ <= delay_(open_, 1), 0, max_(high_-open_, open_ - delay_(open_, 1))), len1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF188(self,name = 'alphaZS_PDF188',maxbacklength=202):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = (high_-low_-sma_(high_-low_,11,2))/sma_(high_-low_,11,2).replace(0,np.nan)*100
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF189(self,name = 'alphaZS_PDF189',len1=10,maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        alphaZS_PDF = mean_(abs_(close_ - mean_(close_, len1)), len1)
        #------------output---------------------
        return [name,alphaZS_PDF.round(num_round)]
    
    def alphaZS_PDF190(self,name = 'alphaZS_PDF190',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]  
    
    def alphaZS_PDF191(self,name = 'alphaZS_PDF191',maxbacklength=22):
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        amount_=self.amount[-maxbacklength:];vwap_=self.vwap[-maxbacklength:]   
        ret_=close_.pct_change().round(num_round)
        # 
        pass
        # alphaZS_PDF = 
        # #------------output---------------------
        # return [name,alphaZS_PDF.round(num_round)]
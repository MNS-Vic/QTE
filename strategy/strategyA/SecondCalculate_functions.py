
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 22 09:18:20 2021

@author: zsqh
"""

import sys;sys.path.append(r"/home/heshuangji")
from apitool import *
import pywt

#-----------
import warnings
warnings.filterwarnings("ignore")
import datetime
#
import os
import numpy as np
import pandas as pd
import re
#
from scipy.stats import mstats,norm
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
#
import matplotlib.pyplot as plt


#%%-------通用处理-------
    
def standardize_(df,length=10,mode='rolling'):
    '''
    标准化, base on 波动率volatility
    mode='rolling','expanding'
    ###################
    df=default,因子
    mode='vol'，'mom'
    固定length=10
    #################
    '''
    if mode=='rolling':
        return_=(df-df.rolling(length).mean())/df.rolling(length).std().replace(0,np.nan)
    if mode=='expanding':
        return_=(df-df.expanding().mean())/df.expanding().std().replace(0,np.nan)
    return return_.astype(float).round(num_round)        

def quantilize1_(df,num=11,length=200):
    '''
    标准化, base on 分位数quantile
    mode='rolling'
    ###################
    df=default,因子
    
    固定length=10
    #################    
    '''
    return_=df.apply(lambda x:myqcut_ts(x,num=num,rolling=length))
    return return_.astype(float).round(num_round)        
def quantilize2_(df,num=11,length=200):
    '''
    标准化, base on 分位数quantile
    mode='expanding'
    ###################
    df=default,因子
    
    固定length=10
    #################    
    '''
    return_=df.apply(lambda x:myqcut_ts(x,num=num,expanding=length))
    return return_.astype(float).round(num_round)    
   
           
#%%-------简单规则处理-------
#-------仅限不平稳序列------需要先统一量纲
def rule1_(df,price_):
    '''
    仅限不平稳序列
    ###################
    df=default,因子
    固定price_=close_
    无参数
    #################      
    '''
    
    df=(df.pct_change()+1.0).cumprod()
    price_=(price_.pct_change()+1.0).cumprod()
    #
    return_=df-price_
    return return_.astype(float).round(num_round)
def rule2_1_(df,price_,mode='rolling',**kwargs):
    '''
    mode='rolling':length=int,mul=float

    仅限不平稳序列
    ###################
    df=default,因子
    mode='rolling','expanding'
    固定length=15,mul=1.5
    
    #################      
  
    '''
    df=(df.pct_change()+1.0).cumprod()
    price_=(price_.pct_change()+1.0).cumprod()    
    if mode=='rolling':  
        return_=df+kwargs['mul']*df.rolling(kwargs['length']).std()-price_
    if mode=='expanding':
        return_=df+kwargs['mul']*df.expanding().std()-price_
    return return_.astype(float).round(num_round)   
def rule2_2_(df,price_,mode='rolling',**kwargs):
    '''
    mode='rolling':length=int,mul=float
    同上
    '''
    df=(df.pct_change()+1.0).cumprod()
    price_=(price_.pct_change()+1.0).cumprod()        
    if mode=='rolling':  
        return_=df-kwargs['mul']*df.rolling(kwargs['length']).std()-price_
    if mode=='expanding':
        return_=df-kwargs['mul']*df.expanding().std()-price_
    return return_.astype(float).round(num_round)   
  
def rule3_1_(df,price_,delay=None): 
    '''
    delay=None,输出结果=当前状态点;否则，输出结果=全部状态持续点
    crossover_df上穿轨道price_
    ###################
    df=default,因子
    
    delay=None,5  
    #################      
      
    '''
    df=(df.pct_change()+1.0).cumprod()
    price_=(price_.pct_change()+1.0).cumprod()    
    if delay==None:
        return_=1*((df>price_) & (df.shift()<price_))
    else:
        return_=1*(df.rolling(delay).min()<=price_)*(df>price_)
 
    return return_.astype(float).round(num_round)

def rule3_2_(df,price_,delay=None): 
    '''
    delay=None,输出结果=当前状态点;否则，输出结果=全部状态持续点
    crossunder_df下穿轨道price_
    ###################
    df=default,因子
    
    delay=None,5  
    #################       
    '''
    df=(df.pct_change()+1.0).cumprod()
    price_=(price_.pct_change()+1.0).cumprod()        
    if delay==None:
        return_=1*((df<price_) & (df.shift()>price_))
    else:
        return_=1*(df.rolling(delay).max()>=price_)*(df<price_)
    return return_.astype(float).round(num_round)

def rule4_1_(df,price_,delay=1): 
    '''
    fakebreakup_
    df先上穿轨道price_,然后下穿
    ###################
    df=default,因子 
    delay=5  
    #################       
    '''
    df=(df.pct_change()+1.0).cumprod()
    price_=(price_.pct_change()+1.0).cumprod()        
    temp1=rule3_1_(df.shift(delay),price_.shift(delay),delay=delay)
    temp2=rule3_2_(df,price_,delay=delay)
    return_=1*(temp1*temp2)
    return return_.astype(float).round(num_round)
def rule4_2_(df,price_,delay=1): 
    '''
    fakebreakdown_
    df先下穿轨道price_,然后上穿
    ###################
    df=default,因子 
    delay=5  
    #################      
    '''
    df=(df.pct_change()+1.0).cumprod()
    price_=(price_.pct_change()+1.0).cumprod()        
    temp1=rule3_2_(df.shift(delay),price_.shift(delay),delay=delay)
    temp2=rule3_1_(df,price_,delay=delay)
    return_=1*(temp1*temp2)
    return return_.astype(float).round(num_round)    
def rule6_1_(df,price_,delay=1): 
    '''
    折返
    
    ''' 
    pass    
#----------无平稳限制-------------
def xFxn_(df,price_,mode='raw',length=15):
    '''    
    :X-F(Xn),Xn=price_默认为close_ 
    mode='raw':
    mode='ma':length
    mode='hl':length
    ###################
    df=default,因子 
    mode='raw'，'ma'，'hl'
    固定length=15
    #################      
    
    '''    
    df=(df.pct_change()+1.0).cumprod()
    price_=(price_.pct_change()+1.0).cumprod()        
    if mode=='raw':
        return_=df-price_
    elif mode=='ma':
        return_=df-price_.rolling(length).mean()
    elif mode=='hl':
        return_=df-0.5*(price_.rolling(length).max()+price_.rolling(length).min())
    return return_.astype(float).round(num_round)      

def macompare_(df,length1=5,length2=15):
    '''    
    双均线相减:Ma(X,n1)-Ma(X,n2)
    ###################
    df=default,因子 
    固定length1=5，length2=15
    #################      
    '''   
    return_=df.rolling(length1).mean()-df.rolling(length2).mean()
    return return_.astype(float).round(num_round)      
def mmacompare_(df,length1=3,length2=10):
    '''    
     “fast” line=“3/10 oscillator” :n1=3,n2=10,
     “slow” line ,ma(fast line,16)
    ###################
    df=default,因子 
    固定length1=3,length2=10
    #################       
    '''   
    fast=df.rolling(length1).mean()-df.rolling(length2).mean()
    slow=fast.rolling(16).mean()
    return_=fast-slow
    return return_.astype(float).round(num_round)  
def polyfit_(df,length=15,mode='ma'):
    '''    
    拟合后Xnew的一阶/二阶导
    mode='ma':length
    mode='np'(np.polyfit):length  
     “fast” line=“3/10 oscillator” :n1=3,n2=10,
     “slow” line ,ma(fast line,16)
    ###################
    df=default,因子 
    mode='ma','np'
    固定length=15
    #################       
      
    '''      
    if mode=='ma':
        dfnew=df.rolling(length).mean()       
        delt=(dfnew/dfnew.shift()-1.0)*100
        ddelt=(delt/delt.shift()-1.0)*100
        return_=1*((delt.abs()<1) & (ddelt.abs()<1)  ) 
    if mode=='np':
        coef_x2=df.rolling(length).apply(lambda x:np.polyfit(range(len(x)),x,2)[0])
        coef_x=df.rolling(length).apply(lambda x:np.polyfit(range(len(x)),x,2)[1])
        return_=1*((coef_x.abs()<1) & (coef_x2.abs()<1)  ) 
    return return_.astype(float).round(num_round)      
def hptp1_1_(df,length=15):  
    '''    
    振幅突破
    静态--相对值--NRn=振幅n日内最小
    ###################
    df=default,因子 
    固定length=15
    #################      
    '''  
    temp=df.diff().abs()
    return_=1*(temp<temp.rolling(length).min().shift())
    return return_.astype(float).round(num_round)   
def hptp1_2_(df,length=15):  
    '''    
    振幅突破
    静态--相对值--ID=波动被前日包含
    ###################
    df=default,因子 
    固定length=15
    #################      
    '''  
    return_=1*( (df>df.rolling(length).min().shift()) & (df<df.rolling(length).max().shift()))
    return return_.astype(float).round(num_round) 
def hptp1_3_1_(df,length=15,mode='atr'):  
    '''    
    振幅突破
    静态--mode='atr','pfe','hl','std'
        绝对值历史分位数--PFE/ATR：不随时间变化    
        绝对值历史分位数--HL/STD：正比于sqrt（T）
    ###################
    df=default,因子 
    mode='atr','pfe','hl','std'
    固定length=15
    #################         
    '''  
    if mode=='atr':
        value=(df-df.shift(length)).abs()
    if mode=='pfe':
        net=tsmax_(df, length)- tsmin_(df, length)
        tot=sum_(delta_(df,1).abs(),length)
        value=net/tot.replace(0.0,np.nan)
    if mode=='hl':
         value=tsmax_(df, length)- tsmin_(df, length)
    if mode=='std':
        value=df.rolling(length).std()     
    return_=value.apply(lambda x:myqcut_ts(x,num=11,expanding=length))  
    return return_.astype(float).round(num_round) 
def hptp1_3_2_(df,length=15,mode='pfe'):  
    '''    
    振幅突破
    静态--mode='atr','pfe','hl','std'
        绝对值历史分位数--PFE/ATR：不随时间变化    
        绝对值历史分位数--HL/STD：正比于sqrt（T）
    ###################
    df=default,因子 
    mode='atr','pfe','hl','std'
    固定length=15
    #################         
    '''  
    if mode=='atr':
        value=(df-df.shift(length)).abs()
    if mode=='pfe':
        net=tsmax_(df, length)- tsmin_(df, length)
        tot=sum_(delta_(df,1).abs(),length)
        value=net/tot.replace(0.0,np.nan)
    if mode=='hl':
         value=tsmax_(df, length)- tsmin_(df, length)
    if mode=='std':
        value=df.rolling(length).std()     
    return_=value.apply(lambda x:myqcut_ts(x,num=11,expanding=length))  
    return return_.astype(float).round(num_round)  
def hptp1_3_3_(df,length=15,mode='hl'):  
    '''    
    振幅突破
    静态--mode='atr','pfe','hl','std'
        绝对值历史分位数--PFE/ATR：不随时间变化    
        绝对值历史分位数--HL/STD：正比于sqrt（T）
    ###################
    df=default,因子 
    mode='atr','pfe','hl','std'
    固定length=15
    #################         
    '''  
    if mode=='atr':
        value=(df-df.shift(length)).abs()
    if mode=='pfe':
        net=tsmax_(df, length)- tsmin_(df, length)
        tot=sum_(delta_(df,1).abs(),length)
        value=net/tot.replace(0.0,np.nan)
    if mode=='hl':
         value=tsmax_(df, length)- tsmin_(df, length)
    if mode=='std':
        value=df.rolling(length).std()     
    return_=value.apply(lambda x:myqcut_ts(x,num=11,expanding=length))  
    return return_.astype(float).round(num_round) 
def hptp1_3_4_(df,length=15,mode='std'):  
    '''    
    振幅突破
    静态--mode='atr','pfe','hl','std'
        绝对值历史分位数--PFE/ATR：不随时间变化    
        绝对值历史分位数--HL/STD：正比于sqrt（T）
    ###################
    df=default,因子 
    mode='atr','pfe','hl','std'
    固定length=15
    #################         
    '''  
    if mode=='atr':
        value=(df-df.shift(length)).abs()
    if mode=='pfe':
        net=tsmax_(df, length)- tsmin_(df, length)
        tot=sum_(delta_(df,1).abs(),length)
        value=net/tot.replace(0.0,np.nan)
    if mode=='hl':
         value=tsmax_(df, length)- tsmin_(df, length)
    if mode=='std':
        value=df.rolling(length).std()     
    return_=value.apply(lambda x:myqcut_ts(x,num=11,expanding=length))  
    return return_.astype(float).round(num_round)     
def hptp2_2_(df):  
    '''    
    振幅突破
    动态--双均线/区间位置变化
    '''      
    pass
def pivotp1_1_(df):  
    '''    
    '''        
    pass
    
#%%-------人工衍生项-------    
def linep_(df):
    '''  
    linearextrapolation    
    线性外推：（当前值-前一值）+当期值
    '''    
    return_=df*2-df.shift()
    return return_.astype(float).round(num_round)      
def filter_(df,mode=1,**kwargs):
    '''  
    过滤=（初值）x过滤项
    选项
        1、过去n周期hl（需要overlap）:length,overlap.e.g.:
            filter_(df,mode=1,length=20,overlap=10)
        2、大周期均线:length1,length2
            filter_(df,mode=2,length1=80,length2=150)
        3、TB策略的adx过滤:high_.low_,close_,length,thresh
            filter_(df,mode=3,length=14,thresh=20,high=price_,low=price_,close_=price_,)
        4、TB策略的atr_filt:close_=DF,f=0.2,lenf=60
            filter_(df,mode=4,f=0.2,lenf=60,close_)

    ###################
    df=default,因子 
    mode=1：length=20,overlap=10
    mode=2：length1=80,length2=150
    mode=3：length=14，thresh=20
    mode=4：f=0.2,lenf=60
    
    #################       
    '''       
    if mode==1:
        filt1=df.rolling(kwargs['length']).max().shift(kwargs['overlap'])
        filt2=df.rolling(kwargs['length']).min().shift(kwargs['overlap'])
        result_=1*(df>filt1)-1*(df<filt2)
    if mode==2:
        filt=1-2*(df.rolling(kwargs['length1']).mean()>df.rolling(kwargs['length2']).mean())
        result_=df*filt
    if mode==3:
        temp=basefunc('ADX',high_=kwargs['high_'],low_=kwargs['low_'],close_=kwargs['close_'],params={'timelength':kwargs['length']})
        dx=pd.DataFrame(temp,index=kwargs['open_'].columns,columns=kwargs['open_'].index).T 
        filt=1*(dx>kwargs['thresh'])
        result_=df*filt
    if mode==4:
        temp=df*0
        for i in range(15):
            temp+=abs(kwargs['close_']-kwargs['close_'].shift(i+1))
        temp=temp/15   
        filt=1*(temp>=(kwargs['f']*tsmax_(temp,kwargs['lenf'])+(1-kwargs['f'])*tsmin_(temp,kwargs['lenf'])))
        result_=df*filt
    return_=result_
    return return_.astype(float).round(num_round)   
        
def kpcompare_(df,kp):
    '''  
    跟关键价格相比
    kp=todayo_,
    
    ''' 
    pass
def stlagg_(df):
    '''  
    短周期向长周期切片聚合
    Short length to long length aggregation
    ''' 
    pass
def nonst_mdd(df):
    '''  
    为非平稳时序，计算mdd
    mode='rolling','expanding'
    '''  
    temp=df.median(axis=1)
    price_=df if temp.iloc[-1]>temp.iloc[1] else -df
    return_=(price_.expanding().max()-price_)/price_.replace(0,np.nan)
    return return_.astype(float).round(num_round)         
def st_mdd(df):
    '''  
    为平稳时序，计算mdd
    mode='rolling','expanding'
    '''      
    return_=nonst_mdd(df.cumsum())
    return return_.astype(float).round(num_round)   
#%%-------Others-------    
def HTfrequency_(df,**kwargs):
    '''
        Hilbert频域视角
    ###################
        mode=1:'HT_DCPERIOD'
        mode=2:'HT_DCPHASE'
        mode=3:'HT_TRENDMODE'
        
    '''
    if mode==1:           
        temp=basefunc(name='HT_DCPERIOD',close_=df)
        return_=pd.DataFrame(temp,index=df.columns,columns=df.index).T  
    if mode==2:             
        temp=basefunc(name='HT_DCPHASE',close_=df)
        return_=pd.DataFrame(temp,index=df.columns,columns=df.index).T  
    if mode==3:             
        temp=basefunc(name='HT_TRENDMODE',close_=df)
        return_=pd.DataFrame(temp,index=df.columns,columns=df.index).T  
    return return_.astype(float).round(num_round)   

# def   
if __name__ == '__main__':
    pass
    #
    filepath = r'/home/heshuangji/Data/DATA_DAY_WEIGHT'
    open_ = pd.read_csv(filepath + '/Open.csv', header=0, parse_dates=True, index_col=0).dropna(how='all') \
            .fillna(method='ffill').fillna(method='bfill')[['RB']]
    high_ = pd.read_csv(filepath + '/High.csv', header=0, parse_dates=True, index_col=0).dropna(how='all') \
            .fillna(method='ffill').fillna(method='bfill')[['RB']]
    low_ = pd.read_csv(filepath + '/Low.csv', header=0, parse_dates=True, index_col=0).dropna(how='all') \
            .fillna(method='ffill').fillna(method='bfill')[['RB']]
    close_ = pd.read_csv(filepath + '/Close.csv', header=0, parse_dates=True, index_col=0).dropna(how='all') \
            .fillna(method='ffill').fillna(method='bfill')[['RB']]
    vol_ = pd.read_csv(filepath + '/Vol.csv', header=0, parse_dates=True, index_col=0).dropna(how='all') \
            .fillna(method='ffill').fillna(method='bfill')[['RB']]
    

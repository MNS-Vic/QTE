

import sys;sys.path.append(r"D:\蓝天LT_Research")
from apitool import *
from ml_functions import *
import warnings
warnings.filterwarnings("ignore")
from queue import Queue
import pandas as pd
import numpy as np
import time
from statsmodels.tsa.stattools import adfuller
from mlfinlab.features.fracdiff import frac_diff_ffd
from mlfinlab.util.multiprocess import mp_pandas_obj
import os
import pickle
from sklearn import metrics
from sklearn.metrics import log_loss, accuracy_score
from sklearn.tree import DecisionTreeClassifier,DecisionTreeRegressor
from sklearn.tree import plot_tree,export_text,export_graphviz
from sklearn.ensemble import BaggingClassifier,BaggingRegressor

#====
data1=get_mydata(mode='FQWEIGHT')
data2=get_mydata(mode='ORIGIN')
localpath=r'D:\蓝天LT_Research\FactorResearch\Temp'
#
temp=((data1['open'].shift(-2)-data1['open'].shift(-1))/data2['open'].shift(-1))
ret=temp[temp.index<='2023-05-31'].stack(dropna=False)  
#
newret,_=get_mqts(ret.unstack(),name='yqts',rolling=False)     
#====
# localpath=r'D:\蓝天LT_Research\FactorResearch\MrZhang'
# ret=pd.DataFrame()
# ret[1]=pd.read_csv(r'D:\蓝天LT_Research\FactorResearch\MrZhang\y.csv',index_col=0).stack(dropna=False)  
# newret=pd.DataFrame(columns=ret.columns)
# for l in ret.columns:
#     print(l)
#     res1,_=get_mqts(ret[l].unstack(),name='yqts',rolling=False)     
#     newret[l]=res1
# newret.to_csv(r'D:\蓝天LT_Research\FactorResearch\MrZhang\newret_qtsy.csv')
# newret=pd.read_csv(r'D:\蓝天LT_Research\FactorResearch\MrZhang\newret_qtsy.csv')
# newret.index=pd.MultiIndex.from_frame(newret[newret.columns[:2]])
# newret=newret.drop(newret.columns[:2],axis=1) 
#=====
print('data preparing...')
#=====
def calc_mic_single(name,tempx,tempy,alpha,timerange=range(2013,2024)):
    res=pd.DataFrame(index=timerange,columns=tempx.columns)
    for t in tempx.columns:
        tempx_=tempx[t]
        tempdf=pd.DataFrame([tempx_,tempy[t]],index=['x','y']).T.dropna()
        for y in res.index:
            startd=str(y)+'-01-01';endd=str(y)+'-12-31'
            try:
                tempdf2=tempdf.loc[~((startd<=tempdf.index) & (tempdf.index<=endd))]               
                if alpha in ['pearson','kendall']:
                    res.loc[y,t]=tempdf2.corr(method=alpha).iloc[0][1]
                else:  
                    if tempdf2.shape[0]>500:
                        res.loc[y,t]=micfunc(tempdf2['x'],tempdf2['y'],alpha=alpha)
            except:
                continue 
    return name,res
def calc_mic_all(name,x,newret,alpha,timerange=range(2013,2024)):
    res=pd.DataFrame(index=[1,2,5,15],columns=timerange)  
    for l in res.index:
        tempdf=pd.DataFrame([x.unstack().rolling(l).mean().stack(dropna=False),newret],index=['x','y']).T.dropna()
        for y in res.columns:
            startd=str(y)+'-01-01';endd=str(y)+'-12-31'
            try:
                tempdf2=tempdf.loc[idx[tempdf.index.levels[0][~((startd<=tempdf.index.levels[0]) & (tempdf.index.levels[0]<=endd))],:],].astype(float).dropna()     
                if alpha in ['pearson','kendall']:
                    res.loc[l,y]=tempdf2.corr(method=alpha).iloc[0][1]
                else:
                    res.loc[l,y]=micfunc(tempdf2['x'],tempdf2['y'],alpha=alpha)
            except:
                continue                     
    return name,res
def find(name,clusterdict,outmic):    
    for k,v in clusterdict.items():
        if name in v:
            return outmic[v].sort_values()

if __name__ == '__main__':
   
    corr=pd.read_csv(r'%s\newdf1_corr(pearson).csv'%(localpath),index_col=0)  
    factortest=pd.read_csv(r'%s\Factortest1_1.csv'%(localpath),index_col=0)


    #修正0：少数据权重
    temp=data1['close'].notna().sum()
    weight0=(temp/1000).apply(lambda x:min(1,x)).round(1)
    #修正1：指定品种权重
    # weight1=data2['amt'].mean()/data2['amt'].mean().max()
    weight1=pd.Series(1,data2['amt'].columns)
    tempw1={'s1_1':1, 's1_2':1, 's1_3':1, 's2_1':1, 's2_2':1, 's2_3':1, 's2_4':1, 's2_5':1,
            's2_6':1, 's3_1':1, 's3_2':0.8, 's3_3':1, 's4_1':1, 's4_2':1, 's4_3':0.5, 's4_4':0.2, 's5_1':1}
    for n in weight1.index:
        for k,v in get_sector(mode='sub').items():
            if n in v:break
        weight1[n]=tempw1[k]
    #修正2：减法
    weight2=data1['close'].notna().sum().apply(lambda x:fitmic(x/100))#    
    #%%生成mic 
    
    #----newdf1的ic值生成&评估
    import polars as pl
    temp=pl.read_csv(r'%s\newdf1_last.csv'%(localpath),encoding='gbk') 
    dfx=temp.to_pandas()
    # dfx=pd.read_csv(r'%s\newdf1_last.csv'%(localpath),engine='c')  
    # dfx=pd.read_csv(r'%s\newdf1_handlast.csv'%(localpath))  
    dfx.index=pd.MultiIndex.from_frame(dfx[dfx.columns[:2]])
    dfx=dfx.drop(dfx.columns[:2],axis=1).loc[:,:]    
    # #  
    alpha=0.5#[0.3,0.5,'kendall']:
    fpath=r'%s\newdf1_mic(alpha%s)'%(localpath,alpha)
    MkDir(fpath)  
    #----计算全品种stack后的mic
    jobs=[]
    for n in dfx.columns:   
        print(n)
        job={'func':calc_mic_all,'name':n,'x':dfx[n],'newret':newret,'alpha':alpha}
        jobs.append(job)         
    executor=ProcessPoolExecutor() 
    for i,res in enumerate(executor.map(expandCall,jobs)):         
    # for job in jobs:
    #     res=expandCall(job)         
        print(res[0])         
        res[1].to_csv( fpath+'\%s.csv'%(res[0]))
    #----计算单品种的mic
    # for l in [1,2,5,15]:           
    #     print(l)
    #     tempy=ret.unstack()
    #     #------------------------          
    #     MkDir(r'%s\Mic_Value(1_alpha%s)\yd%s'%(localpath,alpha,l))        
    #     jobs=[]
    #     for n in dfx.columns: 
    #         temp=dfx[n].unstack().rolling(l).mean()
    #         job={'func':calc_mic_single,'tempx':temp,'tempy':tempy,'name':n,'alpha':alpha,'timerange':range(2012,2023)}
    #         jobs.append(job)         
    #     executor=ProcessPoolExecutor() 
    #     for i,res in enumerate(executor.map(expandCall,jobs)):  
    #     # for job in jobs:
    #     #     res=expandCall(job)           
    #         print(res[0])
    #         res[1].to_csv(r'%s\Mic_Value(1_alpha%s)\yd%s\%s.csv'%(localpath,alpha,l,res[0]))
    #     executor.shutdown(True)
        #------------------------
        # MkDir(r'D:\蓝天LT_Research\FactorResearch\Temp\Mic_Value(fd)\yd%s'%(l))
        # jobs=[]
        # filepath=r'D:\蓝天LT_Research\FactorResearch\Temp\FactorValue_fd%s/'%(l)
        # for f in os.listdir(filepath): 
        #     temp=pd.read_csv(filepath+f,index_col=0)
        #     job={'func':calc_mic_single,'tempx':temp,'tempy':tempy,'name':f[:-4]}
        #     jobs.append(job)         
        # executor=ProcessPoolExecutor() 
        # for i,res in enumerate(executor.map(expandCall,jobs)):                
        #     res[1].to_csv(r'D:\蓝天LT_Research\FactorResearch\Temp\Mic_Value(fd)\yd%s\%s.csv'%(l,res[0]))
        # executor.shutdown(True)            


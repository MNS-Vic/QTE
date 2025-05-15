#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 12 16:12:26 2022

@author: heshuangji
"""

from __future__ import division
import warnings
import sys;sys.path.append(r"D:\蓝天LT_Research")
from apitool import *
from ml_functions import *
warnings.filterwarnings("ignore")
from queue import Queue
import pandas as pd
import numpy as np
import time
from statsmodels.tsa.stattools import adfuller
from mlfinlab.features.fracdiff import frac_diff_ffd
from mlfinlab.util.multiprocess import mp_pandas_obj
import os
from sklearn import metrics
from sklearn.metrics import log_loss, accuracy_score
from sklearn.tree import DecisionTreeClassifier,DecisionTreeRegressor
from sklearn.tree import plot_tree,export_text,export_graphviz
from sklearn.ensemble import BaggingClassifier,BaggingRegressor
import pickle

#
localpath=r'D:\蓝天LT_Research\FactorResearch\Temp'
# localpath=r'D:\蓝天LT_Research\FactorResearch\MrZhang'

def factorvalue_check():#----检查当日更新与历史值是否一致
    from sklearn.metrics import mean_squared_error  as  mse     
    p1=r'/home/heshuangji/Data/FactorValue'
    p2=r'/home/heshuangji/Data/FactorValueLast'
    fname='/AlphasZS_tal'
    #
    files=os.listdir(p2+fname)
    names=[]
    for n in files:
        names.append([n,n.split('@')[0]])
    dfnames=pd.DataFrame(names)
    grouped=dfnames.groupby(1)
    out=[]
    for k,v in grouped.groups.items(): 
        flist=grouped.get_group(k)[0]
        for f in flist:
            try:
                files1=os.listdir(p1+fname)      
                temp='@'.join(f.split('@')[:2])
                f1=list(filter(lambda x:(temp in x) and ('log') not in x 
                                    and f.split('@')[1]==x.split('@')[1],files1))[0]            
                print(f,f1)
                df1=pd.read_csv(p1+fname+'/'+f1,index_col=0).drop(['name', 'BeginOfBar'],axis=1)
                df2=pd.read_csv(p2+fname+'/'+f,index_col=0).drop(['name', 'BeginOfBar'],axis=1)
                df1=df1.replace(np.inf,np.nan).replace(-np.inf,np.nan).fillna(0)
                df2=df2.replace(np.inf,np.nan).replace(-np.inf,np.nan).fillna(0)
                out.append([f,f1,mse(df1.iloc[-1],df2.iloc[-1])])
            except:
                out.append([f,'',1.0])
    out=pd.DataFrame(out)
    a=out[out[2].abs()>1e-6].sort_index()
#%%----手工动量因子生成
MkDir(r'D:\蓝天LT_Research\FactorResearch\Temp\FactorValue\AlphaHand_')
result=pd.DataFrame()
for name in     ['mom','band','hurst_pfe','adx','tsv','ttm','vpin',
                 'rsi','rsv','skewness','kurtosis','obvm','longterm_dma','longterm_newhl'] :
    print(name)
    for length in [5,20,40,60]:    
        temp=get_handfactor(data1['close'], data2['vol'],name, length)
        temp.to_csv(r'D:\蓝天LT_Research\FactorResearch\FactorValue\AlphaHand_\alphaHand_%s@%s.csv'%(name,length))
        result['alphaHand_%s@%s'%(name,length)]=temp.stack(dropna=False)      




if __name__ == '__main__':
    checktype=['RB','TA','NI','M','J','SC','CU','CF']#重点选择8个品种
#%%----Nan & Uni & adftest

    filepath=r'%s\FactorValue/'%(localpath)
    files=os.listdir(filepath)
    factors=[]
    for f in files:
        lpath=filepath+f
        factors.extend([lpath+'/'+x for x in os.listdir(lpath)])
    result=[]
    for i in range(len(factors)):
        l=factors[i]
        print(l)
        try:
            df=pd.read_csv(l,index_col=0).replace(np.inf,np.nan).replace(-np.inf,np.nan)
            # df=df.dropna(how='all')
            try:
                df=df.drop(['name','BeginOfBar'],axis=1)
            except:
                pass
        except:
            continue
        res1=NanCheck(df, benchmark=0.74,thresold= 0.6)#nan超过6成才剔除
        if res1==0:
            result.append([l,res1,np.nan,np.nan])
        else:
            res2=UniqueCheck(df)
            adfv=[]
            for n in checktype:#重点选择8个品种
                _,tempadfv=adf_test(df,bench=n,maxlag=1,thresh=-5)
                adfv.append(tempadfv)
            result.append([l,res1,res2,adfv])
    out=pd.DataFrame(result)
    out.columns=['name','nan','uni','adfv']
    out.index=[x.split('/')[-1][:-4] for x in out['name']]
    out.to_csv(r'%s\Factortest1_1.csv'%(localpath))


#%%----[Notused]针对不同yreturn周期生成对应的新因子
    #max_d>0表示正常差分,<0表示cumsum后再差分
    out=pd.read_csv(r'%s\Factortest1_1.csv'%(localpath),index_col=0)
    check=out.dropna()
    check.index=[x.split('/')[-1][:-4] for x in check['name']]
    names=check[check['nan']>0]
    #
    fdvalue=pd.DataFrame(index=names.index,columns=['d1','d2','d5','d15'])#y_return d1,5,15三个周期的
    for d in [1,2,5,15]:
        MkDir(r'%s\FactorValue_fd%s'%(localpath,d))
    #
    dfx=pd.read_csv(r'%s\newdf1_last.csv'%(localpath))  
    dfx.index=pd.MultiIndex.from_frame(dfx[dfx.columns[:2]])
    dfx=dfx.drop(dfx.columns[:2],axis=1).loc[:,:]          
    for name in dfx.columns:       
        temp=dfx[name].unstack()
        #handle极值
        temp=HandleInf(temp,infnan=True)
        #
        exec('adfvlist=%s'%(out.loc[n.split('-MR')[0],'adfv']).replace('nan','np.nan'))
        adfv=pd.Series(adfvlist).mean()

        threshadv={1:35,2:25,5:15,15:10}
        for d in [1,2,5,15]:         
            try:
                # d2    
                if adfv>-threshadv[d]*0.75:
                    max_d,tempout=autofracdiff_(temp, adfthresh=-threshadv[d],maxlag=1, thresh=0.01,fast=True,bench='RB')
                    flag='fd'
                    fdvalue.loc[name,'d%s'%(d)]=max_d
                elif adfv<-threshadv[d]*1.25:
                    max_d,tempout=autofracdiff_(temp.cumsum(), adfthresh=-threshadv[d],maxlag=1, thresh=0.01,fast=True,bench='RB')
                    flag='cumfd'
                    fdvalue.loc[name,'d%s'%(d)]=-max_d
                else:
                    tempout=temp
                    flag='nonfd'
                    fdvalue.loc[name,'d%s'%(d)]=0            
            except:
                tempout=temp
                flag='cantfd'
                # fdvalue[name]=np.nan
            print(d,flag)
            tempout.to_csv(r'D:\蓝天LT_Research\FactorResearch\Temp\FactorValue_fd%s\%s_%s.csv'%(d,flag,name))
    fdvalue.to_csv(r'D:\蓝天LT_Research\FactorResearch\Temp\fdvalue.csv')            
            
            
    
    
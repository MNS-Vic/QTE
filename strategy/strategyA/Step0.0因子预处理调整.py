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
#============================================
def get_step3(l,filpath,standardize=False):
    '''
    1、处理inf极值
    2、压缩处理
    3、是否标准化
    '''
    try:
        temp=pd.read_csv(l,index_col=0) 
    except:
        temp=pd.read_csv(filpath+l,index_col=0) 
    #step1：处理inf极值
    temp=HandleInf(temp,infnan=True)
    #
    try:
        temp=temp.drop(['name','BeginOfBar'],axis=1)
    except:
        pass
    # temp=temp.loc[temp.index[temp.index<='2021-10-14'],:]
    temp=temp.loc[~temp.index.duplicated(),:]
    name=l.split('/')[-1][:-4]
    
    if len(temp.unstack().unique())>50:#分母为0需要处理           
        con1=(temp.max()-temp.min()).max()>1e6#“最大-最小值”间距过大
        con2=(temp.abs().quantile(0.99)/temp.abs().quantile(0.01).replace(0,1)).max()>1e5#保留并压缩此类因子
        con3=(temp.abs().max()/temp.abs().median().replace(0,1)).max()>1e3#
        con4=(temp.abs().max()/temp.abs().mean().replace(0,1) ).max()>1e3#过滤掉此类因子
        con5=temp.kurt().abs().max()>1e2
        # flag=con1 & con2
        if con1 & con3 & con4 & con5:return #过滤掉此类因子   
        #step2：压缩处理
        if con1 & (con2 | con3 |con4):                             
            temp2,value=myqt_transform(temp,thresh=0.99)   #压缩毛刺极值             
            tempname=name+'-MR'     
            print(name,'-MR')
        else:
            temp2=temp
            tempname=name  
        #step3：是否标准化      
        if standardize:
            temp3=temp2.apply(lambda x:standardize_ts(x,method='median',expanding=500))
        else:
            temp3=temp2
        #final
        res= temp3.stack(dropna=False)
        res.name=tempname
    else:
        res=temp.stack(dropna=False)
        res.name=name   
    print(name,res.size,temp.columns[0])
    return res

 
if __name__ == '__main__':
    checktype=['RB','TA','NI','M','J','SC','CU','CF']
#%% newdf0：生成(部分因子压缩‘-MR’):Make Multi_DF & Corr矩阵
    factortest=pd.read_csv(r'%s\Factortest1_1.csv'%(localpath),index_col=0)
    #----get_step3{处理inf极值 ,压缩处理}-->Multi_DF 
    # jobs=[]
    # for n in factortest.index:
    #     l=factortest.loc[n,'name']
    #     job={'func':get_step3,'l':l,'filpath':''}
    #     jobs.append(job)                    
    # dfx=[]
    # for job in jobs:  
    #     res=expandCall(job)
    #     dfx.append(res)   
    # dfx0=pd.concat(dfx,axis=1)
    # dfx0.dropna(how='all').dropna(how='all',axis=1).to_csv(r'%s\newdf0_last.csv'%(localpath))      
    #----生成并输出原始Corr矩阵
    # dfx=pd.read_csv(r'%s\newdf0_last.csv'%(localpath))  
    # dfx.index=pd.MultiIndex.from_frame(dfx[dfx.columns[:2]])
    import polars as pl
    temp=pl.read_csv(r'%s\newdf0_last.csv'%(localpath),encoding='gbk') 
    dfx=temp.to_pandas()
    dfx.index=pd.MultiIndex.from_frame(dfx[dfx.columns[:2]])  
    dfx=dfx.drop(dfx.columns[:2],axis=1).loc[:,:]  
    dfx=dfx.loc[idx[dfx.index.levels[0][dfx.index.levels[0]<'2023-06-01'],:],:]
    print('preparing done...')
    b=dfx.corr(method='kendall')
    b.to_csv(r'%s\newdf0_corr.csv'%(localpath))            
    #使用Dask
    # import dask.dataframe as dd
    # ddf = dd.from_pandas(dfx, npartitions=16) 
    # b = ddf.map_partitions(lambda df: df.apply(lambda x: df.corrwith(x, method='kendall'), axis=0)).compute(scheduler='processes')
    # b.to_csv(r'%s\newdf0_corr.csv'%(localpath))            
    #----newdf0：Corr相关系数矩阵生成，剔除高相关0.95因子后合并  
    corr=pd.read_csv(r'%s\newdf0_corr.csv'%(localpath),index_col=0)  
    usedlist=get_usedlist(corr,factortest)
    #
    # handfactors=list(map(lambda x:x[:-4],os.listdir(r'D:\蓝天LT_Research\FactorResearch\Temp\FactorValue\AlphaHand_')))
    # usedlist.extend(handfactors)
    # usedlist=list(set(usedlist))
#%% newdf1：X变量数据调整，包含两种方案，rolling&expanding
    #获得MultiDF&相关系数corr1：针对不同品种&不同时段（剔除高相关0.95因子后）
    dfx=dfx[usedlist].astype(float)
    #
    res=pd.DataFrame(index=dfx.columns,columns=['judge0','judge1','judge2','judge3','judge4'])
    for n in dfx.columns:
        print(n)
        temp=dfx[n].unstack()
        res1=temp.mean().sort_values()
        res2=temp.std().sort_values()
        res3=temp.skew().sort_values()
        res4=temp.kurt().sort_values()
        #      
        exec('adfv=%s'%(factortest.loc[n.split('-MR')[0],'adfv']).replace('nan','np.nan'))
        judge0=pd.Series(adfv).mean()
        judge1=len(dfx[n].dropna().unique())#(res1.max()-res1.min())/(res1.quantile(0.75)-res1.quantile(0.25))
        try:#输出正常judge1，2        
            judge2=(res2.max()-res2.min())/(res2.quantile(0.75)-res2.quantile(0.25))
        except:#输出非正常judge1，2
            judge2=np.nan        
        judge3=(res1.max()-res1.min())/(max(1e-6,res2.median()))
        judge4=(res4.max()-res4.min())
        # plt.figure()
        # plt.subplots_adjust(wspace=0,hspace=0)  
        # ax1=plt.subplot(2,2,1);plt.title('1')
        # ax2=plt.subplot(2,2,2);plt.title('2')
        # ax3=plt.subplot(2,2,3);plt.title('3')
        # ax4=plt.subplot(2,2,4);plt.title('4')
        # res1.round(2).sort_values().plot(ax=ax1)
        # res2.round(2).sort_values().plot(ax=ax2)
        # res3.round(2).sort_values().plot(ax=ax3)
        # res4.round(2).sort_values().plot(ax=ax4)
        res.loc[n,:]=[judge0,judge1,judge2,judge3,judge4]
    res=res.astype(float).round(2)
    #----检查绘图
    # a=res.loc[list(filter(lambda x:'alphaHand' in x ,usedlist)),:]
    # #
    # for n in res[ filt1 & ( (filt2 | filt3)) ].sort_values('judge0').index:      
    #     print(n,res.loc[n,:])
    #     temp=dfx[n].unstack()
    #     temp[['RB','TA','NI','M','J','SC','CU','CF']].plot(legend=False)
    #     plt.title(n)
    #     plt.show()
    #     #
        # for t_ in checktype:
        #     temp[t_].hist(bins=20,alpha=0.25,legend=True)     
        #     plt.title(n)
    #----三重过滤条件：unique数，std分布&mean分布+kurt分布，非平稳的mean分布
    filt1=res['judge1']>51
    filt2=(res['judge2']>5) | (( (res['judge2']>3)) & ( (res['judge4']>15) | (res['judge3']>3) ) ) | (res['judge2']*res['judge4']>120) 
    filt3= (res['judge0']>-5) & (res['judge3']>1.5)   
    jobs=[]
    for n in  res[ (filt1 & (filt2 | filt3)) ].sort_values('judge0').index:     
        print(n,'mp_rocess')
        temp=dfx[n].unstack()
        job={'func':get_mqts,'temp':temp,'name':n}
        jobs.append(job)           
    dfx2=[]
    #  
    executor=ProcessPoolExecutor() 
    for i,temp in enumerate(executor.map(expandCall,jobs)):  
    # for job in jobs:  
        # temp=expandCall(job)
        dfx2.append(temp[0])
        dfx2.append(temp[1])
    executor.shutdown(True)
    # #
    for n in res[ ~(filt1 & (filt2 | filt3)) ].sort_values('judge0').index:
        print(n,'sp_rocess')
        temp=dfx[n]
        dfx2.append(temp)
    # #
    dfx02=pd.concat(dfx2,axis=1)
    dfx02.dropna(how='all').dropna(how='all',axis=1).to_csv(r'%s\newdf1_last.csv'%(localpath))  
    #----newdf1的相关性输出
    # import swifter
    # dfx2=pd.read_csv(r'%s\newdf1_last.csv'%(localpath))  
    # dfx2.index=pd.MultiIndex.from_frame(dfx2[dfx2.columns[:2]])
    # dfx2=dfx2.drop(dfx2.columns[:2],axis=1).loc[:,:]   
    # corr = dfx2.swifter.apply(lambda x: dfx2.corrwith(x,method='pearson'), axis=0)
    corr=dfx02.corr(method='pearson')
    corr.to_csv(r'%s\newdf1_corr(pearson).csv'%(localpath))         
    #----多进程相关性
    # method='pearson'
    # jobs=[]
    # for col_name in dfx2.columns: 
    #     job={'func':calculate_corr_with_every_other_column,'df':dfx2,'col_name':col_name,'method':method}
    #     jobs.append(job)         
    # multiprocessing.set_start_method('spawn')
    # executor=ProcessPoolExecutor() 
    # result=[]
    # for i,res in enumerate(executor.map(expandCall,jobs)):                
    #     result.append(res)
    # executor.shutdown(True)
    # b=pd.DataFrame({k: v for d in result for k, v in d.items()}).T 
    # b.to_csv(r'%s\newdf1_corr(%s).csv'%(localpath,method))  
    # #






            
            
            
    
    
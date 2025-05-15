# -*- coding: utf-8 -*-
"""
Created on Tue Jul 30 16:02:38 2019

@author: ShuangJi.He
"""


from apitool import *
#-----------
import pandas as pd
import numpy as np
from talib import abstract
 
#
class AlphasZS_tal(object):
    def __init__(self,open_,high_,low_,close_,vol_,amount_,opt_,vwap_):
        #函数与self,name的对应表    mya.open = self.open
        self.open = open_.fillna(method='ffill').dropna(how='all',axis=1)
        self.high = high_.fillna(method='ffill').dropna(how='all',axis=1)
        self.low = low_.fillna(method='ffill').dropna(how='all',axis=1)
        self.close = close_.fillna(method='ffill').dropna(how='all',axis=1)
        self.vol= vol_.fillna(method='ffill').dropna(how='all',axis=1)
        self.opt=opt_.fillna(method='ffill').dropna(how='all',axis=1)
            
        #
        self.col0=open_.columns#原始的columns
        self.col1=self.open.columns.intersection(self.high.columns).intersection(self.low.columns).intersection(self.close.columns)\
                    .intersection(self.vol.columns)#实际使用的columns，保证所有DF都是满填的
        self.open =self.open.loc[:,self.col1]
        self.high =self.high.loc[:,self.col1]
        self.low =self.low.loc[:,self.col1]
        self.close =self.close.loc[:,self.col1]
        self.vol=self.vol.loc[:,self.col1]
        self.opt=self.opt.loc[:,self.col1]
        self.empty=lambda n:open_.applymap(lambda x:n)
                
    def basefunc(self,name,open_,high_,low_,close_,vol_,params=None):        
        func=abstract.Function(name)           
        if params!=None:func.parameters =params  
        out=[]
        for n in open_.columns:
            inputs = {
                'open':   open_[n].values,
                'high':   high_[n].values,
                'low':    low_[n].values,
                'close':  close_[n].values,
                'volume':  vol_[n].values
            }       
            result = func.run(inputs)
            out.append(result)
        return out
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~自定义alpha~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def alphatal_1(self,name = 'alphatal_1',mul=1 ,maxbacklength=None):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])   
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_2(self,name = 'alphatal_2',mul=1 ,maxbacklength=None):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)               
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_3(self,name = 'alphatal_3',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_4(self,name = 'alphatal_4',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]  
    def alphatal_5(self,name = 'alphatal_5',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)

        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_6(self,name = 'alphatal_6',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_7(self,name = 'alphatal_7',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_8(self,name = 'alphatal_8',mul=1 ,maxbacklength=None):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]    
    def alphatal_9(self,name = 'alphatal_9',mul=1 ,maxbacklength=None):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_10(self,name = 'alphatal_10',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_11(self,name = 'alphatal_11',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_12(self,name = 'alphatal_12',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]  
    def alphatal_13(self,name = 'alphatal_13',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_14(self,name = 'alphatal_14',mul=1 ,maxbacklength=None):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_15(self,name = 'alphatal_15',mul=1 ,maxbacklength=None):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_16(self,name = 'alphatal_16',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]  
    def alphatal_17(self,name = 'alphatal_17',mul=1 ,maxbacklength=None):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_18(self,name = 'alphatal_18',mul=1 ,maxbacklength=None):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_19(self,name = 'alphatal_19',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_20(self,name = 'alphatal_20',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]  
    def alphatal_21(self,name = 'alphatal_21',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_22(self,name = 'alphatal_22',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_23(self,name = 'alphatal_23',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_24(self,name = 'alphatal_24',mul=1 ,maxbacklength=None):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_25(self,name = 'alphatal_25',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]  
    def alphatal_26(self,name = 'alphatal_26',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_27(self,name = 'alphatal_27',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_28(self,name = 'alphatal_28',mul=1 ,maxbacklength=None):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]  
    def alphatal_29(self,name = 'alphatal_29',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_30(self,name = 'alphatal_30',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_31(self,name = 'alphatal_31',mul=1 ,maxbacklength=None):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_32(self,name = 'alphatal_32',mul=1 ,maxbacklength=None):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]  
    def alphatal_33(self,name = 'alphatal_33',mul=1 ,maxbacklength=None):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_34(self,name = 'alphatal_34',mul=1 ,maxbacklength=None):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_35(self,name = 'alphatal_35',mul=1 ,maxbacklength=None):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_36(self,name = 'alphatal_36',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]  
    def alphatal_37(self,name = 'alphatal_37',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_38(self,name = 'alphatal_38',mul=1 ,maxbacklength=None):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_39(self,name = 'alphatal_39',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_40(self,name = 'alphatal_40',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_41(self,name = 'alphatal_41',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_42(self,name = 'alphatal_42',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]  
    def alphatal_43(self,name = 'alphatal_43',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_44(self,name = 'alphatal_44',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_45(self,name = 'alphatal_45',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_46(self,name = 'alphatal_46',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]  
    def alphatal_47(self,name = 'alphatal_47',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_48(self,name = 'alphatal_48',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_49(self,name = 'alphatal_49',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_50(self,name = 'alphatal_50',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_51(self,name = 'alphatal_51',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_52(self,name = 'alphatal_52',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]  
    def alphatal_53(self,name = 'alphatal_53',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_54(self,name = 'alphatal_54',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_55(self,name = 'alphatal_55',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_56(self,name = 'alphatal_56',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]  
    def alphatal_57(self,name = 'alphatal_57',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_58(self,name = 'alphatal_58',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_59(self,name = 'alphatal_59',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]    
    def alphatal_60(self,name = 'alphatal_60',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_61(self,name = 'alphatal_61',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_62(self,name = 'alphatal_62',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]  
    def alphatal_63(self,name = 'alphatal_63',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_64(self,name = 'alphatal_64',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_65(self,name = 'alphatal_65',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_66(self,name = 'alphatal_66',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]  
    def alphatal_67(self,name = 'alphatal_67',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_68(self,name = 'alphatal_68',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_69(self,name = 'alphatal_69',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]  
    def alphatal_70(self,name = 'alphatal_70',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_71(self,name = 'alphatal_71',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_72(self,name = 'alphatal_72',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]  
    def alphatal_73(self,name = 'alphatal_73',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_74(self,name = 'alphatal_74',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_75(self,name = 'alphatal_75',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_76(self,name = 'alphatal_76',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]  
    def alphatal_77(self,name = 'alphatal_77',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_78(self,name = 'alphatal_78',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_79(self,name = 'alphatal_79',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_80(self,name = 'alphatal_80',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_81(self,name = 'alphatal_81',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_82(self,name = 'alphatal_82',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]  
    def alphatal_83(self,name = 'alphatal_83',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_84(self,name = 'alphatal_84',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_85(self,name = 'alphatal_85',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_86(self,name = 'alphatal_86',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]  
    def alphatal_87(self,name = 'alphatal_87',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_88(self,name = 'alphatal_88',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_89(self,name = 'alphatal_89',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_90(self,name = 'alphatal_90',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_91(self,name = 'alphatal_91',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_92(self,name = 'alphatal_92',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]  
    def alphatal_93(self,name = 'alphatal_93',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_94(self,name = 'alphatal_94',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_95(self,name = 'alphatal_95',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_96(self,name = 'alphatal_96',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]  
    def alphatal_97(self,name = 'alphatal_97',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_98(self,name = 'alphatal_98',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_99(self,name = 'alphatal_99',mul=1 ,maxbacklength=5):

        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_100(self,name = 'alphatal_100',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_101(self,name = 'alphatal_101',mul=1 ,maxbacklength=None):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_102(self,name = 'alphatal_102',mul=1 ,maxbacklength=None):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_103(self,name = 'alphatal_103',mul=1 ,maxbacklength=None):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_104(self,name = 'alphatal_104',mul=1 ,maxbacklength=None):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]  
    def alphatal_105(self,name = 'alphatal_105',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_106(self,name = 'alphatal_106',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_107(self,name = 'alphatal_107',mul=1 ,maxbacklength=5):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_108(self,name = 'alphatal_108',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]    
    def alphatal_109(self,name = 'alphatal_109',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_110(self,name = 'alphatal_110',mul=1 ,maxbacklength=None):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_111(self,name = 'alphatal_111',mul=1 ,maxbacklength=None):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_112(self,name = 'alphatal_112',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]  
    def alphatal_113(self,name = 'alphatal_113',mul=1 ,maxbacklength=None):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_114(self,name = 'alphatal_114',mul=1 ,maxbacklength=None):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_115(self,name = 'alphatal_115',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_116(self,name = 'alphatal_116',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]  
    def alphatal_117(self,name = 'alphatal_117',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_118(self,name = 'alphatal_118',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_119(self,name = 'alphatal_119',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_120(self,name = 'alphatal_120',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]  
    def alphatal_121(self,name = 'alphatal_121',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_122(self,name = 'alphatal_122',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_123(self,name = 'alphatal_123',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_124(self,name = 'alphatal_124',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]
    def alphatal_125(self,name = 'alphatal_125',mul=1 ,maxbacklength=50):
        taname=dict_talib()[name.split('@')[0]]
        temp=pd.Series(abstract.Function(taname).__dict__['_Function__info']['parameters'])
        params=None
        if len(temp)>0:
            period=['period' in x for x in temp.index.values]
            if pd.Series(period).any():
                if maxbacklength!=None:maxbacklength=temp[period].max()+maxbacklength      
                #!Bug:直接转换不行
                params=dict( (temp[period]*mul).astype(int).astype(str))
                params=dict( [(k,max(1,int(v))) for k,v in params.items()])
        if maxbacklength==None:maxbacklength=len(self.close)
        open_=self.open[-maxbacklength:];high_=self.high[-maxbacklength:]
        low_=self.low[-maxbacklength:];close_=self.close[-maxbacklength:]
        vol_=self.vol[-maxbacklength:];opt_=self.opt[-maxbacklength:]  
        #      
        temp=self.basefunc(dict_talib()[name.split('@')[0]],open_,high_,low_,close_,vol_,params=params)
        res=pd.DataFrame(temp,index=open_.columns,columns=open_.index).T 
        alpha=pd.DataFrame(index=open_.index,columns=self.col0)
        alpha.loc[:,res.columns]=res
        #------------output---------------------
        return [name,alpha.round(num_round)]  

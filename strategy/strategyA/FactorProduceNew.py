from __future__ import division
import warnings
warnings.filterwarnings("ignore")
from queue import Queue
import pandas as pd
import threading
import numpy as np
import time
from multiprocessing import Pool, Lock, cpu_count, Manager
from multiprocessing.managers import BaseManager
# import clickhouse_driver
import os

class MyManager(BaseManager):
    pass

db_config = {
 'host': '192.168.10.244',
 'port': '9000',
 'user': 'hsj',
 'password': 'hsj0210',
 'db': 'factor_develop_db',
 'table': 'factor_hsj'
}

filepath = r'/home/heshuangji/Data/DATA_DAY_WEIGHT'
factorvaluepath = r'/home/heshuangji/Data/FactorValue/{0}'

CHclient = clickhouse_driver.Client(host=db_config['host'], port=db_config['port'], user=db_config['user'], password=db_config['password'])

# from alphaZS_FH_Class import AlphasZS_FH
# from alphaZS_GS127_Class import AlphasZS_GS127
# from alphaZS_PDF_Class import AlphasZS_PDF
from alphaZS_FH_Class import AlphasZS_FH
from alphaZS_GS127_Class import AlphasZS_GS127
from alphaZS_PDF_Class import AlphasZS_PDF
from alphaZS_101_Class import AlphasZS_YOY
# from alphaZS_TALib_Class import  AlphasZS_tal
from alphaZS_TAall_Class import  AlphasZS_TAall
# from AlphasWYF_ import AlphaWYF_
from AlphasZCL_ import AlphasZCL_

# 是否是第一次生成历史因子值
FisrtHistoryCreratFactor = True
#输入是否需要log
Loglize=True
#
MyManager.register('AlphasZS_FH', AlphasZS_FH)
MyManager.register('AlphasZS_GS127', AlphasZS_GS127)
MyManager.register('AlphasZS_PDF', AlphasZS_PDF)
MyManager.register('AlphasZS_YOY', AlphasZS_YOY)
# MyManager.register('AlphasZS_tal', AlphasZS_tal)
MyManager.register('AlphasZS_TAall', AlphasZS_TAall)
# MyManager.register('AlphaWYF_', AlphaWYF_)
MyManager.register('AlphasZCL_', AlphasZCL_)

# 数据库行情类
class SaveData(threading.Thread):

    def __init__(self, ):
        super(SaveData, self).__init__()
        threading.Thread.__init__(self)

    def run(self):
        global FactorValue,factorvaluepath
        while True:
            if not FactorValue.empty():
                data = FactorValue.get()
                # 获取数据，插入数据库
                name = data['name']
                value = data['value']
                path = data['path']
                value.insert(0, 'name', [name] * len(value))
                pd.DataFrame.to_csv(value, '{0}\\{1}.csv'.format(path, name))
                # value = np.array(value)
                # value = value.tolist()
                # InsertData(value)
            time.sleep(0.005)

def ParaFormat(data):

    x = (data.split('@'))
    x[0] = data
    for i in range(1, len(x)):
        try:         
            x[i] = float(x[i]) if '.' in x[i] else int(x[i]) 
        except:
            pass
    if FisrtHistoryCreratFactor:
        x[-1] = None
    return tuple(x)

def CreatFactor(*args):

    global FactorValue,factorvaluepath
    # 因子值
    FactorValue = Queue(200)
    factorobj, factor, func, paralist = args
    sd = SaveData()
    sd.start()
    # 因子计算
    for para in paralist:
        data = {}
        para = ParaFormat(para)
        fun = getattr(factorobj, factor)
        try:
            name, value = fun(*para)
        except:
            break
        data['name'] = 'log_'+name if Loglize else name
        temp = value.index
        result = []
        for i in temp:
            x = str(i)
            # x = datetime.datetime.strptime(str(i), "%Y-%m-%d %H:%M:%S")
            result.append(x)
        value.insert(0, 'BeginOfBar', result)
        # value['BeginOfBar'] = result
        data['value'] = value
        path = factorvaluepath.format(func)
        data['path'] = path
        FactorValue.put(data)

def GetParaGroup(para, lenrange=[0.1, 1, 3, 10], threshrange=[0.1, 0.2, 0.4, 0.6, 0.8, 1]):

    paragroup = []

    try:

        colname = []
        colname.append('name')
        result = []

        if len(para) > 2:

            for i in range(1, len(para)):

                temp = para[i]
                # 小数参数
                if temp > 0 and temp < 1:
                    df = pd.DataFrame(threshrange, columns=[str(len(colname))])
                    df['name'] = para[0]
                    colname.append(str(len(colname)))
                    result.append(df)
                else:
                    # 整数参数
                    df = pd.DataFrame([max(1, int(temp * x)) for x in lenrange], columns=[str(len(colname))])
                    df['name'] = para[0]
                    colname.append(str(len(colname)))
                    result.append(df)

            df = result[0]
            for i in range(1, len(result)):
                df = pd.merge(df, result[i], how='left', on='name')
            df = df.applymap(lambda x: str(x))
            df = df[colname]
            df = df.drop_duplicates()
            # df['name'] = df.apply(lambda x: "@".join(list(x)), axis=1)
            # paragroup = list(df['name'])

            df['name'] = df.apply(lambda x: "@".join(list(x)), axis=1)
            df = df.set_index('name').astype(float)
            maxindex = df.mean().index[df.mean() == df.mean().max()].values[0]
            otherindex = list(df.columns)
            otherindex.remove(maxindex)
            df = df[df[maxindex] > df[otherindex].max(axis=1)]
            only = df.groupby(otherindex).apply(lambda x: x == x.min())[maxindex]
            paragroup = list(df[only].index)

        else:
            result = (para[0]) + "@" + str(para[-1])
            paragroup = [result]

    except Exception as e:
        print(str(e))

    return paragroup

def InsertData(data):

    sql = "INSERT INTO `%s`.`%s` (Name,  BeginOfBar,I,SC,CF,A,AG,AL,BU,C,HC,J,JD,L,MA,NI,P,PP,RB,RU,SF,SM,SR,TA,ZC,Y,FU,EG,AP,V,JM,ZN,SP,CU,M,RM,OI,EB,FG,PF,PB,SA,SN,SS) VALUES " % (db_config['db'], db_config['table'])
    rsp = CHclient.execute(sql, data, types_check=True)
    if rsp is not None:
        msg = "data insert --" + str(rsp)
        print(msg)

def mkdir(path):

    # 去除首位空格
    path = path.strip()
    # 去除尾部 \ 符号
    path = path.rstrip("\\")
    isExists = os.path.exists(path)
    # 判断结果
    if not isExists:
        os.makedirs(path)
        print(path + ' 创建成功')
        return True
    else:
        # 如果目录存在则不创建，并提示目录已存在
        print(path + ' 目录已存在')
        return False

if __name__ == '__main__':

    open_ = pd.read_csv(filepath+'/Open.csv', header=0, parse_dates=True, index_col=0).dropna(how='all')
    high_ = pd.read_csv(filepath+'/High.csv', header=0, parse_dates=True, index_col=0).dropna(how='all')
    low_ = pd.read_csv(filepath+'/Low.csv', header=0, parse_dates=True, index_col=0).dropna(how='all')
    close_ = pd.read_csv(filepath+'/Close.csv', header=0, parse_dates=True, index_col=0).dropna(how='all')
    vol_ = pd.read_csv(filepath+'/Vol.csv', header=0, parse_dates=True, index_col=0).dropna(how='all')
    opt_ = pd.read_csv(filepath+'/OpenInterest.csv', header=0, parse_dates=True, index_col=0).dropna(how='all')
    amount_ = pd.read_csv(filepath+'/Amount.csv', header=0, parse_dates=True, index_col=0).dropna(how='all')
    vwap_ = amount_/vol_
    #    
    if Loglize:
        open_ = np.log(open_)
        high_ = np.log(high_)
        low_ = np.log(low_)
        close_ = np.log(close_)
        vol_ = np.log(vol_)
        opt_ = np.log(opt_)
        amount_ = np.log(amount_)
        vwap_ = np.log(vwap_)    
    for func in []:     # 'AlphasZS_FH', 'AlphaWYF_','AlphasZCL_','AlphasZS_tal','AlphasZS_YOY','AlphasZS_FH',  'AlphasZS_GS127','AlphasZS_PDF','AlphasZS_TAall' 
            # 创建因子目录
            if not os.path.exists(factorvaluepath.format(func)):os.mkdir(factorvaluepath.format(func))
            # 因子对象实例化
            factorobj = eval("%s(open_,high_,low_,close_,vol_,opt_,amount_,vwap_)"%(func))
            # 用于获取默认参数
            factorobjbase = eval("%s(open_,high_,low_,close_,vol_,opt_,amount_,vwap_)"%(func))
            # 生成需要的因子函数list
            alphalist = []
            temp = factorobj.__dir__()
            # 获取因子函数
            for factor in temp:
                if "alpha" in factor and factor != 'empty':
                    alphalist.append(factor)
            for factor in alphalist:
                print(factor)
                # 获取默认参数
                para = getattr(factorobjbase, factor).__defaults__
                # 生成参数寻优列表
                paralist = GetParaGroup(para)
                CreatFactor(factorobj, factor, func, paralist)
#%%
    # with MyManager() as manager:    
    #     for func in ['AlphasZS_TAall','AlphasZS_tal','AlphasZS_YOY','AlphasZS_FH', 
    #              'AlphasZS_GS127','AlphasZS_PDF']:
    #         if not os.path.exists(factorvaluepath.format(func)):os.mkdir(factorvaluepath.format(func))       
    #         # 因子对象实例化
    #         factorobj = eval("manager.%s(open_,high_,low_,close_,vol_,opt_,amount_,vwap_)"%(func))
    #         # 用于获取默认参数
    #         factorobjbase = eval("%s(open_,high_,low_,close_,vol_,opt_,amount_,vwap_)"%(func))
    #         # 生成需要的因子函数list
    #         alphalist = []
    #         temp = factorobj.__dir__()
    #         # 获取因子函数
    #         for factor in temp:
    #             if "alpha" in factor and factor != 'empty':
    #                 alphalist.append(factor)
    #         # print(alphalist)
    #         pool = Pool()
    #         for factor in alphalist:
    #             print(factor)
    #             # 获取默认参数
    #             para = getattr(factorobjbase, factor).__defaults__
    #             # 生成参数寻优列表
    #             paralist = GetParaGroup(para)
    #             pool.apply_async(CreatFactor, args=(factorobj, factor, func, paralist))
    #         pool.close();pool.join()
            

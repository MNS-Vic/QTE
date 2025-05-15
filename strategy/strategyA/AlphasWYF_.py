from apitool import *
import talib as tb


class AlphaWYF_(object):


    def __init__(self, open_, high_, low_, close_, vol_, opt_, amount_= None , vwap_ = None):

        # 函数与self,name的对应表    mya.open = self.open
        self.open = open_
        self.high = high_
        self.low = low_
        self.close = close_
        self.vol = vol_
        self.opt = opt_
        self.amount = amount_
        self.vwap = vwap_
        self.empty = lambda n: oldempty_(n, open_)

    def alphaWYF1(self, name='alphaWYF1', maxbacklength=20):


        if maxbacklength == None: maxbacklength = len(self.close)

        open_ = self.open[-maxbacklength:]
        high_ = self.high[-maxbacklength:]
        low_ = self.low[-maxbacklength:]
        close_ = self.close[-maxbacklength:]
        vol_ = self.vol[-maxbacklength:]
        amount_ = self.amount[-maxbacklength:]
        temp = (((close_ - low_) - (high_ - low_)) / (high_ - low_)) * vol_
        ad = cumsum_(temp)
        return [name, ad.round(num_round)]

    def alphaWYF2(self, name='alphaWYF2',  maxbacklength=20):

        def maxcol(a, b, c):

            if a >= b and a >= c:
                return 1
            elif b >= c and b >= a:
                return 2
            else:
                return 3

        if maxbacklength == None: maxbacklength = len(self.close)

        open_ = self.open[-maxbacklength:]
        high_ = self.high[-maxbacklength:]
        low_ = self.low[-maxbacklength:]
        close_ = self.close[-maxbacklength:]
        vol_ = self.vol[-maxbacklength:]
        amount_ = self.amount[-maxbacklength:]

        K = max_((high_ - close_.shift(1)), (low_ - close_.shift(1)))

        x = high_ - close_.shift(1)
        y = low_ - close_.shift(1)
        z = high_ - low_

        HCP = high_ - close_.shift(1)
        LC = low_ - close_
        CPOP = close_.shift(1) - open_.shift(1)
        LCP = low_ - close_.shift(1)
        HL = high_ - close_

        R = {}
        columns = x.columns
        for col in columns:
            df = pd.DataFrame([x[col], y[col], z[col], HCP[col], LC[col], CPOP[col], LCP[col], HL[col]]).T
            df.columns = ['1', '2', '3', '4', '5', '6', '7', '8']
            df[col] = df.apply(
                lambda x: x['4'] - 0.5 * x['5'] + 0.25 * x['6'] if maxcol(x['1'], x['2'], x['3']) == 1
                else x['7'] - 0.5 * x['8'] + 0.25 * x['6'] if maxcol(
                    x['1'], x['2'], x['3']) == 2 else 0.5 * x['8'] + 0.25 * x['6'], axis=1)

            R[col] = df[col]
        R = pd.DataFrame.from_dict(R, orient='index').T
        R.sort_index(inplace=True)
        ASI = (50 * K) * (
                    ((close_ - close_.shift(1)) + 0.5 * (close_ - open_) + (close_.shift(1) - open_.shift(1))) / R.replace(0,np.nan))

        return [name, ASI.round(num_round)]

    def alphaWYF3(self, name='alphaWYF3', maxbacklength=20, ):

        if maxbacklength == None: maxbacklength = len(self.close)

        open_ = self.open[-maxbacklength:]
        high_ = self.high[-maxbacklength:]
        low_ = self.low[-maxbacklength:]
        close_ = self.close[-maxbacklength:]
        vol_ = self.vol[-maxbacklength:]
        amount_ = self.amount[-maxbacklength:]

        X = 0.5 * (high_ + low_) / 2
        Y = 0.5 * (high_.shift(1) + low_.shift(1)) / 2
        Z = vol_ / (high_ - low_)

        EMV = (X - Y) / Z

        return [name, EMV.round(num_round)]

    def alphaWYF4(self, name='alphaWYF4',  period=5, maxbacklength=20):

        if maxbacklength == None: maxbacklength = len(self.close)

        high_ = self.high[-maxbacklength:]
        low_ = self.low[-maxbacklength:]

        Up = high_.rolling(period).apply(lambda x: 100 * (period - np.argmax(x)) / period)
        Down = low_.rolling(period).apply(lambda x: 100 * (period - np.argmin(x)) / period)

        return [name, Up.round(num_round)]

    def alphaWYF5(self, name='alphaWYF5', period=5,  maxbacklength=20):

        if maxbacklength == None: maxbacklength = len(self.close)

        high_ = self.high[-maxbacklength:]
        low_ = self.low[-maxbacklength:]

        Up = high_.rolling(period).apply(lambda x: 100 * (period - np.argmax(x)) / period)
        Down = low_.rolling(period).apply(lambda x: 100 * (period - np.argmin(x)) / period)

        return [name, Down.round(num_round)]

    def alphaWYF6(self,  name='alphaWYF6', period=5, maxbacklength=20):

        if maxbacklength == None: maxbacklength = len(self.close)

        high_ = self.high[-maxbacklength:]
        low_ = self.low[-maxbacklength:]

        Up = high_.rolling(period).apply(lambda x: 100 * (period - np.argmax(x)) / period)
        Down = low_.rolling(period).apply(lambda x: 100 * (period - np.argmin(x)) / period)
        AroonOscillator = Up - Down

        return [name, AroonOscillator.round(num_round)]

    def alphaWYF7(self, name='alphaWYF7', period=5, maxbacklength=20):

        if maxbacklength == None: maxbacklength = len(self.close)

        open_ = self.open[-maxbacklength:]
        high_ = self.high[-maxbacklength:]
        low_ = self.low[-maxbacklength:]
        close_ = self.close[-maxbacklength:]
        vol_ = self.vol[-maxbacklength:]
        amount_ = self.amount[-maxbacklength:]

        t1 = high_ - low_
        t2 = high_ - close_.shift(1)
        t3 = close_.shift(1) - low_

        ATR = {}
        columns = close_.columns
        for col in columns:
            df = pd.DataFrame([t1[col], t2[col], t3[col]]).T
            df.columns = ['1', '2', '3']
            df[col] = df.apply(lambda x: max(x), axis=1)
            ATR[col] = df[col]

        ATR = pd.DataFrame.from_dict(ATR, orient='index').T
        ATR.sort_index(inplace=True)
        ATR = ema_(ATR, period)

        return [name, ATR.round(num_round)]

    def alphaWYF8(self, name='alphaWYF8',  period=5, maxbacklength=20):

        if maxbacklength == None: maxbacklength = len(self.close)

        open_ = self.open[-maxbacklength:]
        high_ = self.high[-maxbacklength:]
        low_ = self.low[-maxbacklength:]
        close_ = self.close[-maxbacklength:]
        vol_ = self.vol[-maxbacklength:]
        amount_ = self.amount[-maxbacklength:]

        H = high_.rolling(period).apply(lambda x: max(x))
        L = high_.rolling(period).apply(lambda x: min(x))

        M = (close_ + H + L) / 3
        A = sma2_(M, period)
        D = stddev_(M - A, period)
        CCI = (M - A) / (0.015 * D)
        return [name, CCI.round(num_round)]

        return [name, CCI.round(num_round)]

    def alphaWYF9(self, name='alphaWYF9', maxbacklength=20):

        if maxbacklength == None: maxbacklength = len(self.close)

        open_ = self.open[-maxbacklength:]
        high_ = self.high[-maxbacklength:]
        low_ = self.low[-maxbacklength:]
        close_ = self.close[-maxbacklength:]
        vol_ = self.vol[-maxbacklength:]
        amount_ = self.amount[-maxbacklength:]

        PDM = max_(high_ - high_.shift(1), 0)
        MDM = max_(low_ - low_.shift(1), 0)

        t1 = high_ - low_
        t2 = high_ - close_.shift(1)
        t3 = close_.shift(1) - low_

        TR = {}
        columns = close_.columns
        for col in columns:
            df = pd.DataFrame([t1[col], t2[col], t3[col]]).T
            df.columns = ['1', '2', '3']
            df[col] = df.apply(lambda x: max(x), axis=1)
            TR[col] = df[col]

        TR = pd.DataFrame.from_dict(TR, orient='index').T
        TR.sort_index(inplace=True)
        PDI = ema_(PDM, 27) / ema_(TR, 27)
        MDI = ema_(MDM, 27) / ema_(TR, 27)

        DX = 100 * abs_(PDI - MDI) / (PDI + MDI)
        ADX = (DX + DX.shift(14)) / 2

        return [name, PDI.round(num_round), MDI.round(num_round), DX.round(num_round), ADX.round(num_round)]

    def alphaWYF10(self, name='alphaWYF10', maxbacklength=20):

        if maxbacklength == None: maxbacklength = len(self.close)

        open_ = self.open[-maxbacklength:]
        high_ = self.high[-maxbacklength:]
        low_ = self.low[-maxbacklength:]
        close_ = self.close[-maxbacklength:]
        vol_ = self.vol[-maxbacklength:]
        amount_ = self.amount[-maxbacklength:]

        PDM = max_(high_ - high_.shift(1), 0)
        MDM = max_(low_ - low_.shift(1), 0)

        t1 = high_ - low_
        t2 = high_ - close_.shift(1)
        t3 = close_.shift(1) - low_

        TR = {}
        columns = close_.columns
        for col in columns:
            df = pd.DataFrame([t1[col], t2[col], t3[col]]).T
            df.columns = ['1', '2', '3']
            df[col] = df.apply(lambda x: max(x), axis=1)
            TR[col] = df[col]

        TR = pd.DataFrame.from_dict(TR, orient='index').T
        TR.sort_index(inplace=True)
        PDI = ema_(PDM, 27) / ema_(TR, 27)
        MDI = ema_(MDM, 27) / ema_(TR, 27)

        DX = 100 * abs_(PDI - MDI) / (PDI + MDI)
        ADX = (DX + DX.shift(14)) / 2

        return [name, PDI.round(num_round), ]

    def alphaWYF11(self, name='alphaWYF11', maxbacklength=20):

        if maxbacklength == None: maxbacklength = len(self.close)

        open_ = self.open[-maxbacklength:]
        high_ = self.high[-maxbacklength:]
        low_ = self.low[-maxbacklength:]
        close_ = self.close[-maxbacklength:]
        vol_ = self.vol[-maxbacklength:]
        amount_ = self.amount[-maxbacklength:]

        PDM = max_(high_ - high_.shift(1), 0)
        MDM = max_(low_ - low_.shift(1), 0)

        t1 = high_ - low_
        t2 = high_ - close_.shift(1)
        t3 = close_.shift(1) - low_

        TR = {}
        columns = close_.columns
        for col in columns:
            df = pd.DataFrame([t1[col], t2[col], t3[col]]).T
            df.columns = ['1', '2', '3']
            df[col] = df.apply(lambda x: max(x), axis=1)
            TR[col] = df[col]

        TR = pd.DataFrame.from_dict(TR, orient='index').T
        TR.sort_index(inplace=True)
        PDI = ema_(PDM, 27) / ema_(TR, 27)
        MDI = ema_(MDM, 27) / ema_(TR, 27)

        DX = 100 * abs_(PDI - MDI) / (PDI + MDI)
        ADX = (DX + DX.shift(14)) / 2

        return [name, DX.round(num_round),]

    def alphaWYF12(self, name='alphaWYF12', maxbacklength=20):

        if maxbacklength == None: maxbacklength = len(self.close)

        open_ = self.open[-maxbacklength:]
        high_ = self.high[-maxbacklength:]
        low_ = self.low[-maxbacklength:]
        close_ = self.close[-maxbacklength:]
        vol_ = self.vol[-maxbacklength:]
        amount_ = self.amount[-maxbacklength:]

        PDM = max_(high_ - high_.shift(1), 0)
        MDM = max_(low_ - low_.shift(1), 0)

        t1 = high_ - low_
        t2 = high_ - close_.shift(1)
        t3 = close_.shift(1) - low_

        TR = {}
        columns = close_.columns
        for col in columns:
            df = pd.DataFrame([t1[col], t2[col], t3[col]]).T
            df.columns = ['1', '2', '3']
            df[col] = df.apply(lambda x: max(x), axis=1)
            TR[col] = df[col]

        TR = pd.DataFrame.from_dict(TR, orient='index').T
        TR.sort_index(inplace=True)
        PDI = ema_(PDM, 27) / ema_(TR, 27)
        MDI = ema_(MDM, 27) / ema_(TR, 27)

        DX = 100 * abs_(PDI - MDI) / (PDI + MDI)
        ADX = (DX + DX.shift(14)) / 2

        return [name, ADX.round(num_round)]

    def alphaWYF13(self, name='alphaWYF13', period=5, maxbacklength=20):

        if maxbacklength == None: maxbacklength = len(self.close)

        open_ = self.open[-maxbacklength:]
        high_ = self.high[-maxbacklength:]
        low_ = self.low[-maxbacklength:]
        close_ = self.close[-maxbacklength:]
        vol_ = self.vol[-maxbacklength:]
        amount_ = self.amount[-maxbacklength:]

        x = close_ - open_
        y = high_ - low_
        BOP = ema_(x / y, period)

        return [name, BOP.round(num_round), ]

    def alphaWYF14(self, name='alphaWYF14', period=5, maxbacklength=20):

        if maxbacklength == None: maxbacklength = len(self.close)

        open_ = self.open[-maxbacklength:]
        high_ = self.high[-maxbacklength:]
        low_ = self.low[-maxbacklength:]
        close_ = self.close[-maxbacklength:]
        vol_ = self.vol[-maxbacklength:]
        amount_ = self.amount[-maxbacklength:]

        CLV = (close_ - low_) / (high_ - low_)

        x = CLV * vol_
        x = x.rolling(period).sum()

        y = vol_.rolling(period).sum()

        CMF = x / y

        return [name, CMF.round(num_round), ]

    def alphaWYF15(self, name='alphaWYF15', period=5, maxbacklength=20):

        if maxbacklength == None: maxbacklength = len(self.close)

        open_ = self.open[-maxbacklength:]
        high_ = self.high[-maxbacklength:]
        low_ = self.low[-maxbacklength:]
        close_ = self.close[-maxbacklength:]
        vol_ = self.vol[-maxbacklength:]
        amount_ = self.amount[-maxbacklength:]

        data = close_ - close_.shift(1)
        up = data.apply(lambda x: x if x > 0 else 0)
        down = data.apply(lambda x: abs(x) if x < 0 else 0)
        sumup = up.rolling(period).sum()
        sumdown = down.rolling(period).sum()
        CMO = 100 * ((sumup - sumdown) / (sumup + sumdown))

        return [name, CMO.round(num_round), ]

    def alphaWYF16(self, name='alphaWYF16', period=5, maxbacklength=20):

        if maxbacklength == None: maxbacklength = len(self.close)

        open_ = self.open[-maxbacklength:]
        high_ = self.high[-maxbacklength:]
        low_ = self.low[-maxbacklength:]
        close_ = self.close[-maxbacklength:]
        vol_ = self.vol[-maxbacklength:]
        amount_ = self.amount[-maxbacklength:]

        data = close_.rolling(period).sum() / period

        DPO = close_.shift(1) - data

        return [name, DPO.round(num_round), ]

    def alphaWYF17(self, name='alphaWYF17', period=5, maxbacklength=20):

        if maxbacklength == None: maxbacklength = len(self.close)

        open_ = self.open[-maxbacklength:]
        high_ = self.high[-maxbacklength:]
        low_ = self.low[-maxbacklength:]
        close_ = self.close[-maxbacklength:]
        vol_ = self.vol[-maxbacklength:]
        amount_ = self.amount[-maxbacklength:]

        data = ema_((high_ - low_), period)

        CVI = (data - data.shift(period)) / (100 * data.shift(period))

        return [name, CVI.round(num_round), ]

    def alphaWYF18(self, name='alphaWYF18', period=5, maxbacklength=20):

        import math

        if maxbacklength == None: maxbacklength = len(self.close)

        open_ = self.open[-maxbacklength:]
        high_ = self.high[-maxbacklength:]
        low_ = self.low[-maxbacklength:]
        close_ = self.close[-maxbacklength:]
        vol_ = self.vol[-maxbacklength:]
        amount_ = self.amount[-maxbacklength:]

        margin = 1000
        commision = 25
        k = 300 / (math.sqrt(margin) * (150 + commision)) * 100
        x = max_(max_((high_ - low_), abs_(high_ - close_.shift(1))), abs_(close_.shift(1) - low_))
        MTR = ema_(x, period)

        HD = high_ - high_.shift(1)
        LD = low_.shift(1) - low_
        temp = HD - LD
        x = temp.applymap(lambda x: 1 if x > 0 else 0)
        y = HD.applymap(lambda x: 1 if x > 0 else 0)
        DMP = ema_(x * y * HD, period)

        temp = LD - HD
        x = temp.applymap(lambda x: 1 if x > 0 else 0)
        y = LD.applymap(lambda x: 1 if x > 0 else 0)
        DMM = ema_(x * y * LD, period)

        PDI = DMP * 100 / MTR
        MDI = DMM * 100 / MTR
        ADX = ema_((abs_(MDI - PDI) / (MDI + PDI)) * 100, period)
        ADXR = (ADX + ADX.shift(period)) / 2
        CSI = k * ADXR * MTR

        return [name, CSI.round(num_round), ]

    def alphaWYF19(self, name='alphaWYF19',  factor=0.2, maxbacklength=20):

        def fun(x):
            a = factor
            temp = []
            for i in range(0, len(x)):

                if i == 0:
                    temp.append(x[i])
                else:
                    temp.append(x[i - 1] + a * (x[i] - temp[i - 1]))
            return temp

        if maxbacklength == None: maxbacklength = len(self.close)

        open_ = self.open[-maxbacklength:]
        high_ = self.high[-maxbacklength:]
        low_ = self.low[-maxbacklength:]
        close_ = self.close[-maxbacklength:]
        vol_ = self.vol[-maxbacklength:]
        amount_ = self.amount[-maxbacklength:]
        opt_ = self.opt[-maxbacklength:]

        x = (high_ + low_) / 2
        temp = opt_ - opt_.shift(1)

        k = ((x) - (x.shift(2))) * ( (1 + (abs_(temp))) / (min_(opt_ , opt_.shift(1))) ) * vol_

        k = k.fillna(0)

        HPV = k.apply(fun, axis=0)

        return [name, HPV.round(num_round), ]

    def alphaWYF20(self, name='alphaWYF20',  maxbacklength=20):



        if maxbacklength == None: maxbacklength = len(self.close)

        open_ = self.open[-maxbacklength:]
        high_ = self.high[-maxbacklength:]
        low_ = self.low[-maxbacklength:]
        close_ = self.close[-maxbacklength:]
        vol_ = self.vol[-maxbacklength:]
        amount_ = self.amount[-maxbacklength:]
        opt_ = self.opt[-maxbacklength:]

        HT_DCPERIOD = close_.apply(tb.HT_DCPERIOD)


        return [name, HT_DCPERIOD.round(num_round), ]

    def alphaWYF21(self, name='alphaWYF21', maxbacklength=20):

        if maxbacklength == None: maxbacklength = len(self.close)

        open_ = self.open[-maxbacklength:]
        high_ = self.high[-maxbacklength:]
        low_ = self.low[-maxbacklength:]
        close_ = self.close[-maxbacklength:]
        vol_ = self.vol[-maxbacklength:]
        amount_ = self.amount[-maxbacklength:]
        opt_ = self.opt[-maxbacklength:]

        HT_DCPHASE = close_.apply(tb.HT_DCPHASE)


        return [name, HT_DCPHASE.round(num_round), ]

    def alphaWYF22(self, name='alphaWYF22', maxbacklength=20):

        if maxbacklength == None: maxbacklength = len(self.close)

        open_ = self.open[-maxbacklength:]
        high_ = self.high[-maxbacklength:]
        low_ = self.low[-maxbacklength:]
        close_ = self.close[-maxbacklength:]
        vol_ = self.vol[-maxbacklength:]
        amount_ = self.amount[-maxbacklength:]
        opt_ = self.opt[-maxbacklength:]

        HT_PHASOR_Inphase = {}
        columns = close_.columns
        for col in columns:
            data1,data2 = tb.HT_PHASOR(close_[col])
            HT_PHASOR_Inphase[col] = data1

        HT_PHASOR_Inphase = pd.DataFrame.from_dict(HT_PHASOR_Inphase, orient='index').T
        HT_PHASOR_Inphase.sort_index(inplace=True)
        return [name, HT_PHASOR_Inphase.round(num_round), ]

    def alphaWYF23(self, name='alphaWYF23', maxbacklength=20):

        if maxbacklength == None: maxbacklength = len(self.close)

        open_ = self.open[-maxbacklength:]
        high_ = self.high[-maxbacklength:]
        low_ = self.low[-maxbacklength:]
        close_ = self.close[-maxbacklength:]
        vol_ = self.vol[-maxbacklength:]
        amount_ = self.amount[-maxbacklength:]
        opt_ = self.opt[-maxbacklength:]

        HT_PHASOR_Inphase = {}
        columns = close_.columns
        for col in columns:
            data1,data2 = tb.HT_PHASOR(close_[col])
            HT_PHASOR_Inphase[col] = data2

        HT_PHASOR_Quadrature = pd.DataFrame.from_dict(HT_PHASOR_Inphase, orient='index').T
        HT_PHASOR_Quadrature.sort_index(inplace=True)
        return [name, HT_PHASOR_Quadrature.round(num_round), ]

    def alphaWYF24(self, name='alphaWYF24', maxbacklength=20):

        if maxbacklength == None: maxbacklength = len(self.close)

        open_ = self.open[-maxbacklength:]
        high_ = self.high[-maxbacklength:]
        low_ = self.low[-maxbacklength:]
        close_ = self.close[-maxbacklength:]
        vol_ = self.vol[-maxbacklength:]
        amount_ = self.amount[-maxbacklength:]
        opt_ = self.opt[-maxbacklength:]

        HT_QUADRA = close_.apply(tb.HT_QUADRA)

        return [name, HT_QUADRA.round(num_round), ]

    def alphaWYF25(self, name='alphaWYF25', maxbacklength=20):

        if maxbacklength == None: maxbacklength = len(self.close)

        open_ = self.open[-maxbacklength:]
        high_ = self.high[-maxbacklength:]
        low_ = self.low[-maxbacklength:]
        close_ = self.close[-maxbacklength:]
        vol_ = self.vol[-maxbacklength:]
        amount_ = self.amount[-maxbacklength:]
        opt_ = self.opt[-maxbacklength:]

        HT_SINE_Sine = {}
        columns = close_.columns
        for col in columns:
            data1, data2 = tb.HT_SINE(close_[col])
            HT_SINE_Sine[col] = data1

        HT_SINE_Sine = pd.DataFrame.from_dict(HT_SINE_Sine, orient='index').T
        HT_SINE_Sine.sort_index(inplace=True)

        return [name, HT_SINE_Sine.round(num_round), ]

    def alphaWYF26(self, name='alphaWYF26',  maxbacklength=20):

        if maxbacklength == None: maxbacklength = len(self.close)

        open_ = self.open[-maxbacklength:]
        high_ = self.high[-maxbacklength:]
        low_ = self.low[-maxbacklength:]
        close_ = self.close[-maxbacklength:]
        vol_ = self.vol[-maxbacklength:]
        amount_ = self.amount[-maxbacklength:]
        opt_ = self.opt[-maxbacklength:]

        HT_SINE_LeadSine = {}
        columns = close_.columns
        for col in columns:
            data1, data2 = tb.HT_SINE(close_[col])
            HT_SINE_LeadSine[col] = data2

        HT_SINE_LeadSine = pd.DataFrame.from_dict(HT_SINE_LeadSine, orient='index').T
        HT_SINE_LeadSine.sort_index(inplace=True)
        return [name, HT_SINE_LeadSine.round(num_round), ]

    def alphaWY27(self, name='alphaWYF27',  maxbacklength=20):

        if maxbacklength == None: maxbacklength = len(self.close)

        open_ = self.open[-maxbacklength:]
        high_ = self.high[-maxbacklength:]
        low_ = self.low[-maxbacklength:]
        close_ = self.close[-maxbacklength:]
        vol_ = self.vol[-maxbacklength:]
        amount_ = self.amount[-maxbacklength:]
        opt_ = self.opt[-maxbacklength:]

        HT_TRENDLINE = close_.apply(tb.HT_TRENDLINE)

        return [name, HT_TRENDLINE.round(num_round), ]

    def alphaWYF28(self, name='alphaWYF28',  maxbacklength=20):

        if maxbacklength == None: maxbacklength = len(self.close)

        open_ = self.open[-maxbacklength:]
        high_ = self.high[-maxbacklength:]
        low_ = self.low[-maxbacklength:]
        close_ = self.close[-maxbacklength:]
        vol_ = self.vol[-maxbacklength:]
        amount_ = self.amount[-maxbacklength:]
        opt_ = self.opt[-maxbacklength:]

        HT_TRENDMODE = close_.apply(tb.HT_TRENDMODE)

        return [name, HT_TRENDMODE.round(num_round), ]

    def alphaWYF29(self, name='alphaWYF29', opt1=5, opt2=1, maxbacklength=20):

        if maxbacklength == None: maxbacklength = len(self.close)

        open_ = self.open[-maxbacklength:]
        high_ = self.high[-maxbacklength:]
        low_ = self.low[-maxbacklength:]
        close_ = self.close[-maxbacklength:]
        vol_ = self.vol[-maxbacklength:]
        amount_ = self.amount[-maxbacklength:]
        opt_ = self.opt[-maxbacklength:]

        slop = close_.rolling(opt1).apply(lambda x: np.polyfit(range(len(x)), x, 1)[0])
        intercept = close_.rolling(opt1).apply(lambda x: np.polyfit(range(len(x)), x, 1)[1])
        forecast = slop * (opt1 + opt2 - 1) + intercept
        FO = 100 * ((close_ - forecast.shift(1))/close_)

        return [name, FO.round(num_round)]

    def alphaWYF30(self, name='alphaWYF30', period=4, ration=0.1, maxbacklength=20):

        if maxbacklength == None: maxbacklength = len(self.close)

        open_ = self.open[-maxbacklength:]
        high_ = self.high[-maxbacklength:]
        low_ = self.low[-maxbacklength:]
        close_ = self.close[-maxbacklength:]
        vol_ = self.vol[-maxbacklength:]
        amount_ = self.amount[-maxbacklength:]
        opt_ = self.opt[-maxbacklength:]

        mid = (low_ + high_) * 0.5
        columns = close_.columns
        FisherTransformation = {}
        for col in columns:
            result = []
            for i in range(period, len(close_)):
                if i < period:
                    result.append(close_[col][i])
                else:
                    value = ration * 2 * (((mid[col][i] - min(low_[col][(i-period):i])) / (max(high_[col][(i-period):i]) - min(low_[col][(i-period):i]))) - 0.5) -\
                    (1 - ration) * result[i-1]
                    result.append(value)
        FisherTransformation = pd.DataFrame.from_dict(FisherTransformation, orient='index').T
        FisherTransformation.sort_index(inplace=True)
        return [name, FisherTransformation.round(num_round)]

    def alphaWYF31(self, name='alphaWYF31', maxbacklength=20):

        if maxbacklength == None: maxbacklength = len(self.close)

        open_ = self.open[-maxbacklength:]
        high_ = self.high[-maxbacklength:]
        low_ = self.low[-maxbacklength:]
        close_ = self.close[-maxbacklength:]
        vol_ = self.vol[-maxbacklength:]
        amount_ = self.amount[-maxbacklength:]
        opt_ = self.opt[-maxbacklength:]

        ForceIndex = vol_ * (close_ - close_.shift(1))

        return [name, ForceIndex.round(num_round)]

    def alphaWYF32(self, name='alphaWYF32', period=0.1, ration=0.1, maxbacklength=20):

        if maxbacklength == None: maxbacklength = len(self.close)

        open_ = self.open[-maxbacklength:]
        high_ = self.high[-maxbacklength:]
        low_ = self.low[-maxbacklength:]
        close_ = self.close[-maxbacklength:]
        vol_ = self.vol[-maxbacklength:]
        amount_ = self.amount[-maxbacklength:]
        opt_ = self.opt[-maxbacklength:]
        FAMA = {}
        for col in close_.columns:
            mama, fama = tb.MAMA(close_[col], fastlimit=period, slowlimit=ration)
            FAMA[col] = fama

        FAMA = pd.DataFrame.from_dict(FAMA, orient='index').T
        FAMA.sort_index(inplace=True)
        return [name, FAMA.round(num_round)]



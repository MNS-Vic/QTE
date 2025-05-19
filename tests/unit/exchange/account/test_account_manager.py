#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
账户管理器单元测试
"""
import pytest
from decimal import Decimal
import uuid
from qte.exchange.account.account_manager import AccountManager, UserAccount, AssetBalance, Position, TransactionRecord

# 使用Decimal确保精确计算
D = lambda x: Decimal(str(x))

class TestAccountManager:
    """账户管理器测试类"""
    
    @pytest.fixture
    def account_manager(self):
        """创建账户管理器实例"""
        return AccountManager()
    
    @pytest.fixture
    def user_id(self):
        """创建测试用户ID"""
        return f"test_user_{uuid.uuid4()}"
    
    @pytest.fixture
    def base_asset(self):
        """基础资产 - 如BTC"""
        return "BTC"
    
    @pytest.fixture
    def quote_asset(self):
        """计价资产 - 如USDT"""
        return "USDT"
    
    @pytest.fixture
    def symbol(self, base_asset, quote_asset):
        """交易对 - 如BTC/USDT"""
        return f"{base_asset}/{quote_asset}"
    
    def test_account_creation(self, account_manager, user_id):
        """测试账户创建 (AC-001)"""
        # 创建账户
        account = account_manager.create_account(user_id)
        
        # 验证账户属性
        assert account.user_id == user_id
        assert account.name == user_id  # 默认名称与用户ID相同
        assert isinstance(account.balances, dict)
        assert len(account.balances) == 0
        assert isinstance(account.positions, dict)
        assert len(account.positions) == 0
        assert isinstance(account.transactions, list)
        assert len(account.transactions) == 0
        
        # 验证账户已添加到管理器
        assert account_manager.get_account(user_id) is account
        assert user_id in account_manager.get_all_accounts()
        
        # 测试创建自定义名称的账户
        custom_name = "测试账户"
        custom_account = account_manager.create_account(user_id + "_custom", custom_name)
        assert custom_account.name == custom_name
    
    def test_deposit(self, account_manager, user_id, quote_asset):
        """测试存款操作 (AC-002)"""
        # 创建账户
        account = account_manager.create_account(user_id)
        
        # 测试存入资金
        deposit_amount = D("1000.50")
        result = account.deposit(quote_asset, deposit_amount)
        
        # 验证结果
        assert result is True
        
        # 验证余额更新
        balance = account.get_balance(quote_asset)
        assert balance.free == deposit_amount
        assert balance.locked == D(0)
        assert balance.total == deposit_amount
        
        # 验证交易记录
        assert len(account.transactions) == 1
        transaction = account.transactions[0]
        assert transaction.transaction_type == "DEPOSIT"
        assert transaction.asset == quote_asset
        assert transaction.amount == deposit_amount
        
        # 测试存款金额为零或负数
        assert account.deposit(quote_asset, D(0)) is False
        assert account.deposit(quote_asset, D("-10")) is False
        
        # 余额不应该变化
        assert account.get_balance(quote_asset).free == deposit_amount
    
    def test_withdraw(self, account_manager, user_id, quote_asset):
        """测试取款操作 (AC-003)"""
        # 创建账户并存入资金
        account = account_manager.create_account(user_id)
        initial_amount = D("2000")
        account.deposit(quote_asset, initial_amount)
        
        # 测试提取部分资金
        withdraw_amount = D("500.25")
        result = account.withdraw(quote_asset, withdraw_amount)
        
        # 验证结果
        assert result is True
        
        # 验证余额更新
        expected_balance = initial_amount - withdraw_amount
        balance = account.get_balance(quote_asset)
        assert balance.free == expected_balance
        assert balance.locked == D(0)
        assert balance.total == expected_balance
        
        # 验证交易记录
        assert len(account.transactions) == 2  # 存款和取款
        transaction = account.transactions[1]  # 最新交易
        assert transaction.transaction_type == "WITHDRAW"
        assert transaction.asset == quote_asset
        assert transaction.amount == -withdraw_amount  # 取款金额为负数
        
        # 测试取款金额超过余额
        exceed_amount = expected_balance + D("100")
        assert account.withdraw(quote_asset, exceed_amount) is False
        
        # 测试取款金额为零或负数
        assert account.withdraw(quote_asset, D(0)) is False
        assert account.withdraw(quote_asset, D("-10")) is False
        
        # 余额不应该变化
        assert account.get_balance(quote_asset).free == expected_balance
    
    def test_lock_asset(self, account_manager, user_id, quote_asset):
        """测试资产冻结 (AC-004)"""
        # 创建账户并存入资金
        account = account_manager.create_account(user_id)
        initial_amount = D("1000")
        account.deposit(quote_asset, initial_amount)
        
        # 测试锁定部分资金
        lock_amount = D("300")
        result = account.lock_asset(quote_asset, lock_amount)
        
        # 验证结果
        assert result is True
        
        # 验证余额更新
        balance = account.get_balance(quote_asset)
        assert balance.free == initial_amount - lock_amount
        assert balance.locked == lock_amount
        assert balance.total == initial_amount  # 总额不变
        
        # 验证交易记录 - 只有存款交易，锁定不产生交易记录
        assert len(account.transactions) == 1
        
        # 测试锁定金额超过可用余额
        exceed_amount = balance.free + D("100")
        assert account.lock_asset(quote_asset, exceed_amount) is False
        
        # 测试锁定金额为零或负数
        assert account.lock_asset(quote_asset, D(0)) is False
        assert account.lock_asset(quote_asset, D("-10")) is False
        
        # 余额不应该变化
        assert account.get_balance(quote_asset).free == initial_amount - lock_amount
        assert account.get_balance(quote_asset).locked == lock_amount
    
    def test_unlock_asset(self, account_manager, user_id, quote_asset):
        """测试资产解冻 (AC-005)"""
        # 创建账户，存入并锁定资金
        account = account_manager.create_account(user_id)
        initial_amount = D("1000")
        account.deposit(quote_asset, initial_amount)
        lock_amount = D("400")
        account.lock_asset(quote_asset, lock_amount)
        
        # 测试解锁部分资金
        unlock_amount = D("150")
        result = account.unlock_asset(quote_asset, unlock_amount)
        
        # 验证结果
        assert result is True
        
        # 验证余额更新
        balance = account.get_balance(quote_asset)
        assert balance.free == initial_amount - lock_amount + unlock_amount
        assert balance.locked == lock_amount - unlock_amount
        assert balance.total == initial_amount  # 总额不变
        
        # 测试解锁金额超过锁定余额
        exceed_amount = balance.locked + D("100")
        assert account.unlock_asset(quote_asset, exceed_amount) is False
        
        # 测试解锁金额为零或负数
        assert account.unlock_asset(quote_asset, D(0)) is False
        assert account.unlock_asset(quote_asset, D("-10")) is False
        
        # 余额不应该变化
        assert account.get_balance(quote_asset).free == initial_amount - lock_amount + unlock_amount
        assert account.get_balance(quote_asset).locked == lock_amount - unlock_amount
    
    def test_order_funds_processing(self, account_manager, user_id, symbol, base_asset, quote_asset):
        """测试订单资金处理 (AC-006)"""
        # 创建账户并存入资金
        account = account_manager.create_account(user_id)
        account.deposit(base_asset, D("10"))  # 10 BTC
        account.deposit(quote_asset, D("50000"))  # 50000 USDT
        
        # 添加交易对
        account_manager.add_active_symbol(symbol)
        
        # 测试买单锁定资金 (锁定USDT)
        buy_amount = D("2.5")  # 买入2.5 BTC
        buy_price = D("20000")  # 单价20000 USDT
        buy_value = buy_amount * buy_price  # 总价50000 USDT
        
        result = account_manager.lock_funds_for_order(
            user_id, symbol, "BUY", buy_amount, buy_price,
            base_asset, quote_asset
        )
        
        # 验证结果
        assert result is True
        
        # 验证买单锁定了USDT
        quote_balance = account.get_balance(quote_asset)
        assert quote_balance.free == D("50000") - buy_value
        assert quote_balance.locked == buy_value
        
        # 测试卖单锁定资金 (锁定BTC)
        sell_amount = D("5")  # 卖出5 BTC
        sell_price = D("21000")  # 单价21000 USDT
        
        result = account_manager.lock_funds_for_order(
            user_id, symbol, "SELL", sell_amount, sell_price,
            base_asset, quote_asset
        )
        
        # 验证结果
        assert result is True
        
        # 验证卖单锁定了BTC
        base_balance = account.get_balance(base_asset)
        assert base_balance.free == D("10") - sell_amount
        assert base_balance.locked == sell_amount
        
        # 测试取消买单 (解锁USDT)
        result = account_manager.unlock_funds_for_order(
            user_id, symbol, "BUY", buy_amount, buy_price,
            base_asset, quote_asset
        )
        
        # 验证结果
        assert result is True
        
        # 验证解锁了USDT
        quote_balance = account.get_balance(quote_asset)
        assert quote_balance.free == D("50000")
        assert quote_balance.locked == D("0")
        
        # 测试取消卖单 (解锁BTC)
        result = account_manager.unlock_funds_for_order(
            user_id, symbol, "SELL", sell_amount, sell_price,
            base_asset, quote_asset
        )
        
        # 验证结果
        assert result is True
        
        # 验证解锁了BTC
        base_balance = account.get_balance(base_asset)
        assert base_balance.free == D("10")
        assert base_balance.locked == D("0")
    
    def test_balance_query(self, account_manager, user_id):
        """测试余额查询 (AC-007)"""
        # 创建账户并存入多种资产
        account = account_manager.create_account(user_id)
        account.deposit("BTC", D("5.5"))
        account.deposit("ETH", D("50"))
        account.deposit("USDT", D("10000"))
        
        # 锁定部分资产
        account.lock_asset("BTC", D("2"))
        account.lock_asset("USDT", D("3000"))
        
        # 验证获取余额
        btc_balance = account.get_balance("BTC")
        assert btc_balance.asset == "BTC"
        assert btc_balance.free == D("3.5")
        assert btc_balance.locked == D("2")
        assert btc_balance.total == D("5.5")
        
        eth_balance = account.get_balance("ETH")
        assert eth_balance.asset == "ETH"
        assert eth_balance.free == D("50")
        assert eth_balance.locked == D("0")
        assert eth_balance.total == D("50")
        
        usdt_balance = account.get_balance("USDT")
        assert usdt_balance.asset == "USDT"
        assert usdt_balance.free == D("7000")
        assert usdt_balance.locked == D("3000")
        assert usdt_balance.total == D("10000")
        
        # 验证不存在的资产将返回零余额
        xrp_balance = account.get_balance("XRP")
        assert xrp_balance.asset == "XRP"
        assert xrp_balance.free == D("0")
        assert xrp_balance.locked == D("0")
        assert xrp_balance.total == D("0")
        
        # 验证账户快照
        snapshot = account.get_account_snapshot()
        assert len(snapshot["balances"]) == 3  # BTC, ETH, USDT
        assert len(snapshot["positions"]) == 0  # 没有持仓
        assert snapshot["userId"] == user_id
    
    def test_fee_calculation(self, account_manager, user_id, symbol, base_asset, quote_asset):
        """测试交易手续费计算 (AC-008)"""
        # 创建账户并存入资金
        account = account_manager.create_account(user_id)
        account.deposit(base_asset, D("10"))  # 10 BTC
        account.deposit(quote_asset, D("50000"))  # 50000 USDT
        
        # 添加交易对
        account_manager.add_active_symbol(symbol)
        
        # 测试买入并计算手续费（以USDT支付）
        buy_amount = D("2")  # 买入2 BTC
        buy_price = D("20000")  # 单价20000 USDT
        fee_rate = D("0.001")  # 手续费率0.1%
        fee = buy_amount * buy_price * fee_rate  # 手续费40 USDT
        
        # 先锁定资金
        account_manager.lock_funds_for_order(
            user_id, symbol, "BUY", buy_amount, buy_price,
            base_asset, quote_asset
        )
        
        # 结算交易
        result = account_manager.settle_trade(
            user_id, symbol, "BUY", buy_amount, buy_price,
            fee, quote_asset,  # 手续费以USDT支付
            base_asset, quote_asset
        )
        
        # 验证结果
        assert result is True
        
        # 验证BTC增加
        base_balance = account.get_balance(base_asset)
        assert base_balance.free == D("10") + buy_amount
        
        # 验证USDT减少（包括手续费）
        quote_balance = account.get_balance(quote_asset)
        expected_quote = D("50000") - (buy_amount * buy_price) - fee
        assert quote_balance.free == expected_quote
        assert quote_balance.locked == D("0")  # 锁定的已经解锁并扣除
        
        # 测试卖出并计算手续费（以BTC支付）
        sell_amount = D("1")  # 卖出1 BTC
        sell_price = D("21000")  # 单价21000 USDT
        fee_rate = D("0.001")  # 手续费率0.1%
        fee = sell_amount * fee_rate  # 手续费0.001 BTC
        
        # 先锁定资金
        account_manager.lock_funds_for_order(
            user_id, symbol, "SELL", sell_amount, sell_price,
            base_asset, quote_asset
        )
        
        # 结算交易
        result = account_manager.settle_trade(
            user_id, symbol, "SELL", sell_amount, sell_price,
            fee, base_asset,  # 手续费以BTC支付
            base_asset, quote_asset
        )
        
        # 验证结果
        assert result is True
        
        # 验证BTC减少（包括手续费）
        base_balance = account.get_balance(base_asset)
        expected_base = D("10") + buy_amount - sell_amount - fee
        assert base_balance.free == expected_base
        assert base_balance.locked == D("0")  # 锁定的已经解锁并扣除
        
        # 验证USDT增加
        quote_balance = account.get_balance(quote_asset)
        expected_quote += sell_amount * sell_price
        assert quote_balance.free == expected_quote
    
    def test_insufficient_balance(self, account_manager, user_id, symbol, base_asset, quote_asset):
        """测试余额不足处理 (AC-009)"""
        # 创建账户并存入有限资金
        account = account_manager.create_account(user_id)
        account.deposit(base_asset, D("1"))  # 1 BTC
        account.deposit(quote_asset, D("5000"))  # 5000 USDT
        
        # 添加交易对
        account_manager.add_active_symbol(symbol)
        
        # 测试买入金额超过余额
        buy_amount = D("2")  # 买入2 BTC
        buy_price = D("20000")  # 单价20000 USDT，总价40000 USDT > 5000 USDT
        
        # 尝试锁定资金
        result = account_manager.lock_funds_for_order(
            user_id, symbol, "BUY", buy_amount, buy_price,
            base_asset, quote_asset
        )
        
        # 验证结果 - 应该失败
        assert result is False
        
        # 验证USDT余额未变化
        quote_balance = account.get_balance(quote_asset)
        assert quote_balance.free == D("5000")
        assert quote_balance.locked == D("0")
        
        # 测试卖出数量超过余额
        sell_amount = D("1.5")  # 卖出1.5 BTC > 1 BTC
        sell_price = D("21000")  # 单价21000 USDT
        
        # 尝试锁定资金
        result = account_manager.lock_funds_for_order(
            user_id, symbol, "SELL", sell_amount, sell_price,
            base_asset, quote_asset
        )
        
        # 验证结果 - 应该失败
        assert result is False
        
        # 验证BTC余额未变化
        base_balance = account.get_balance(base_asset)
        assert base_balance.free == D("1")
        assert base_balance.locked == D("0")
        
        # 测试取款金额超过余额
        assert account.withdraw(quote_asset, D("6000")) is False
        assert account.withdraw(base_asset, D("2")) is False
        
        # 验证余额未变化
        assert account.get_balance(quote_asset).free == D("5000")
        assert account.get_balance(base_asset).free == D("1")
    
    def test_trade_settlement(self, account_manager, user_id, symbol, base_asset, quote_asset):
        """测试成交结算 (AC-010)"""
        # 创建账户并存入资金
        account = account_manager.create_account(user_id)
        account.deposit(base_asset, D("5"))  # 5 BTC
        account.deposit(quote_asset, D("100000"))  # 100000 USDT
        
        # 添加交易对
        account_manager.add_active_symbol(symbol)
        
        # 准备买入订单
        buy_amount = D("2")  # 买入2 BTC
        buy_price = D("20000")  # 单价20000 USDT
        
        # 锁定买入资金
        account_manager.lock_funds_for_order(
            user_id, symbol, "BUY", buy_amount, buy_price,
            base_asset, quote_asset
        )
        
        # 验证锁定状态
        quote_balance = account.get_balance(quote_asset)
        locked_amount = buy_amount * buy_price
        assert quote_balance.locked == locked_amount
        
        # 执行结算（完全成交）
        result = account_manager.settle_trade(
            user_id, symbol, "BUY", buy_amount, buy_price,
            D("0"), quote_asset,  # 简化测试，不计算手续费
            base_asset, quote_asset
        )
        
        # 验证结果
        assert result is True
        
        # 验证BTC增加
        base_balance = account.get_balance(base_asset)
        assert base_balance.free == D("7")  # 5 + 2
        
        # 验证USDT减少
        quote_balance = account.get_balance(quote_asset)
        assert quote_balance.free == D("100000") - buy_amount * buy_price
        assert quote_balance.locked == D("0")  # 锁定已解除
        
        # 验证交易记录
        trade_transaction = None
        for txn in account.transactions:
            if txn.transaction_type == "TRADE":
                trade_transaction = txn
                break
                
        assert trade_transaction is not None
        assert trade_transaction.asset == base_asset
        assert trade_transaction.amount == buy_amount
        assert "price" in trade_transaction.details
        assert trade_transaction.details["price"] == buy_price
        
        # 测试部分成交
        sell_amount = D("3")  # 卖出3 BTC
        sell_price = D("21000")  # 单价21000 USDT
        
        # 锁定卖出资金
        account_manager.lock_funds_for_order(
            user_id, symbol, "SELL", sell_amount, sell_price,
            base_asset, quote_asset
        )
        
        # 验证锁定状态
        base_balance = account.get_balance(base_asset)
        assert base_balance.locked == sell_amount
        
        # 执行部分结算（部分成交1.5 BTC）
        partial_amount = D("1.5")
        result = account_manager.settle_trade(
            user_id, symbol, "SELL", partial_amount, sell_price,
            D("0"), base_asset,  # 简化测试，不计算手续费
            base_asset, quote_asset
        )
        
        # 验证结果
        assert result is True
        
        # 验证BTC部分减少，部分仍锁定
        base_balance = account.get_balance(base_asset)
        assert base_balance.free == D("4")  # 7 - 3(锁定全部) 
        assert base_balance.locked == D("1.5")  # 3 - 1.5(部分结算)
        
        # 验证USDT增加
        quote_balance = account.get_balance(quote_asset)
        quote_increase = partial_amount * sell_price
        expected_quote = D("100000") - (buy_amount * buy_price) + quote_increase
        assert quote_balance.free == expected_quote
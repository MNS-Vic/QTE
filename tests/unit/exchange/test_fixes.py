#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试修复后的问题
"""
import pytest
from decimal import Decimal
from qte.exchange.account.account_manager import AccountManager, UserAccount, AssetBalance

# 使用Decimal确保精确计算
D = lambda x: Decimal(str(x))

class TestAccountManagerFixes:
    """测试账户管理器修复"""
    
    @pytest.fixture
    def account_manager(self):
        """创建账户管理器实例"""
        return AccountManager()
    
    @pytest.fixture
    def test_account(self, account_manager):
        """创建测试账户"""
        return account_manager.create_account("test_user")
    
    def test_lock_asset_no_transaction_record(self, test_account):
        """测试修复AC-001: 锁定资产不应该产生交易记录"""
        # 存入资金
        test_account.deposit("USDT", D("1000"))
        
        # 记录原始交易数量
        original_transaction_count = len(test_account.transactions)
        
        # 锁定资产
        test_account.lock_asset("USDT", D("500"))
        
        # 验证交易记录数量未增加
        assert len(test_account.transactions) == original_transaction_count
    
    def test_unlock_asset_no_transaction_record(self, test_account):
        """测试修复AC-001的延伸: 解锁资产不应该产生交易记录"""
        # 存入并锁定资金
        test_account.deposit("USDT", D("1000"))
        test_account.lock_asset("USDT", D("500"))
        
        # 记录原始交易数量
        original_transaction_count = len(test_account.transactions)
        
        # 解锁资产
        test_account.unlock_asset("USDT", D("200"))
        
        # 验证交易记录数量未增加
        assert len(test_account.transactions) == original_transaction_count
    
    def test_account_snapshot_no_zero_balances(self, test_account):
        """测试修复AC-002: 账户快照不应包含零余额资产"""
        # 添加一些资产
        test_account.deposit("USDT", D("1000"))
        test_account.deposit("BTC", D("0"))  # 零余额资产
        test_account.deposit("ETH", D("0.5"))
        
        # 获取账户快照
        snapshot = test_account.get_account_snapshot()
        
        # 验证零余额资产不在快照中
        assert "USDT" in snapshot["balances"]
        assert "ETH" in snapshot["balances"]
        assert "BTC" not in snapshot["balances"]

from qte.exchange.rest_api.rest_server import ExchangeRESTServer
from qte.exchange.matching.matching_engine import MatchingEngine
from unittest.mock import MagicMock
from flask import Flask
import json

class TestRESTServerFixes:
    """测试REST服务器修复"""
    
    @pytest.fixture
    def setup_components(self):
        """设置测试组件"""
        self.matching_engine = MagicMock()
        self.account_manager = MagicMock()
        self.server = ExchangeRESTServer(
            matching_engine=self.matching_engine,
            account_manager=self.account_manager,
            host="localhost",
            port=5000
        )
        self.client = self.server.app.test_client()
        
        # 添加测试用户和API密钥
        self.test_user_id = "test_user"
        self.test_api_key = self.server.create_api_key(self.test_user_id)
        
        return self.server
    
    def test_authentication(self, setup_components):
        """测试修复REST-001: API认证问题"""
        # 测试无API密钥的情况
        response = self.client.get('/api/v1/account')
        assert response.status_code == 401
        
        # 测试无效API密钥的情况
        response = self.client.get('/api/v1/account', headers={'X-API-KEY': 'invalid_key'})
        assert response.status_code == 401
        
        # 测试有效API密钥的情况
        # 模拟账户信息
        mock_snapshot = {
            "user_id": self.test_user_id,
            "balances": {"USDT": {"free": 1000.0, "locked": 0.0}}
        }
        self.account_manager.get_account.return_value = MagicMock()
        self.account_manager.get_account().get_account_snapshot.return_value = mock_snapshot
        
        # 进行请求
        response = self.client.get('/api/v1/account', headers={'X-API-KEY': self.test_api_key})
        
        # 验证响应
        assert response.status_code == 200
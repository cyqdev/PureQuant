import ccxt
from ccxt import *


class EXCHANGE:

    def __init__(self, platform, apikey, secret, symbol, password=None):
        """
        使用CCXT框架中的交易所
        :param platform: 平台名称，例如"okex"
        :param apikey: api key
        :param secret: secret key
        :param symbol: 交易对
        :param password: okex需要传入passphrase
        """
        if platform not in ccxt.exchanges:
            print("CCXT暂不支持此交易所！CCXt目前支持的交易所是以下这些：")
            print([i for i in ccxt.exchanges])
            exit()
        self.symbol = symbol
        self.exchange = eval(platform)({
            'apiKey': apikey,
            'secret': secret,
            'password': password
        }) if password else eval(platform)({
            'apiKey': apikey,
            'secret': secret
        })
        symbol_list = []
        for item in self.exchange.fetch_markets():
            symbol_list.append(item['symbol'])
        if symbol not in symbol_list:
            print("{}交易所暂不支持此币对！{}交易所目前支持的币对有以下这些：".format(platform, platform))
            print(symbol_list)
            exit()

    def fetchOrderBook(self):
        """交易委托账本"""
        return self.exchange.fetchOrderBook(self.symbol)

    def fetch_order_book(self, limit):
        """市场深度"""
        return self.exchange.fetch_order_book(self.symbol, limit)

    def fetchTicker(self):
        """查询指定交易对实时行情"""
        return self.exchange.fetchTicker(self.symbol)

    def fetchTickers(self):
        """查询所有交易对实时行情"""
        return self.exchange.fetchTickers()

    def fetchTrade(self):
        """查询交易,获取指定交易对的最近交易记录"""
        return self.exchange.fetch_trades(self.symbol)

    def fetch_balance(self):
        """查询账户余额"""
        return self.exchange.fetch_balance()

    def fetchTrades(self):
        """查询交易 """
        return self.exchange.fetchTrades(self.symbol)

    def fetchOrder(self, order_id):
        """查询指定ID的委托单"""
        return self.exchange.fetchOrder(id=order_id, symbol=self.symbol)

    def fetchOrders(self):
        """查询全部委托单"""
        if (self.exchange.has['fetchOrders']):
            return self.exchange.fetchOrders()
        else:
            return "此交易所不支持此功能！"

    def fetchOpenOrders(self):
        """查询全部敞口委托单"""
        if (self.exchange.has['fetchOpenOrders']):
            return self.exchange.fetchOpenOrders(self.symbol)
        else:
            return "此交易所不支持此功能！"

    def fetchClosedOrders(self):
        """查询全部已完结委托单"""
        if (self.exchange.has['fetchClosedOrders']):
            return self.exchange.fetchClosedOrders(self.symbol)
        else:
            return "此交易所不支持此功能！"

    def create_order(self, type, side, amount, price=None):
        """
        委托下单
        :param type: 委托单类型，例如：'limit', ccxt库目前仅仅统一了市价单和限价单的API
        :param side:委托单的交易方向，买入还是卖出。例如：'buy'
        :param amount:你希望交易的数量。
        :param price:你希望为交易支付的报价货币的数量，仅限于限价单
        :return:可以使用一个变量来接收返回的下单信息并取出这笔订单的order id。例如：info = exchange.create_order(...)['id']
        """
        return self.exchange.create_order(symbol=self.symbol, type=type, side=side, amount=amount, price=price)

    def create_market_buy_order(self, amount):
        """市价买入委托"""
        return self.exchange.create_market_buy_order(self.symbol, amount)

    def create_market_sell_order(self, amount):
        """市价卖出委托"""
        return self.exchange.create_market_sell_order(self.symbol, amount)

    def create_limit_buy_order(self, amount):
        """限价买入委托"""
        return self.exchange.create_limit_buy_order(self.symbol, amount)

    def create_limit_sell_order(self, amount):
        """限价卖出委托"""
        return self.exchange.create_limit_sell_order(self.symbol, amount)

    def cancel_order(self, order_id):
        """取消委托单"""
        return self.exchange.cancel_order(order_id, self.symbol)

    def fetch_my_trades(self):
        """查询个人的历史交易"""
        if self.exchange.has['fetchMyTrades']:
            return self.exchange.fetch_my_trades(self.symbol)

    def fetchDepositAddress(self, code):
        """
        获取充值地址
        :param code: 统一的货币代码，大写字符串
        :return:
        """
        if self.exchange.has['fetchDepositAddress']:
            return self.exchange.fetchDepositAddress(code)
        elif self.exchange.has['createDepositAddress']:
            return self.exchange.createDepositAddress(code)

    def withdraw(self, code, amount, address, tag=None):
        """
        提现
        :param code: 统一的货币代码，大写字符串
        :param amount: 数量
        :param address: 地址
        :param tag: 标签
        :return:
        """
        return self.exchange.withdraw(code, amount, address, tag=tag)

    def fetchDeposits(self, code=None, since=None, limit=None):
        """查询充值记录"""
        if self.exchange.has['fetchDeposits']:
            deposits = self.exchange.fetch_deposits(code=code, since=since, limit=limit)
            return deposits
        else:
            raise Exception(self.exchange.id + ' does not have the fetch_deposits method')

    def fetchWithdrawals(self, code=None, since=None, limit=None):
        """查询提现记录"""
        if self.exchange.has['fetchWithdrawals']:
            withdrawals = self.exchange.fetch_withdrawals(code=code, since=since, limit=limit)
            return withdrawals
        else:
            raise Exception(self.exchange.id + ' does not have the fetch_withdrawals method')

    def fetchTransactions(self, code=None, since=None, limit=None):
        """查询链上交易"""
        if self.exchange.has['fetchTransactions']:
            transactions = self.exchange.fetch_transactions(code=code, since=since, limit=limit)
            return transactions
        else:
            raise Exception(self.exchange.id + ' does not have the fetch_transactions method')

    def fetchTradingFees(self):
        """查询交易手续费"""
        return self.exchange.fetchTradingFees(self.symbol)

    def fetchFundingFees(self):
        """查询资金操作手续费"""
        return self.exchange.fetchFundingFees()

    def fetchStatus(self):
        """查询交易所状态"""
        return self.exchange.fetchStatus()

    def currencies(self):
        """资金操作费"""
        return self.exchange.currencies

    def fetch_markets(self):
        """获取此交易所的所有交易对信息"""
        return self.exchange.fetch_markets()

    def fetchLedger(self, code):
        """
        查询账本
        :param code: 统一的货币代码，大写字符串
        :return:
        """
        return self.exchange.fetchLedger(code)

    def fetch_all_supported_symbols(self):
        """获取此交易所支持的所有交易对名称列表"""
        symbols_list = []
        for item in self.exchange.fetch_markets():
            symbols_list.append(item['symbol'])
        return symbols_list

    def get_kline(self, time_frame):
        """获取k线数据"""
        records = self.exchange.fetch_ohlcv(symbol=self.symbol, timeframe=time_frame)
        records.reverse()
        return records


if __name__ == '__main__':
    exchange = EXCHANGE(
        platform="okex",
        apikey="",
        secret="",
        symbol="BTC/USDT",
        password="")

    info = exchange.get_kline("1d")
    print(info)
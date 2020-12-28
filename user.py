import random
from decimal import Decimal

import tinvest
from tinvest import SandboxRegisterRequest, BrokerAccountType, SandboxSetCurrencyBalanceRequest, SandboxCurrency, \
    OperationType, LimitOrderRequest

import settings


class User:
    def __init__(self):
        self.client = tinvest.SyncClient(settings.__TINKOFF_API__, use_sandbox=True)

        self.client.clear_sandbox_account()

        xx = SandboxRegisterRequest(broker_account_type=BrokerAccountType.tinkoff)
        self.client.register_sandbox_account(xx)

        self.our_currency = {'rub': SandboxCurrency.rub, 'eur': SandboxCurrency.eur, 'usd': SandboxCurrency.usd}

        self.messages_properties = {'usd': 'Долларов', 'rub': 'Рублей', 'eur': 'Евро'}

        print('Создали новый акк')

    def top_up_balance(self, balance, curr):
        current_balance = self.get_balance(beatiful=False)
        already_have = current_balance[curr]
        a = SandboxSetCurrencyBalanceRequest(balance=Decimal(balance) + already_have,
                                             currency=self.our_currency.get(curr, SandboxCurrency.rub))
        self.client.set_sandbox_currencies_balance(a)
        return True

    def get_balance(self, beatiful=True):
        portfolio = self.client.get_portfolio_currencies()
        sum_dict = {
            self.messages_properties.get(x.currency.name, x.currency.name) if beatiful else x.currency.name: x.balance
            for x in portfolio.payload.currencies}
        return sum_dict

    def get_list_stocks(self):
        a = self.client.get_market_stocks()
        x = a.payload.instruments[0]
        l = [(i.name, i.ticker) for i in a.payload.instruments]
        random.shuffle(l)
        return l[:10]

    def search_by_ticker(self, ticker='AAPL'):
        a = self.client.get_market_search_by_ticker(ticker=ticker)
        ans = ''
        for i in a.payload.instruments:
            ans += '{0}: {1}\n'.format(i.ticker, i.name)
        return 'Ничего не найдено' if ans == '' else ans

    def show_price_list(self, ticker):
        a = self.client.get_market_search_by_ticker(ticker=ticker)
        if len(a.payload.instruments) == 1:
            self.figi = a.payload.instruments[0].figi
            print('figi = ' + self.figi)
            market = self.client.get_market_orderbook(figi=self.figi, depth=5)
            data = []
            for i in market.payload.asks:
                data.append([i.price, i.quantity])

            return data, self.messages_properties[a.payload.instruments[0].currency.name]
        else:
            return False

    def buy_by_ticker(self, price, cnt):
        try:
            aa = LimitOrderRequest(lots=cnt, operation=OperationType.buy, price=price)
            self.client.post_orders_limit_order(figi=self.figi, body=aa)
            return True
        except Exception:
            return False

    def get_my_stocks(self):
        portfolio = self.client.get_portfolio()
        my_stocks = []
        for info in portfolio.payload.positions:
            print(info.instrument_type.name)
            if info.instrument_type.name == 'stock':
                my_stocks.append({'ticker': info.ticker,
                                  'name': info.name,
                                  'lots': info.lots,
                                  'cnt': info.balance})
        print(portfolio)
        return my_stocks

    def test(self):
        # Поиск акций по тикеру
        a = self.client.get_market_search_by_ticker(ticker='AAPL')
        # print(a)

        # Список всех акций
        a = self.client.get_market_stocks()
        print(len(a.payload.instruments))
        # Список всех облигаций
        a = self.client.get_market_bonds()

        # Список фондов
        a = self.client.get_market_etfs()

        # Вывод заявок на продажу
        a = self.client.get_market_orderbook(figi='BBG000B9XRY4', depth=10)

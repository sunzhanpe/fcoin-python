# coding=utf-8

import threading
import time
from fcoin3 import Fcoin
from config import Api
from config import Config


# 已成交
filled = 'filled'
# 未成交
submitted = 'submitted'
# 买金额
buy_amount = Config['buy_amount']
# 卖金额
sell_amount = Config['sell_amount']
# 交易对
symbol = Config['symbol']
#止盈
zhiying = Config['zhiying']
#止损
zhisun = Config['zhisun']


# 初始化
fcoin = Fcoin()

# 授权
api_key = Api['key']
api_secret = Api['secret']
fcoin.auth(api_key, api_secret)


# 获取交易对的筹码类型
def get_symbol_type(this_symbol):
    types = dict(ftusdt='ft', btcusdt='btc', ethusdt='eth', bchusdt='bch', ltcusdt='ltc', etcusdt='etc')

    return types[this_symbol]


# 取小数，不四舍五入
def get_float(value, length):
    if type(value) is not float:
        value = str(value)
    flag = '.'
    point = value.find(flag)
    length = int(length) + point
    value = value[0:point] + value[point:length + 1]

    return float(value)


# 查询账户余额
# 支持 zil omg btc icx eth btm bch ltc usdt ft zip etc
def get_balance_action(this_symbol):
    balance_info = fcoin.get_balance()
    if balance_info is None:
        pass
    elif 'data' in balance_info and len(balance_info['data']):
        for item in balance_info['data']:
            if item['currency'] == this_symbol:
                balance = item
                label = this_symbol.upper()
                print(label, '账户余额', balance['balance'], '可用', balance['available'], '冻结', balance['frozen'])

                return balance['available']
    else:
        pass


# 获取订单列表
def get_order_list(this_symbol, this_states):
    order_list = fcoin.list_orders(symbol=this_symbol, states=this_states)
    if this_states == filled:
        print('已成交订单列表：')
    elif this_states == submitted:
        print('未成交订单列表：')
    for order in order_list['data']:
        print('订单ID', order['id'], '挂单价格', order['price'], '挂单数量', order['amount'], '方向', order['side'])
        if this_states == submitted:
            print('开始取消订单')
            cancel_order_action(order['id'])


# 获取订单列表第一个订单
def get_order_list_first(this_symbol, this_states):
    order_list = fcoin.list_orders(symbol=this_symbol, states=this_states)
    if order_list is None:
        pass
    elif 'data' in order_list and len(order_list['data']):
        order_item = order_list['data'][0]

        if order_item:
            order_price = float(order_item['price'])
            if this_states == submitted:
                print('发现未成交订单，尝试先取消委托订单')
                cancel_order_action(order_item['id'])
            elif this_states == filled:
                now_price = get_ticker(symbol)
                if order_item['side'] == 'buy':
                    print('尝试卖出')
                    if now_price >= order_price + zhisun * order_price:
                        print('卖出损失小于赚的手续费，尝试卖出')
                        current_amount = get_balance_action(get_symbol_type(this_symbol))
                        if sell_amount > current_amount:
                            # 卖出当前所有可用余额
                            sell_action(symbol, now_price, current_amount)
                        else:
                            # 卖出固定量
                            sell_action(symbol, now_price, sell_amount)
                    else:
                        print('卖出损失较大，不操作')
                elif order_item['side'] == 'sell':
                    # 这里只判断卖出价格高于买入价格
                    print('尝试买入')
                    # 直接买入
                    # now_price <= order_price or
                    if now_price <= order_price + zhiying * order_price:
                        print('买入损失小于赚的手续费，尝试买入')
                        buy_action(symbol, now_price, buy_amount)
                    else:
                        print('买入损失较大，不操作')
    else:
        if this_states == submitted:
            print('没有发现未成交订单')
            get_order_list_first(this_symbol, filled)
        elif this_states == filled:
            now_price = get_ticker(symbol)
            print('初次现价买入')
            buy_action(symbol, now_price, buy_amount)


# 查询订单
def check_order_state(this_order_id):
    check_info = fcoin.get_order(this_order_id)
    return check_info['data']


# 买操作
def buy_action(this_symbol, this_price, this_amount):
    buy_result = fcoin.buy(this_symbol, this_price, this_amount)
    if buy_result is None:
        print("没有买到或者余额不足")
        return True
    buy_order_id = buy_result['data']
    if buy_order_id:
        print('买单', this_price, '价格成功委托', '订单ID', buy_order_id)

    # 输出订单信息
    # print(fcoin.get_order(buy_order_id))
    return buy_order_id


# 卖操作
def sell_action(this_symbol, this_price, this_amount):
    this_amount = get_float(this_amount, 2)
    sell_result = fcoin.sell(this_symbol, this_price, this_amount)
    if sell_result is None:
        pass
    else:
        sell_order_id = sell_result['data']
        if sell_order_id:
            print('卖单', this_price, '价格成功委托', '订单ID', sell_order_id)

        # 输出订单信息
        # print(fcoin.get_order(sell_order_id))
        return sell_order_id


# 撤销订单
def cancel_order_action(this_order_id):
    cancel_info = fcoin.cancel_order(this_order_id)
    # if cancel_info['status'] == 0:
    #     print('成功撤销订单', this_order_id)


# 获取行情
def get_ticker(this_symbol):
    ticker = fcoin.get_market_ticker(symbol)
    now_price = ticker['data']['ticker'][0]
    print('最新成交价', now_price)

    return now_price


def robot():
    # 账户余额
    # get_balance_action('btc')
    # get_balance_action('usdt')
    # 获取委托订单列表
    get_order_list_first(symbol, submitted)


# 定时器
def timer():
    while True:
        robot()
        time.sleep(0)


# 守护进程
if __name__ == '__main__':
    t = threading.Thread(target=timer())
    t.start()
    t.join()

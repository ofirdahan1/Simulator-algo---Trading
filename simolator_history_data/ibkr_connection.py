import time, datetime
import queue
import threading
import pandas as pd
from enum import Enum,auto
from ibapi.client import EClient
from ibapi.wrapper import EWrapper

from ibapi.client import Contract
from ibapi.order import Order


# from lightweight_charts import Chart

from threading import Thread

INITIAL_SYMBOL = "DELL"
ACCOUNT_ID = ""
DEFAULT_HOST = '127.0.0.1'
DEFAULT_CLIENT_ID = 1

LIVE_TRADING = False
LIVE_TRADING_PORT = 4001
PAPER_TRADING_PORT = 4002
TRADING_PORT = PAPER_TRADING_PORT
if LIVE_TRADING:
    TRADING_PORT = LIVE_TRADING_PORT
    ACCOUNT_ID = ""

data_queue = queue.Queue()
tick_set = set()
time_a =0
time_b =0
stock_counter = 1
class TICKTYPE(Enum):
    BID_SIZE= 0
    BID_PRICE= auto()
    ASK_PRICE= auto()
    ASK_SIZE= auto()
    LAST_PRICE= auto()
    LAST_SIZE= auto()
    HIGH= auto()
    LOW= auto()
    VOLUME= auto()
    CLOSE= auto()
    BID_OPTION_COMPUTATION= auto()
    ASK_OPTION_COMPUTATION= auto()
    LAST_OPTION_COMPUTATION= auto()
    MODEL_OPTION= auto()
    OPEN= auto()
    LOW_13_WEEK= auto()
    HIGH_13_WEEK= auto()
    LOW_26_WEEK= auto()
    HIGH_26_WEEK= auto()
    LOW_52_WEEK= auto()
    HIGH_52_WEEK= auto()
    AVG_VOLUME= auto()
    OPEN_INTEREST= auto()
    OPTION_HISTORICAL_VOL= auto()
    OPTION_IMPLIED_VOL= auto()
    OPTION_BID_EXCH= auto()
    OPTION_ASK_EXCH= auto()
    OPTION_CALL_OPEN_INTEREST= auto()
    OPTION_PUT_OPEN_INTEREST= auto()
    OPTION_CALL_VOLUME= auto()
    OPTION_PUT_VOLUME= auto()
    INDEX_FUTURE_PREMIUM= auto()
    BID_EXCH= auto()
    ASK_EXCH= auto()
    AUCTION_VOLUME= auto()
    AUCTION_PRICE= auto()
    AUCTION_IMBALANCE= auto()
    MARK_PRICE= auto()
    BID_EFP_COMPUTATION= auto()
    ASK_EFP_COMPUTATION= auto()
    LAST_EFP_COMPUTATION= auto()
    OPEN_EFP_COMPUTATION= auto()
    HIGH_EFP_COMPUTATION= auto()
    LOW_EFP_COMPUTATION= auto()
    CLOSE_EFP_COMPUTATION= auto()
    LAST_TIMESTAMP= auto()
    SHORTABLE= auto()
    FUNDAMENTAL_RATIOS= auto()
    RT_VOLUME= auto()
    HALTED= auto()
    BID_YIELD= auto()
    ASK_YIELD= auto()
    LAST_YIELD= auto()
    CUST_OPTION_COMPUTATION= auto()
    TRADE_COUNT= auto()
    TRADE_RATE= auto()
    VOLUME_RATE= auto()
    LAST_RTH_TRADE= auto()
    RT_HISTORICAL_VOL= auto()
    IB_DIVIDENDS= auto()
    BOND_FACTOR_MULTIPLIER= auto()
    REGULATORY_IMBALANCE= auto()
    NEWS_TICK= auto()
    SHORT_TERM_VOLUME_3_MIN= auto()
    SHORT_TERM_VOLUME_5_MIN= auto()
    SHORT_TERM_VOLUME_10_MIN= auto()
    DELAYED_BID= auto()
    DELAYED_ASK= auto()
    DELAYED_LAST= auto()
    DELAYED_BID_SIZE= auto()
    DELAYED_ASK_SIZE= auto()
    DELAYED_LAST_SIZE= auto()
    DELAYED_HIGH= auto()
    DELAYED_LOW= auto()
    DELAYED_VOLUME= auto()
    DELAYED_CLOSE= auto()
    DELAYED_OPEN= auto()
    RT_TRD_VOLUME= auto()
    CREDITMAN_MARK_PRICE= auto()
    CREDITMAN_SLOW_MARK_PRICE= auto()
    DELAYED_BID_OPTION= auto()
    DELAYED_ASK_OPTION= auto()
    DELAYED_LAST_OPTION= auto()
    DELAYED_MODEL_OPTION= auto()
    LAST_EXCH= auto()
    LAST_REG_TIME= auto()
    FUTURES_OPEN_INTEREST= auto()
    AVG_OPT_VOLUME= auto()
    DELAYED_LAST_TIMESTAMP= auto()
    SHORTABLE_SHARES= auto()
    DELAYED_HALTED= auto()
    REUTERS_2_MUTUAL_FUNDS= auto()
    ETF_NAV_CLOSE= auto()
    ETF_NAV_PRIOR_CLOSE= auto()
    ETF_NAV_BID= auto()
    ETF_NAV_ASK= auto()
    ETF_NAV_LAST= auto()
    ETF_FROZEN_NAV_LAST= auto()
    ETF_NAV_HIGH= auto()
    ETF_NAV_LOW= auto()
    SOCIAL_MARKET_ANALYTICS= auto()
    ESTIMATED_IPO_MIDPOINT= auto()
    FINAL_IPO_LAST= auto()

class req_action():
    """this class is to uniq any stock action with a same reqId for the all the run"""
    HistoryMktData = 0
    RtData = 1
    Buy = 2
    Sell = 3
class req_account():
    """this class is to uniq any account action with a same reqId for the all the run"""
    SNAPSHOUT = 0
    RT_STREAM = 1
    UPDATE_PROTFOLIO = 2
class account_data():
    def __init__(self):
        self.Data = {}
        self.account_id = ACCOUNT_ID
    def __repr__(self):
        return self.Data

class RT_stock_data():
    def __init__(self,idx,name):
        self.idx_stock_list = idx
        self.reqId_group = idx*10
        self.name=name
        self.Data = {}
        self.action = 'None'
        self.status = 'None'

    def __repr__(self):
        # return f"bid_price:{self.bid_price} bid_size:{self.bid_size} ask_price:{self.ask_price} ask_size:{self.ask_size} last_price:{self.last_price} volume:{self.volume} high:{self.high} low:{self.low} open:{self.open} close:{self.close}"
        str_print = [ f", {key}:{val}" for key,val in self.Data.items()]
        str_print = "".join(str_print)
        return self.name+str_print
class IBClient(EWrapper, EClient):

    def __init__(self, host, port, client_id):
        EClient.__init__(self, self)

        self.key_lock = threading.Lock()
        self.key_lock_client = threading.Lock()
        self.key_lock_wrapper = threading.Lock()

        self.C_W_barriers = {}
        self.stocks_data = {}
        self.ordId_stock = {}
        self.account = account_data()

        self.available_order_id = 1
        self.active_order_id = []
        self.MarketDataType = 1

        self.connect(host, port, client_id)
        thread = Thread(target=self.run)
        thread.start()

    ######### EWrapper ###########

    def connectionClosed(self):
        self.tryReconnectIfNot()

    def error(self, req_id, code, msg, misc):
        if code in [2104, 2106, 2158]:
            print(msg)
        else:
            self.tryReconnectIfNot()
            print(f'req_id: {req_id} Error {code}: {msg}')

    # def nextValidId(self, orderId):
    #     self.available_order_id = orderId
    def tickPrice(self, reqId, tickType, price, attrib):  # L1 : {1, 2, 4, 6, 7, 9, 14}
        # with self.key_lock_wrapper:
        if reqId in self.ordId_stock:
            tick_type_name = TICKTYPE(tickType).name
            stock = self.ordId_stock[reqId]
            if tick_type_name not in self.stocks_data[stock].Data:
                self.stocks_data[stock].Data.update({tick_type_name:price})
            else:
                self.stocks_data[stock].Data[tick_type_name] = price
        # name = TickTypeEnum(tickType).name
        # if tickType == 0:
        #     self.stocks_data[self.ordId_stock[reqId]].bid_size = price
        #     # print(f"BID_SIZE: {price}")
        # elif tickType == 1:  # 1 corresponds to the bid price
        #     self.stocks_data[self.ordId_stock[reqId]].bid_price = price
        #     # print(f"Bid Price: {price}")
        # elif tickType == 2:  # 2 corresponds to the ask price
        #     self.stocks_data[self.ordId_stock[reqId]].ask_price = price
        #     # print(f"Ask Price: {price}")
        # elif tickType == 3:  # 3 corresponds to the ask size
        #     self.stocks_data[self.ordId_stock[reqId]].ask_size = price
        #     # print(f"ASK_SIZE: {price}")
        # elif tickType == 4:  # 4 corresponds to the last price
        #     self.stocks_data[self.ordId_stock[reqId]].last_price = price
        #     # print(f"LAST_PRICE: {price}")
        # elif tickType == 8:  # 8 corresponds to the last volume
        #     self.stocks_data[self.ordId_stock[reqId]].volume = price
        #     # print(f"VOLUME: {price}")
        # elif tickType == 6:  # 8 corresponds to the last volume
        #     self.stocks_data[self.ordId_stock[reqId]].high = price
        # elif tickType == 7:  # 8 corresponds to the last volume
        #     self.stocks_data[self.ordId_stock[reqId]].low = price
        # elif tickType == 9:  # 8 corresponds to the last volume
        #     self.stocks_data[self.ordId_stock[reqId]].close = price
        # elif tickType == 14:  # 8 corresponds to the last volume
        #     self.stocks_data[self.ordId_stock[reqId]].open = price
        # self.barrier_for_2_thread_base_on_ordId(reqId)

    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        self.stocks_data[self.ordId_stock[orderId]].status = status

    def contractDetails(self, reqId, contractDetails):
        print(f"ContractDetails: {contractDetails}")

    def historicalData(self, req_id, bar):
        print(bar)

        t = datetime.datetime.fromtimestamp(int(bar.date))

        # creation bar dictionary for each bar received
        data = {
            'date': t,
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': int(bar.volume)
        }
        print(data)

        # Put the data into the queue
        data_queue.put(data)

        # callback when all historical data has been received

    def historicalDataEnd(self, reqId, start, end):
        print(f"end of data {start} {end} , reqId:{reqId}")

    def accountSummary(self, reqId, account, tag, value, currency):
        with self.key_lock_wrapper:
            if 'USD' in currency and account in self.account.account_id:
                try:
                    if tag not in self.account.Data:
                        self.account.Data.update({tag:value})
                    else:
                        self.account.Data[tag] = value
                except:
                    raise ValueError(f"insted of float we got {value}")


    def updateAccountValue(self, key, value, currency, accountName):
        with self.key_lock_wrapper:
            if 'USD' in currency and accountName in self.account.account_id:
                try:
                    if key not in self.account.Data:
                        self.account.Data.update({key:value})
                    else:
                        self.account.Data[key] =value
                except:
                    raise ValueError(f"insted of float we got {value}")

    def updatePortfolio(self, contract, position, marketPrice, marketValue, averageCost, unrealizedPNL, realizedPNL, accountName):
        print(f"Contract: {contract.symbol}, Position: {position}, Market Price: {marketPrice}, Unrealized PnL: {unrealizedPNL}")

    def position(self, account, contract, position, avgCost):
        print(f"Account: {account}, Symbol: {contract.symbol}, Position: {position}, Avg Cost: {avgCost}")

    def pnl(self, reqId, dailyPnL, unrealizedPnL, realizedPnL):
        print(f"PnL - Daily: {dailyPnL}, Unrealized: {unrealizedPnL}, Realized: {realizedPnL}")

    ################################################# My FUN ################################################
    #### EXCEPTION #####
    def tryReconnectIfNot(self):
        if not self.isConnected():
            with self.key_lock_client:
                with self.key_lock_wrapper:
                    if not self.isConnected():
                        for attempt in range(5):
                            try:
                                print(f"Attempt {attempt} to reconnect...")
                                self.connect(DEFAULT_HOST, TRADING_PORT, DEFAULT_CLIENT_ID)
                                self.run()
                                if self.isConnected():
                                    print("Reconnection successful.")
                                    break
                            except Exception as e:
                                print(f"Reconnection attempt {attempt} failed: {e}")
                                time.sleep(3)
                        else:
                            print("Max reconnection attempts reached. Exiting.")
    ###REWRITE CANCEL CLIENT REQUESTS ####
    
    def cancel_order(self,reqId):
        with self.key_lock_client:
            self.cancelOrder(reqId)
        time.sleep(1)
    def cancel_account_summary(self, reqId:int):
        with self.key_lock_client:
            self.cancelAccountSummary(reqId)
        time.sleep(1)
    def cancel_positions(self):
        with self.key_lock_client:
            self.cancelPositions()
        time.sleep(1)
    def cancel_PnL(self, reqId: int):
        with self.key_lock_client:
            self.cancelPnL(reqId)
        time.sleep(1)
    def cancel_historical_data(self, reqId: int):
        with self.key_lock_client:
            self.cancelHistoricalData(reqId)
        time.sleep(1)
    def cancel_mkt_data(self, reqId: int):
        with self.key_lock_client:
            self.cancelMktData(reqId)
        time.sleep(1)

    def cancel_reqId(self, reqId:int):
        if reqId >= 10:
            reqId_modulo = reqId%10
            if reqId_modulo == req_action.HistoryMktData:
                self.cancel_historical_data(reqId)
            elif reqId_modulo == req_action.RtData:
                self.cancel_mkt_data(reqId)
            elif reqId_modulo == req_action.Buy:
                self.cancelOrder(reqId)
            elif reqId_modulo == req_action.Sell:
                self.cancelOrder(reqId)
        else:
            if reqId == req_account.SNAPSHOUT:
                self.cancel_account_summary(reqId)
            elif reqId == req_account.RT_STREAM:
                self.req_account_updates(False,ACCOUNT_ID)
            elif reqId == req_account.UPDATE_PROTFOLIO:
                self.cancel_positions()


    ### REWRITE DATA CLIENT REQUESTS ####
    def change_data_type(self,num:int):
        if num != self.MarketDataType:
            self.tryReconnectIfNot()
            with self.key_lock_client:
                self.MarketDataType = num
                client.reqMarketDataType(num)
            time.sleep(1)
    def place_order(self,reqId, contract, order):
        self.tryReconnectIfNot()
        with self.key_lock_client:
            self.placeOrder(reqId, contract, order)
        time.sleep(1)
    def req_account_summary(self,reqId,groupName = 'ALL',tags ="$LEDGER:USD"):
        self.tryReconnectIfNot()
        with self.key_lock_client:
            self.reqAccountSummary(reqId, groupName, tags)
        time.sleep(1)
    def req_account_updates(self,subscribe:bool, acctCode:str):
        self.tryReconnectIfNot()
        with self.key_lock_client:
            self.reqAccountUpdates(subscribe, acctCode)  #acctCode: Replace with your account ID Ex "U1234567"
        time.sleep(1)
    def req_account_positions(self):
        self.tryReconnectIfNot()
        with self.key_lock_client:
            self.reqPositions()
        time.sleep(1)
    def req_account_PnL(self,reqId: int, account: str, modelCode: str):
        self.tryReconnectIfNot()
        with self.key_lock_client:
            self.reqPnL(reqId, account, modelCode)  # Replace with your account ID
        time.sleep(1)
    def req_mkt_data(self, reqId, contract:Contract,genericTickList:str, snapshot:bool, regulatorySnapshot: bool,mktDataOptions):
        self.tryReconnectIfNot()
        with self.key_lock_client:
            self.reqMktData(reqId, contract, genericTickList, snapshot, regulatorySnapshot, mktDataOptions)
        time.sleep(1)



    ### FILL & RETURN CLIENT OBJECT DATA ####
    def create_order(self,action, quantity, orderType, price=None):
        order = Order()
        order.action = action
        order.totalQuantity = quantity
        order.orderType = orderType
        if price:
            order.lmtPrice = price
        # Set the manual cancel time (in a format accepted by IBKR)
        # order.manualCancelOrderTime = "2024-08-17 15:00:00"  # Example timestamp
        return order
    def create_stock_contract(self,symbol, exchange='SMART', currency='USD'):
        contract = Contract()
        contract.symbol = symbol
        contract.secType = 'STK'
        contract.exchange = exchange
        contract.currency = currency
        return contract



    ### USEFULL FUNCTION ####
    def constrain(self,val,min_val,max_val):
        return min(max_val,max(min_val,val))



    ### MANGING MY DATA STRUCTURE ###
    def add_stock_to_stock_list(self,stock:str):
        with self.key_lock_client:
            if stock not in self.stocks_data:
                global stock_counter
                self.stocks_data.update({stock:RT_stock_data(stock_counter,stock)})
                stock_counter += 1
    def add_ordId_stock(self,reqId,stock):
        with self.key_lock:
            if reqId not in self.ordId_stock:
                self.ordId_stock.update({reqId:stock})
            else:
                self.ordId_stock[reqId] = stock
    def remove_ordId_stock(self,reqId):
        with self.key_lock:
            self.ordId_stock.pop(reqId)
    def adding_req_barrier(self,reqId):
        with self.key_lock_client:
            if reqId not in self.C_W_barriers:
                self.C_W_barriers.update({reqId:threading.Barrier(2)})
    def remove_req_barrier(self,reqId):
        with self.key_lock:
            if reqId in self.C_W_barriers:
                self.C_W_barriers.pop(reqId)



    #### BARRIER SYCHRONIZATION ###
    def barrier_for_2_thread_base_on_ordId(self,reqId,thread = 'Wrapper'):
        if reqId in self.C_W_barriers:
            self.C_W_barriers[reqId].wait()
            self.remove_req_barrier(reqId)
        if 'C' in thread:
            print(f"{self.ordId_stock[reqId]}: ",self.stocks_data[self.ordId_stock[reqId]])

    #### MY ALGO ####
    def get_snap_account(self,time_wait_sec):
        status ='FAIL'
        reqId_account_data = req_account.SNAPSHOUT
        # self.adding_req_barrier(reqId_account_data)
        self.add_ordId_stock(reqId_account_data,'ACCOUNT')
        self.account.Data = {}
        self.req_account_summary(reqId_account_data,"All", "NetLiquidation,CashBalance,AvailableFunds,BuyingPower,TotalCashBalance,SettledCash,GrossPositionValue")
        data_types_needed = set("BuyingPower") #"NetLiquidation","CashBalance","AvailableFunds","BuyingPower","TotalCashBalance","SettledCash","GrossPositionValue"
        data_types_needed = set(["NetLiquidation", "CashBalance", "AvailableFunds", "BuyingPower", "TotalCashBalance"]) #"NetLiquidation","CashBalance","AvailableFunds","BuyingPower","TotalCashBalance","SettledCash","GrossPositionValue"
        time_start = time.time()
        while (time.time()-time_start) < time_wait_sec:
            data_types_received = set(self.account.Data.keys())
            if data_types_needed.issubset(data_types_received):
                status = 'SUCCESS'
                break
            time.sleep(1)
        self.cancel_account_summary(reqId_account_data)
        return status

        # self.barrier_for_2_thread_base_on_ordId(reqId_account_data, 'Client')
    def get_straming_acount(self,time_stream_sec):
        status = 'FAIL'
        reqId_account_data = req_account.RT_STREAM
        # data_types_needed = set("BuyingPower")  # "NetLiquidation","CashBalance","AvailableFunds","BuyingPower","TotalCashBalance","SettledCash","GrossPositionValue"
        data_types_needed = set(["NetLiquidation", "CashBalance", "AvailableFunds", "BuyingPower", "TotalCashBalance"])  # "NetLiquidation","CashBalance","AvailableFunds","BuyingPower","TotalCashBalance","SettledCash","GrossPositionValue"

        # self.adding_req_barrier(reqId_account_data)
        self.add_ordId_stock(reqId_account_data, 'ACCOUNT')
        self.account.Data = {}
        self.req_account_updates(True, ACCOUNT_ID)
        time_start_stream = time.time()
        while (time.time()-time_start_stream) < time_stream_sec:
            data_types_received = set(self.account.Data.keys())
            if data_types_needed.issubset(data_types_received):
                status = 'SUCCESS'
                break
            time.sleep(1)
        self.req_account_updates(False,ACCOUNT_ID)
        return status
    def req_update_stock_data(self,symbol,continues=False):
        self.change_data_type(1)
        contract = self.create_stock_contract(symbol)
        reqId_mkt_data = self.stocks_data[symbol].reqId_group+req_action.RtData
        # if not continues:
        #     self.adding_req_barrier(reqId)
        self.add_ordId_stock(reqId_mkt_data,symbol)
        self.req_mkt_data(reqId_mkt_data, contract, '', False, False, [])
        # if not continues:
        #     self.barrier_for_2_thread_base_on_ordId(reqId, 'Client')
        #     self.cancel_mkt_data(reqId)
        # return self.stocks_data[symbol].last_price

    def try_buy_sell_all(self, symbol, action, quantity,limit_time_sec=60):
        start = time.time()
        contract = self.create_stock_contract(symbol)
        order = self.create_order(action, quantity, 'LMT')
        self.req_update_stock_data(symbol, True)
        ordId_order = self.stocks_data[symbol].reqId_group
        ordId_order = (ordId_order+req_action.Buy) if 'BUY' in action else (ordId_order+req_action.Sell)
        status = 'FAIL'
        while (time.time()-start) < limit_time_sec:
            if (time.time() - start) < limit_time_sec//2:
                order.lmtPrice = round((self.stocks_data[symbol].bid_price + self.stocks_data[symbol].ask_price)/2,2)
            if (time.time()-start) > limit_time_sec//2:
                if 'SELL' in action:
                    order.lmtPrice = round(max(self.stocks_data[symbol].bid_price,self.stocks_data[symbol].last_price*0.999),2)
                elif 'BUY' in action:
                    order.lmtPrice = round(min(self.stocks_data[symbol].ask_price,self.stocks_data[symbol].last_price*1.001),2)
            self.place_order(ordId_order, contract, order)
            time.sleep(1)
            if 'Filled' in self.stocks_data[symbol].status:
                status = 'SUCCESS'
                break
        ordId_mkt_data = self.stocks_data[symbol].reqId_group + req_action.RtData
        self.cancel_mkt_data(ordId_mkt_data)
        self.remove_ordId_stock(ordId_mkt_data)
        self.stocks_data[self.ordId_stock[ordId_order]].status = 'None'
        if 'SUCCESS' in status or 'BUY' in action:
            self.cancel_order(ordId_order)
            self.remove_ordId_stock(ordId_order)
        return status



def get_bar_data(symbol, timeframe):
    print(f"getting bar data for {symbol} {timeframe}")

    contract = Contract()
    contract.symbol = symbol
    contract.secType = 'STK'
    contract.exchange = 'SMART'
    contract.currency = 'USD'
    what_to_show = 'TRADES'

    # now = datetime.datetime.now().strftime('%Y%m%d %H:%M:%S')
    # chart.spinner(True)

    client.reqHistoricalData(3, contract, '20240628-23:59:59', '1 D', timeframe, what_to_show, True, 2, False, [])
    time.sleep(1)
    # chart.watermark(symbol)

# called when we want to update what is rendered on the chart


if __name__ == '__main__':
    client = IBClient(DEFAULT_HOST, TRADING_PORT, DEFAULT_CLIENT_ID)
    time.sleep(1)
    # status = client.get_straming_acount(1)
    # # status = client.get_snap_account()
    # print(status)
    # print(client.account.Data)
    symbol = 'NVDA'
    counter = 0
    symbols =  ['NVDA','MSFT','AAPL']#
    # symbols =  ['N','M','A']#
    threads = []
    # client.add_stock_to_stock_list(symbol)
    # print(client.stocks_data[symbol].Data)
    for idx, stock in enumerate(symbols):
        threads.append(threading.Thread(target=client.add_stock_to_stock_list, args=(stock,)))
        threads[idx].start()
    for idx, stock in enumerate(symbols):
        threads[idx].join()

    threads = []
    while counter<10:
        for idx,stock in enumerate(symbols):
            threads.append(threading.Thread(target=client.req_update_stock_data, args=(stock)))
            threads[idx].start()
        for idx,stock in enumerate(symbols):
            print(client.stocks_data[stock])
            threads[idx].join()
        threads =[]
        # price = client.req_update_stock_data(client.available_order_id,symbol)
        # print(f"Last price of {symbol}: {price}")
        counter +=1
        # time.sleep(10)

    # Request market data
    # client.reqMktData(1, nvda_contract, "", False, False, [])

    # Wait for a few seconds to allow data to be fetched
    # time.sleep(5)

    # Disconnect from TWS
    client.disconnect()

    # chart = Chart(toolbox=True, width=1000, inner_width=0.6, inner_height=1)
    # chart.legend(True)
    # chart.topbar.textbox('symbol', INITIAL_SYMBOL)
    # client.reqMarketDataType(3)
    # get_bar_data(INITIAL_SYMBOL, '1 min')
    #
    # time.sleep(1)
    # client.disconnect()
    # chart.show(block=True)
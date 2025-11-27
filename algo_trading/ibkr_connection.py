import time
import queue
import threading
# import pandas as pd
from enum import Enum,auto
from ibapi.client import EClient
from ibapi.wrapper import EWrapper

from ibapi.client import Contract
from ibapi.order import Order
from ibapi.order_state import OrderState
from ibapi.commission_report import CommissionReport
from ibapi.execution import Execution

from datetime import datetime

import globals_v2 as glb


# from lightweight_charts import Chart

from threading import Thread

ACCOUNT_ID = ""
DEFAULT_HOST = '127.0.0.1'
DEFAULT_CLIENT_ID = 1
LOG_FILE_PATH = f"/Users/ofirdahan/Desktop/interactive brokers/stock_analyzer/paper_trading_data_result/"
LIVE_TRADING = False
LIVE_TRADING_PORT = 4001
PAPER_TRADING_PORT = 4002
PAPER_TRADING_PORT_TWS = 7496
TRADING_PORT = PAPER_TRADING_PORT_TWS
if LIVE_TRADING:
    TRADING_PORT = LIVE_TRADING_PORT
    ACCOUNT_ID = ""

data_queue = queue.Queue()
tick_set = set()
time_a =0
time_b =0
CANCEL_TIME_WAIT = 2
CANCEL_TRY = 5


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
        self.data_types_needed = {"NetLiquidation", "CashBalance", "AvailableFunds", "BuyingPower", "TotalCashBalance","TotalCashBalance"} # "NetLiquidation","CashBalance","AvailableFunds","BuyingPower","TotalCashBalance","SettledCash","GrossPositionValue"
        self.data_types_received = set()  # "NetLiquidation","CashBalance","AvailableFunds","BuyingPower","TotalCashBalance","SettledCash","GrossPositionValue"
        self.symbol_position_updated = set()
        self.update_account_status = False
        self.subscribe=False
        self.open_orders =set()
    def __repr__(self):
        str_print = [f", {key}:{val}" for key, val in self.Data.items()]
        str_print = "".join(str_print)
        return 'ACCOUNT' + str_print

class RT_stock_data():
    def __init__(self,idx,name):
        self.idx_stock_list = idx
        self.reqId_group = idx*10
        self.name=name
        self.Data = {}
        self.historical_data = {}
        self.last_update ={}
        self.shears = 0
        self.action = 'None'
        self.status = 'None'


    def __repr__(self):
        # return f"bid_price:{self.bid_price} bid_size:{self.bid_size} ask_price:{self.ask_price} ask_size:{self.ask_size} last_price:{self.last_price} volume:{self.volume} high:{self.high} low:{self.low} open:{self.open} close:{self.close}"
        str_print = [ f", {key}:{val}" for key,val in self.Data.items()]
        str_print = "".join(str_print)
        return self.name+f" ,POS:{self.shears}"+str_print
class IBClient(EWrapper, EClient):

    def __init__(self):
        EClient.__init__(self, self)
        self.active = True
        self.key_lock = threading.Lock()
        self.key_lock_client = threading.Lock()
        self.key_lock_wrapper = threading.Lock()
        self.key_lock_log_file = threading.Lock()

        self.stock_counter = 0
        self.key_lock_barriers = threading.Lock()
        self.C_W_barriers = {}
        self.key_lock_reqId_stock_data = threading.Lock()
        self.stocks_data = {}
        self.reqId_stock = {}
        self.key_lock_execId_commission = threading.Lock()
        self.execId_symbol_commission = {}

        self.key_lock_ordId = threading.Lock()
        self.ordId_active = {}
        self.key_lock_cancel_appending = threading.Lock()
        self.cancel_appending = {}
        self.ordId_active_group = {'BUY':[],'SELL':[]}
        self.key_lock_account = threading.Lock()
        self.account = account_data()

        self.key_lock_ordId_new = threading.Condition()
        self.valid_order_id = 100

        self.MarketDataType = 1

        self.connect(DEFAULT_HOST, TRADING_PORT, DEFAULT_CLIENT_ID)
        thread = Thread(target=self.run)
        thread.start()
        global LOG_FILE_PATH
        LOG_FILE_PATH = glb.PATH_RESULTS +f"ibkr_log_{datetime.today().strftime('Y%Y_M%m_D%d__%Hh_%Mm_%Ss')}.txt"
        self.write_to_file('',mode='+w')
        time.sleep(1)

    ######### EWrapper ###########

    def connectionClosed(self):
        self.tryReconnectIfNot()

    def error(self, req_id, code, msg, misc=""):
        txt = f'req_id: {req_id} Error {code}: {msg}'
        if code in [2104, 2106, 2158]:
            pass
        else:
            self.tryReconnectIfNot()
            if 'OrderId' in msg and "needs to be cancelled is not found" in msg:
                txt = f'OrderId: {req_id} Error {code}: {msg}'
                self.remove_active_order_id(req_id)
            elif 'needs to be cancelled is not found' in msg or 'is not an active market data request' in msg or "Can't find EId with tickerId" in msg:
                self.remove_reqId_stock(req_id)
            elif 'API client has been unsubscribed from account data':
                with self.key_lock_account:
                    self.account.subscribe = False
                self.remove_reqId_stock(req_account.RT_STREAM)
        self.write_to_file(txt)

    def tickPrice(self, reqId, tickType, price, attrib):  # L1 : {1, 2, 4, 6, 7, 9, 14}
        if reqId in self.reqId_stock:
            tick_type_name = TICKTYPE(tickType).name
            stock = self.reqId_stock[reqId]
            # print(stock,tick_type_name, price)

            with self.key_lock_reqId_stock_data:
                self.stocks_data[stock].Data.update({tick_type_name: price})
            self.barrier_for_2_thread_base_on_reqId(reqId)

    def openOrder(self, orderId, contract: Contract, order: Order,orderState: OrderState):
        pass
        # if orderId:
        #     print(f"Order ID: {orderId}, Contract: {contract.symbol}, Order: {order.action}, Status: {orderState.status}")
        # else:
        #     print("No open orders found.")
        # with self.key_lock_account:
        #     self.account.open_orders.add(orderId)

    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        txt = f"Order ID={orderId} Status Update: Status={status}, Filled={filled}, Remaining={remaining}, Avg Fill Price={avgFillPrice}, Last Fill Price={lastFillPrice}, Client ID={clientId}, Why Held={whyHeld}"
        self.write_to_file(txt)
        if orderId in self.ordId_active:
            with self.key_lock_ordId:
                if orderId in self.ordId_active:
                    symbol = self.ordId_active[orderId][0]
                    action = self.ordId_active[orderId][1]
                else:
                    return
            with self.key_lock_reqId_stock_data:
                self.stocks_data[symbol].status = status
            if status in ["Cancelled","Filled","Error"]:
                self.remove_active_order_id(orderId)
                if 'BUY' in action:
                    glb.my_portfolio[symbol].diff_from_wanted_buy_sell.append(glb.my_portfolio[symbol].last_price-avgFillPrice)
                    self.write_to_file(f"ordId {orderId} removed, stock {symbol} action {action} filled {filled} in avg price {avgFillPrice} and wanted price was {glb.my_portfolio[symbol].last_price} diff {glb.my_portfolio[symbol].last_price-avgFillPrice}",symbol)

                else:
                    glb.my_portfolio[symbol].diff_from_wanted_buy_sell.append(avgFillPrice-glb.my_portfolio[symbol].last_price)
                    self.write_to_file(f"ordId {orderId} removed, stock {symbol} action {action} filled {filled} in avg price {avgFillPrice} and wanted price was {glb.my_portfolio[symbol].last_price} diff {avgFillPrice-glb.my_portfolio[symbol].last_price}",symbol)

    def execDetails(self, reqId:int, contract:Contract, execution:Execution):
        """This event is fired when the reqExecutions() functions is
                invoked, or when an order is filled.  """
        if contract.symbol in glb.my_portfolio:
            with glb.my_portfolio[contract.symbol].key_lock_available_money:
                shears = float(execution.shares)
                if "BOT" in execution.side:
                    glb.my_portfolio[contract.symbol].shears += shears
                    glb.my_portfolio[contract.symbol].available_money -= execution.price*shears
                    if contract.symbol in glb.demo_portfolio_treads:
                        glb.demo_portfolio_treads[contract.symbol].limit_points_buy_sell["BUY"].append([glb.demo_portfolio_treads[contract.symbol].counter,execution.price])
                    if glb.my_portfolio[contract.symbol].shears > 0:
                        glb.my_portfolio[contract.symbol].flag_enter_status = True

                elif "SLD" in execution.side:
                    glb.my_portfolio[contract.symbol].shears -= shears
                    glb.my_portfolio[contract.symbol].available_money += execution.price*shears
                    if contract.symbol in glb.demo_portfolio_treads:
                        glb.demo_portfolio_treads[contract.symbol].limit_points_buy_sell["SELL"].append((glb.demo_portfolio_treads[contract.symbol].counter,execution.price))
                    if glb.my_portfolio[contract.symbol].shears <= 0:
                        glb.my_portfolio[contract.symbol].flag_enter_status = False
            flag = False
            with self.key_lock_execId_commission:
                txt = f"ordId: {execution.orderId}, {contract.symbol} execDetails: {execution.side} of {execution.shares} in price of {execution.price} "
                if execution.execId in self.execId_symbol_commission:
                    commission = self.execId_symbol_commission[execution.execId]
                    flag = True
                else:
                    self.execId_symbol_commission.update({execution.execId:{"ordId": execution.orderId,"symbol":contract.symbol,"side":execution.side,"shares":execution.shares,"price":execution.price}})
                if flag:
                    self.execId_symbol_commission.pop(execution.execId)
            if flag:
                with glb.my_portfolio[contract.symbol].key_lock_available_money:
                    glb.my_portfolio[contract.symbol].available_money -= commission
                    glb.my_portfolio[symbol].total_stock_net_value = glb.my_portfolio[symbol].available_money + glb.my_portfolio[symbol].shears * execution.price

                self.write_to_file(txt + f"with commission of {commission} .[USD]",symbol)

                time = datetime.today().strftime('%H:%M:%S')
                glb.my_portfolio[symbol].store_to_logs_info(execution.side, time, execution.price, execution.shares, commission)

    def commissionReport(self, commissionReport: CommissionReport):
        # This method is called when a commission report is received
        if 'USD' in commissionReport.currency:
            flag = False
            with self.key_lock_execId_commission:
                if commissionReport.execId in self.execId_symbol_commission:
                    exec_Data = self.execId_symbol_commission[commissionReport.execId]
                    txt = f"ordId: {exec_Data["ordId"]}, {exec_Data["symbol"]} execDetails: {exec_Data["side"]} of {exec_Data["shares"]} in price of {exec_Data["price"]} "
                    flag = True
                else:
                    self.execId_symbol_commission.update({commissionReport.execId: commissionReport.commission})
                if flag:
                    self.execId_symbol_commission.pop(commissionReport.execId)
            if flag:
                with glb.my_portfolio[exec_Data["symbol"]].key_lock_available_money:
                    glb.my_portfolio[exec_Data["symbol"]].available_money -= commissionReport.commission
                self.write_to_file(txt + f"with commission of {commissionReport.commission} .[USD]",exec_Data["symbol"])
                glb.my_portfolio[exec_Data["symbol"]].total_stock_net_value = glb.my_portfolio[exec_Data["symbol"]].available_money + glb.my_portfolio[exec_Data["symbol"]].shears * exec_Data["price"]
                time = datetime.today().strftime('%H:%M:%S')
                glb.my_portfolio[exec_Data["symbol"]].store_to_logs_info(exec_Data["side"], time, exec_Data["price"], exec_Data["shares"], commissionReport.commission)

    def contractDetails(self, reqId, contractDetails):
        print(f"ContractDetails: {contractDetails}")

    def historicalData(self, req_id, bar):
        symbol = self.reqId_stock[req_id]
        with glb.key_lock_stocks_data:
            glb.stocks_data[symbol]['open'].append(float(bar.open))
            glb.stocks_data[symbol]['close'].append(float(bar.close))
            glb.stocks_data[symbol]['avg'].append((float(bar.high)+float(bar.low))/2)
            glb.stocks_data[symbol]['volume'].append(float(bar.volume))
            glb.stocks_data[symbol]['dates'].append(bar.date)

    def historicalDataEnd(self, reqId, start, end):
        symbol= self.reqId_stock[reqId]
        self.remove_reqId_stock(reqId)
        txt = f"reqId:{reqId}, end historical data of {symbol} data {start} {end} "
        self.write_to_file(txt,symbol)
        self.barrier_for_2_thread_base_on_reqId(reqId)


    def accountSummary(self, reqId, account, tag, value, currency):
        txt = f"reqId:{reqId} account:{account} tag:{tag} value:{value} got account summary"
        self.write_to_file(txt,'ACCOUNT')
        if 'USD' in currency and account in self.account.account_id:
            try:
                with self.key_lock_account:
                    self.account.Data.update({tag:value})
            except:
                raise ValueError(f"insted of float we got {value}")
        self.barrier_for_2_thread_base_on_reqId(reqId)

    def updateAccountValue(self, key, value, currency, accountName):
        if 'USD' in currency and accountName in self.account.account_id and key in self.account.data_types_needed:
            try:
                with self.key_lock_account:
                    self.account.Data.update({key:value})
                    self.account.Data.update({key:value})
                if 'CashBalance' in key:
                    with glb.key_lock_available_money:
                        # glb.my_available_money_dollar = float(value)
                        glb.my_available_money_dollar = glb.my_available_money_dollar
                    self.write_to_file(f"account:{accountName} key:{key} value:{value} currency:{currency} account update",'ACCOUNT')
            except:
                pass

    def updatePortfolio(self, contract: Contract, position: float, marketPrice: float, marketValue: float,averageCost: float, unrealizedPNL: float, realizedPNL: float, accountName: str):
        if 'USD' in contract.currency and accountName in self.account.account_id:
            if contract.symbol in glb.demo_portfolio_treads:
                glb.demo_portfolio_treads[contract.symbol].current_price = round(float(marketPrice),3)
            position =float(position)
            if contract.symbol in glb.my_portfolio:
                with glb.my_portfolio[contract.symbol].key_lock_available_money:
                    glb.my_portfolio[contract.symbol].shears = position
                    glb.my_portfolio[contract.symbol].total_stock_net_value = position*round(float(marketPrice),3)+ glb.my_portfolio[contract.symbol].available_money

            if position > 0:
                if contract.symbol not in glb.my_portfolio:
                    glb.update_my_portfolio_files(contract.symbol, 0, 0)
                    glb.my_portfolio[contract.symbol].shears = position
            with self.key_lock_account:
                self.account.symbol_position_updated.add(contract.symbol)
            txt =f"UpdatePortfolio. Symbol:{contract.symbol} SecType:{contract.secType} Exchange:{contract.exchange} Position:{position} MarketPrice:{marketPrice} MarketValue:{marketValue} AverageCost:{averageCost} UnrealizedPNL:{unrealizedPNL} RealizedPNL:{realizedPNL} AccountName:{accountName}"
            self.write_to_file(txt,contract.symbol)

        # print("UpdatePortfolio.", "Symbol:", contract.symbol, "SecType:", contract.secType, "Exchange:", contract.exchange,
        #       "Position:", position, "MarketPrice:", marketPrice, "MarketValue:", marketValue, "AverageCost:", averageCost,
        #       "UnrealizedPNL:", unrealizedPNL, "RealizedPNL:", realizedPNL, "AccountName:", accountName)


    def position(self, account, contract, position, avgCost):
        print(f"Account: {account}, Symbol: {contract.symbol}, Position: {position}, Avg Cost: {avgCost}")

    def pnl(self, reqId, dailyPnL, unrealizedPnL, realizedPnL):
        print(f"PnL - Daily: {dailyPnL}, Unrealized: {unrealizedPnL}, Realized: {realizedPnL}")

    ################################################# My FUN ################################################
    #### EXCEPTION #####
    def tryReconnectIfNot(self):
        if not self.isConnected() and self.active:
            with self.key_lock:
                if not self.isConnected() and self.active:
                    for attempt in range(5):
                        try:
                            self.write_to_file(f"Attempt {attempt} to reconnect...")
                            self.connect(DEFAULT_HOST, TRADING_PORT, DEFAULT_CLIENT_ID)
                            thread = Thread(target=self.run)
                            thread.start()
                            time.sleep(1)
                            if self.isConnected():
                                self.write_to_file("Reconnection successful.")
                                break
                        except Exception as e:
                            self.write_to_file(f"Reconnection attempt {attempt} failed: {e}")
                            time.sleep(3)
                    else:
                        self.write_to_file("Max reconnection attempts reached. Exiting.")
    ###REWRITE CANCEL CLIENT REQUESTS ####
    def cancel_order(self, ordId):
        with self.key_lock_ordId:
            if ordId in self.ordId_active:
                action = self.ordId_active[ordId][1]
                symbol = self.ordId_active[ordId][0]
            else:
                return
        counter = 0
        while counter < CANCEL_TRY and ordId in self.ordId_active_group[symbol][action]:
            with self.key_lock_client:
                self.cancelOrder(ordId, "")
            self.write_to_file(f"CANCEL:ordId {ordId}, attempt {counter}",symbol)
            counter += 1
            time.sleep(CANCEL_TIME_WAIT)

    def cancel_order_stock_actions(self,symbol,actions):
        counter = 0
        while counter < CANCEL_TRY and symbol in self.ordId_active_group:
            if all(len(self.ordId_active_group[symbol][action]) == 0 for action in actions):
                break
            for action in actions:
                for ordId in self.ordId_active_group[symbol][action]:
                    with self.key_lock_client:
                        self.cancelOrder(ordId,"")
                    self.write_to_file(f"CANCEL: ordId {ordId}, attempt {counter}",symbol)
            counter += 1
            time.sleep(CANCEL_TIME_WAIT)
    def cancel_account_summary(self, reqId:int):
        counter = 0
        while reqId in self.reqId_stock and counter < CANCEL_TRY:
            with self.key_lock_cancel_appending:
                self.cancel_appending.update({reqId:''})
            with self.key_lock_client:
                self.cancelAccountSummary(reqId)
            self.write_to_file(f"CANCEL: reqId{reqId}, attempt {counter} account summary",'ACCOUNT')
            counter += 1
            time.sleep(CANCEL_TIME_WAIT)
    def cancel_positions(self,reqId):
        counter = 0
        while reqId in self.reqId_stock and counter < CANCEL_TRY:
            with self.key_lock_cancel_appending:
                self.cancel_appending.update({reqId:''})
            with self.key_lock_client:
                self.cancelPositions()
            counter += 1
            time.sleep(CANCEL_TIME_WAIT)
    def cancel_PnL(self, reqId: int):
        counter = 0
        while reqId in self.reqId_stock and counter < CANCEL_TRY:
            with self.key_lock_cancel_appending:
                self.cancel_appending.update({reqId:''})
            with self.key_lock_client:
                self.cancelPnL(reqId)
            counter += 1
            time.sleep(CANCEL_TIME_WAIT)
    def cancel_historical_data(self, symbol :str):
        req_hist_data = self.stocks_data[symbol].reqId_group + req_action.HistoryMktData
        counter = 0
        while req_hist_data in self.reqId_stock and counter < CANCEL_TRY:
            with self.key_lock_cancel_appending:
                self.cancel_appending.update({req_hist_data:''})
            with self.key_lock_client:
                self.cancelHistoricalData(req_hist_data)
            self.write_to_file(f"CANCEL: reqId{req_hist_data}, attempt {counter}, HistoricalData,symbol{symbol} ",symbol)
            counter += 1
            time.sleep(CANCEL_TIME_WAIT)
    def cancel_mkt_data(self, symbol: str):
        # req_mkt_data = self.stocks_data[symbol].reqId_group + req_action.RtData
        # counter = 0
        # while req_mkt_data in self.reqId_stock and counter<CANCEL_TRY:
        #     with self.key_lock_cancel_appending:
        #         self.cancel_appending.update({req_mkt_data:''})
        #     with self.key_lock_client:
        #         self.cancelMktData(req_mkt_data)
        #     self.write_to_file(f"CANCEL: reqId{req_mkt_data}, attempt {counter}, MktData,symbol{symbol} ")
        #     counter += 1
        #     time.sleep(CANCEL_TIME_WAIT)
        req_mkt_data = self.stocks_data[symbol].reqId_group + req_action.RtData
        counter = 0
        if req_mkt_data in self.reqId_stock:
            with self.key_lock_cancel_appending:
                self.cancel_appending.update({req_mkt_data: ''})
            with self.key_lock_client:
                self.cancelMktData(req_mkt_data)
                self.cancelMktData(req_mkt_data)
            # self.write_to_file(f"CANCEL: reqId{req_mkt_data}, attempt {counter}, MktData,symbol{symbol} ")
            self.write_to_file(f"TRY CANCEL: reqId{req_mkt_data}, attempt {counter}, cancel MktData, symbol{symbol} ",symbol)
            # counter += 1

    # def cancel_reqId(self, reqId:int):
    #     #### need to change to sending thread ###
    #     if reqId >= 10:
    #         reqId_modulo = reqId%10
    #         if reqId_modulo == req_action.HistoryMktData:
    #             self.cancel_historical_data(reqId)
    #         elif reqId_modulo == req_action.RtData:
    #             self.cancel_mkt_data(reqId)
    #         elif reqId_modulo == req_action.Buy:
    #             self.cancelOrder(reqId,"")
    #         elif reqId_modulo == req_action.Sell:
    #             self.cancelOrder(reqId,"")
    #     else:
    #         if reqId == req_account.SNAPSHOUT:
    #             self.cancel_account_summary(reqId)
    #         elif reqId == req_account.RT_STREAM:
    #             self.req_account_updates(False,ACCOUNT_ID)
    #         elif reqId == req_account.UPDATE_PROTFOLIO:
    #             self.cancel_positions()
    #
    #
    ### REWRITE DATA CLIENT REQUESTS ####
    def disconnection(self):
        with self.key_lock:
            self.active = False
        self.disconnect()
        self.write_to_file(f"disconnect Client")

    def change_data_type(self,num:int):
        if num != self.MarketDataType:
            self.tryReconnectIfNot()
            with self.key_lock_client:
                self.MarketDataType = num
                client.reqMarketDataType(num)
            self.write_to_file(f"change mkt data type to:{num}")
            time.sleep(1)
    def req_historical_data(self,reqId:int , contract:Contract, endDateTime:str,durationStr:str, barSizeSetting:str, whatToShow:str,useRTH:int, formatDate:int, keepUpToDate:bool, chartOptions):
        self.tryReconnectIfNot()
        self.adding_req_barrier(reqId)
        with self.key_lock_client:
            self.reqHistoricalData(reqId, contract, endDateTime,durationStr, barSizeSetting, whatToShow,useRTH, formatDate, keepUpToDate, chartOptions)
        self.write_to_file(f"reqId:{reqId} request historicalData",contract.symbol)
        self.barrier_for_2_thread_base_on_reqId(reqId)
    def place_order(self,contract, order):
        self.tryReconnectIfNot()
        # flag = False
        # with self.key_lock_ordId:
        #     if ordId in self.ordId_active:
        #         flag = True
        # if flag:
        with self.key_lock_client:
            ordId = self.add_active_order_id(contract.symbol, order.action)
            self.placeOrder(ordId, contract, order)
        with self.key_lock_reqId_stock_data:
            bid = self.stocks_data[contract.symbol].Data['BID_PRICE']
            ask = self.stocks_data[contract.symbol].Data['ASK_PRICE']
            last_price = self.stocks_data[contract.symbol].Data['LAST_PRICE']
        txt = f"reqId:{ordId} ,symbol:{contract.symbol} ,action:{order.action} ,amount:{order.totalQuantity} ,last price:{last_price} ,ordLimitPr: {order.lmtPrice}"
        txt = txt+f" ,ASK: {ask}" if 'BUY' in order.action else txt+f" ,BID: {bid}"
        txt += f" ,place {order.action} order"
        self.write_to_file(txt,contract.symbol)
        return ordId
    def req_account_summary(self,reqId,groupName = "ALL",tags ="NetLiquidation,CashBalance,AvailableFunds,BuyingPower,TotalCashBalance,SettledCash,GrossPositionValue"):
        self.tryReconnectIfNot()
        self.adding_req_barrier(reqId)
        with self.key_lock_client:
            self.reqAccountSummary(reqId, groupName, tags)
        self.write_to_file(f"reqId:{reqId} ,request account summary",'ACCOUNT')
        self.barrier_for_2_thread_base_on_reqId(reqId)
    def req_account_updates(self,subscribe:bool ,timeout=60, acctCode:str = ACCOUNT_ID):
        self.tryReconnectIfNot()
        start_time = time.time()
        if subscribe:
            with self.key_lock_account:
                self.update_account_status = False
                self.account.Data ={}
        status = 'FAILED'
        while (time.time()-start_time) < timeout:
            with self.key_lock_client:
                self.reqAccountUpdates(subscribe, acctCode)  #acctCode: Replace with your account ID Ex "U1234567"
            time.sleep(1)
            if subscribe:
                if len(self.account.Data)>0:
                    self.account.subscribe = True
                    status = 'SUCCESS'
                    break
            else:
                if not self.account.subscribe:
                    status = 'SUCCESS'
                    break
        # self.write_to_file(f"request account update ,subscribe:{subscribe} {status}")
        return status
    def req_account_positions(self):
        self.tryReconnectIfNot()
        with self.key_lock_client:
            self.reqPositions()

    def req_account_PnL(self,reqId: int, account: str, modelCode: str):
        self.tryReconnectIfNot()
        with self.key_lock_client:
            self.reqPnL(reqId, account, modelCode)  # Replace with your account ID
    def req_mkt_data(self, reqId, contract:Contract,genericTickList:str, snapshot:bool, regulatorySnapshot: bool,mktDataOptions):
        self.tryReconnectIfNot()
        self.adding_req_barrier(reqId)
        with self.key_lock_client:
            self.reqMktData(reqId, contract, genericTickList, snapshot, regulatorySnapshot, mktDataOptions)
        self.write_to_file(f"reqId: {reqId} symbol {contract.symbol} ,request mkt data ",contract.symbol)
        self.barrier_for_2_thread_base_on_reqId(reqId)

    ### FILL & RETURN CLIENT OBJECT DATA ####
    def nextValidId(self, orderId: int):
        with self.key_lock_ordId_new:
            self.valid_order_id = max(orderId,self.valid_order_id)  # Store the order ID for later use
            self.key_lock_ordId_new.notify()

    def get_next_valid_order_id(self):
        with self.key_lock_ordId_new:
            self.reqIds(-1)
            self.key_lock_ordId_new.wait()
            ordId = self.valid_order_id
        return ordId
    def create_order(self,action, quantity, orderType, price=None):
        order = Order()
        order.action = action
        order.totalQuantity = quantity
        order.orderType = orderType
        if glb.include_pre_post_mkt:
            order.tif = "DAY"  # Valid for the day
            order.outsideRth = True  # Allow execution outside regular trading hours (True/False)
        # order.auxPrice = stop_price  # The stop price


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
        with self.key_lock_reqId_stock_data:
            if stock not in self.stocks_data:
                self.stock_counter += 1
                self.stocks_data.update({stock:RT_stock_data(self.stock_counter,stock)})
                self.write_to_file(f"reqId group:{self.stocks_data[stock].reqId_group} ,adding stock:{stock} to stock list",stock)
    def add_reqId_stock(self,reqId,stock):
        with self.key_lock_reqId_stock_data:
            self.reqId_stock.update({reqId: stock})
        self.write_to_file(f"reqId {reqId}: added to the reqId list",stock)
    def remove_reqId_stock(self,reqId):
        flag = False
        if reqId in self.reqId_stock:
            with self.key_lock_reqId_stock_data:
                    if reqId in self.reqId_stock:
                        stock = self.reqId_stock[reqId]
                        self.reqId_stock.pop(reqId)
                        flag =True
            if reqId in self.cancel_appending:
                with self.key_lock_cancel_appending:
                    self.cancel_appending.pop(reqId)
            if flag:
                txt = f"remove reqId {reqId},canceled stock {stock}"
                if reqId>10:
                    reqId =reqId%10
                    if reqId == req_action.HistoryMktData:
                        txt = f"REMOVE: reqId {reqId},and canceled stock {stock} HistoricalMktData"
                    elif reqId == req_action.RtData:
                        txt = f"REMOVE: reqId {reqId},and canceled stock {stock} streaming DATA(BID,ASK..)"
                else:
                    if reqId == req_account.RT_STREAM:
                        txt = f"REMOVE: reqId {reqId},and canceled account streaming DATA"
                    # elif reqId == req_action.RtData:
                    #     txt = f"remove reqId {reqId},canceled stock {stock} streaming DATA(BID,ASK..)"
                self.write_to_file(txt,stock)
    def adding_req_barrier(self,reqId):
        with self.key_lock_barriers:
            self.C_W_barriers.update({reqId:threading.Barrier(2)})
    def remove_req_barrier(self,reqId):
        with self.key_lock_barriers:
            if reqId in self.C_W_barriers:
                self.C_W_barriers.pop(reqId)

    def add_active_order_id(self,stock,action):
        flag_creating = True
        with self.key_lock_ordId:
            if stock in self.ordId_active_group:
                if len(self.ordId_active_group[stock][action])>0:
                    ordId = self.ordId_active_group[stock][action][-1]
                    flag_creating = False
        if flag_creating:
            ordId = self.get_next_valid_order_id()
            with self.key_lock_ordId:
                self.ordId_active.update({ordId:[stock,action]})
                if stock in self.ordId_active_group:
                    if ordId not in self.ordId_active_group[stock][action]:
                        self.ordId_active_group[stock][action].append(ordId)
                else:
                    self.ordId_active_group.update({stock:{'BUY':[],'SELL':[]}})
                    self.ordId_active_group[stock][action].append(ordId)
                self.ordId_active_group[action].append(ordId)
        return ordId

    def remove_active_order_id(self,ordId):
        if ordId in self.ordId_active:
            with self.key_lock_ordId:
                if ordId in self.ordId_active:
                    stock = self.ordId_active[ordId][0]
                    action = self.ordId_active[ordId][1]
                    self.ordId_active.pop(ordId)
                    self.ordId_active_group[action].remove(ordId)
                    self.ordId_active_group[stock][action].remove(ordId)

    #### BARRIER SYCHRONIZATION ###
    def barrier_for_2_thread_base_on_reqId(self,reqId,thread = 'Wrapper'):
        if reqId in self.C_W_barriers:
            self.C_W_barriers[reqId].wait()
            self.remove_req_barrier(reqId)


    #### MY ALGO ####
    def write_to_file(self,txt,stock = '',mode ='a+'):
        global LOG_FILE_PATH
        time_txt = datetime.today().strftime('%H:%M:%S')+' '+txt+'\n'
        path = LOG_FILE_PATH
        if stock != '':
            path.replace('.txt',stock+'.txt')
        with self.key_lock_log_file:
            with open(path, mode) as f:
                f.write(time_txt)
            print(time_txt)

    def collect_historical_data(self,symbol, endDateTime="",  # Use the current time
                          durationStr="1 D",  # Duration of 1 day
                          barSizeSetting="1 min",  # 1 minute bars
                          whatToShow="TRADES",  # Type of data
                          useRTH=1,  # Use Regular Trading Hours
                          formatDate=1,  # Date format
                          keepUpToDate=False,
                          chartOptions=[]):
        contract = self.create_stock_contract(symbol)
        reqId_historical = self.stocks_data[symbol].reqId_group+req_action.HistoryMktData
        self.add_reqId_stock(reqId_historical,symbol)
        self.req_historical_data(reqId_historical,contract,endDateTime,durationStr,barSizeSetting,whatToShow,useRTH,formatDate,keepUpToDate,chartOptions)


    def get_snap_account(self,time_wait_sec):
        status ='FAIL'
        reqId_account_data = req_account.SNAPSHOUT
        # self.adding_req_barrier(reqId_account_data)
        with self.key_lock_account:
            self.account.Data = {}
            self.account.symbol_position_updated = set()
        self.add_reqId_stock(reqId_account_data, 'ACCOUNT')
        self.req_account_summary(reqId_account_data,"All", "NetLiquidation,CashBalance,AvailableFunds,BuyingPower,TotalCashBalance,SettledCash,GrossPositionValue")
        invested_stock_set = set([stock for stock in glb.my_portfolio if glb.my_portfolio[stock].flag_invest_in_this_stock])
        time_start = time.time()
        while (time.time()-time_start) < time_wait_sec:
            if self.account.data_types_needed.issubset(self.account.Data) and invested_stock_set.issubset(self.account.symbol_position_updated):#"NetLiquidation","CashBalance","AvailableFunds","BuyingPower","TotalCashBalance","SettledCash","GrossPositionValue"
                status = 'SUCCESS'
                break
            time.sleep(1)
        (threading.Thread(target=self.cancel_account_summary, args=(reqId_account_data,))).start()
        return status

    def get_straming_acount(self,time_stream_sec):
        time_start_stream = time.time()
        status = 'FAIL'
        self.add_reqId_stock(req_account.RT_STREAM, 'ACCOUNT')
        with self.key_lock_account:
            self.account.Data = {}
            self.account.symbol_position_updated = set()
        if 'FAILED' in self.req_account_updates(True):
            return False
        invested_stock_set = set([stock for stock in glb.my_portfolio if glb.my_portfolio[stock].flag_invest_in_this_stock])
        while (time.time()-time_start_stream) < time_stream_sec:
            if self.account.data_types_needed.issubset(self.account.Data) and (invested_stock_set.issubset(self.account.symbol_position_updated) or glb.demo_portfolio_treads[next(iter(glb.demo_portfolio_treads))].counter):#"NetLiquidation","CashBalance","AvailableFunds","BuyingPower","TotalCashBalance","SettledCash","GrossPositionValue"
                status = 'SUCCESS'
                self.account.update_account_status = True
                print(f"success streaming ACCOUNT in time:{time.time()-time_start_stream}")
                break
            time.sleep(1)
        (threading.Thread(target=self.req_account_updates, args=(False,))).start()
        with self.key_lock_account:
            txt = f"reqid :UPDATE ACCOUNT ,finished status:{status} " + self.account.__repr__()
        self.write_to_file(txt,'ACCOUNT')

        return status
    def req_update_stock_data(self,symbol,lable='',time_out=10):
        self.change_data_type(1)
        contract = self.create_stock_contract(symbol)
        reqId = self.stocks_data[symbol].reqId_group+req_action.RtData
        flag = False
        with self.key_lock_reqId_stock_data:
            self.stocks_data[symbol].Data = {}
            if reqId in self.reqId_stock:
                flag = True
        if flag:
            if reqId not in self.cancel_appending:
                return 'SUCCESS'
            while True:
                time.sleep(2)
                with self.key_lock_cancel_appending:
                    if reqId not in self.cancel_appending:
                        break
                self.cancel_mkt_data(symbol)

        self.add_reqId_stock(reqId,symbol)
        sub_thread = threading.Thread(target=self.req_mkt_data, args=(reqId, contract, '', False, False, []))
        sub_thread.start()
        sub_thread.join(timeout=time_out)
        if sub_thread.is_alive():
            self.barrier_for_2_thread_base_on_reqId(reqId)
            self.write_to_file(f"req {reqId} stock {symbol} request mkt data Failed",symbol)
            return 'FAIL'
        else:
            self.write_to_file(f"req {reqId} stock {symbol} request mkt data activate",symbol)
            return 'SUCCESS'

    def try_buy_sell(self, symbol, action, quantity,limit_time_sec=45):
        self.write_to_file(f"LOGIC: try {action} {quantity} shears for {symbol}",symbol)
        status = 'FAIL'
        start_time = time.time()
        contract = self.create_stock_contract(symbol)
        order = self.create_order(action, quantity, 'LMT')
        # order = self.create_order(action, quantity, 'MKT')
        if status in self.req_update_stock_data(symbol,time_out=10):
            self.write_to_file(f"FINISH {action} LOGIC : status {status} ,time {time.time() - start_time}[sec]",symbol)
            return status
        sub_thread = threading.Thread(target=self.cancel_order_stock_actions, args=(symbol, ['BUY','SELL'],))
        sub_thread.start()
        sub_thread.join(timeout=2*CANCEL_TIME_WAIT)
        ordId = 0
        counter = 0
        # ordId = self.add_active_order_id(symbol,action)
        while (time.time() - start_time) < limit_time_sec and not glb.request_stream_data_collection:
            if 'LAST_PRICE' in self.stocks_data[symbol].Data and (('BID_PRICE' in self.stocks_data[symbol].Data and "SELL" in action) or ('ASK_PRICE' in self.stocks_data[symbol].Data and "BUY" in action)):
                while (time.time() - start_time) < limit_time_sec and not glb.request_stream_data_collection:
                    with self.key_lock_reqId_stock_data:
                        if (time.time() - start_time) < min((limit_time_sec // 2),2):
                            if 'SELL' in action:
                                order.lmtPrice = round(self.stocks_data[symbol].Data['BID_PRICE'] * 1.004,2)  # if not glb.include_pre_post_mkt else self.stocks_data[symbol].Data['BID_PRICE']
                            elif 'BUY' in action:
                                order.lmtPrice = round(self.stocks_data[symbol].Data['ASK_PRICE'] * 0.9996,2)  # if not glb.include_pre_post_mkt else self.stocks_data[symbol].Data['ASK_PRICE']
                        elif (time.time() - start_time) < min((limit_time_sec // 2),2):
                            if 'SELL' in action:
                                order.lmtPrice = round(self.stocks_data[symbol].Data['BID_PRICE'] * 1.0003, 2)  # if not glb.include_pre_post_mkt else self.stocks_data[symbol].Data['BID_PRICE']
                            elif 'BUY' in action:
                                order.lmtPrice = round(self.stocks_data[symbol].Data['ASK_PRICE'] * 0.9997, 2)  # if not glb.include_pre_post_mkt else self.stocks_data[symbol].Data['ASK_PRICE']

                        else:
                            order.orderType = 'MKT'
                            # if 'SELL' in action:
                            #     order.lmtPrice = self.stocks_data[symbol].Data['BID_PRICE']  # if not glb.include_pre_post_mkt else self.stocks_data[symbol].Data['BID_PRICE']
                            # elif 'BUY' in action:
                            #     order.lmtPrice = self.stocks_data[symbol].Data['ASK_PRICE']  # if not glb.include_pre_post_mkt else self.stocks_data[symbol].Data['ASK_PRICE']

                        # # if counter < 5:
                        #     order.lmtPrice = round((self.stocks_data[symbol].Data['BID_PRICE'] + self.stocks_data[symbol].Data['ASK_PRICE']) / 2, 2)
                        # elif (time.time() - start_time) > (limit_time_sec // 2):
                        # # elif counter >= 5:
                        # if glb.include_pre_post_mkt:

                        # if 'SELL' in action and order.orderType == 'LMT':
                        #     order.lmtPrice = round(self.stocks_data[symbol].Data['BID_PRICE'] * 0.9996, 2)  # if not glb.include_pre_post_mkt else self.stocks_data[symbol].Data['BID_PRICE']
                        # elif 'BUY' in action and order.orderType == 'LMT':
                        #     order.lmtPrice = round(self.stocks_data[symbol].Data['ASK_PRICE'] * 1.0004, 2)  # if not glb.include_pre_post_mkt else self.stocks_data[symbol].Data['ASK_PRICE']
                        # else:
                                            # self.place_order(ordId, contract, order)
                    ordId = self.place_order(contract, order)
                    time.sleep(1)
                    if 'Filled' in self.stocks_data[symbol].status:
                        status = 'SUCCESS'
                        break
                break
            counter += 1
            time.sleep(1)
        self.cancel_mkt_data(symbol)
        if 'SUCCESS' in status:
            self.stocks_data[symbol].status = 'None'
        elif ordId:
            sub_thread = threading.Thread(target=self.cancel_order, args=(ordId,))
            sub_thread.start()
        self.write_to_file(f"FINISH {action} LOGIC : status {status} ,time {time.time()-start_time}[sec]",symbol)
        return status

if __name__ == '__main__':
    client = IBClient()
    # client.reqAllOpenOrders()
    # client.reqAllOpenOrders()
    # time.sleep(6)
    #
    # client.reqGlobalCancel()
    # client.reqGlobalCancel()

    # status = client.get_straming_acount(1)
    # # status = client.get_snap_account()
    # print(status)
    # print(client.account.Data)
    # symbol = 'NVDA'
    counter = 0
    symbols = ['NVDA','MSFT','AAPL']
    # symbols =  ['N','M','A']#
    for symbol in symbols:
        stock_data = {'open': [], 'close': [], 'avg': [], 'volume': [], 'dates': [], 'last_price': float(0)}
        glb.stocks_data.update({symbol: stock_data})
    threads = []
    for idx, stock in enumerate(symbols):
        threads.append(threading.Thread(target=client.add_stock_to_stock_list, args=(stock,)))
        threads[idx].start()
    for idx, stock in enumerate(symbols):
        threads[idx].join()
    client.collect_historical_data('NVDA')
    stock_path = glb.PATH_RESULTS + '/' + 'NVDA'
    stock_log_price_times_path = stock_path + '/log_price_times' + 'NVDA' + '.csv'
    with open(stock_log_price_times_path, 'w', newline='') as file:
        import csv
        writer = csv.writer(file)
        writer.writerow(glb.stocks_data['NVDA']['dates'])  # Write the list as a single row
        writer.writerow([122.045,122.43,122.515,122.505,122.67,122.84,122.94,122.97,123.05,123.035,123.05000000000001,122.755,122.55,122.65,122.97,123.06,123.14500000000001,123.38,123.4,123.48,123.565,123.46000000000001,123.265,123.265,123.36,123.41,123.655,123.87,123.94999999999999,124.07499999999999,124.15,124.125,124.23,124.27,124.325,124.36,124.44,124.345,124.3,124.285,124.245,124.295,124.39,124.43,124.4,124.37,124.485,124.52000000000001,124.525,124.50999999999999,124.58500000000001,124.67,124.66,124.755,124.84,124.87,124.8,124.75999999999999,124.83000000000001,124.65,124.49,124.41499999999999,124.39500000000001,124.31,124.275,124.425,124.58500000000001,124.645,124.63,124.60499999999999,124.72999999999999,124.66,124.675,124.68,124.685,124.75,124.69999999999999,124.82,124.71000000000001,124.61500000000001,124.50999999999999,124.575,124.46,124.39,124.39500000000001,124.47,124.6,124.645,124.535,124.565,124.49000000000001,124.44999999999999,124.465,124.545,124.405,124.44999999999999,124.485,124.56,124.69,124.80000000000001,124.8,124.775,124.73,124.715,124.605,124.455,124.34,124.37,124.39500000000001,124.47999999999999,124.53999999999999,124.525,124.52000000000001,124.45,124.35499999999999,124.27,124.41499999999999,124.395,124.22,124.075,123.99,124.05000000000001,123.945,123.81,123.86,123.965,124.08,124.12,124.13499999999999,124.185,124.21000000000001,124.14,124.015,123.91,123.84,123.855,123.78,123.69,123.58500000000001,123.61500000000001,123.675,123.63,123.405,123.305,123.2,123.285,123.285,123.245,123.38,123.465,123.58,123.48500000000001,123.4,123.36500000000001,123.395,123.36500000000001,123.17,123.20500000000001,123.18,123.23,123.31,123.33000000000001,123.25,123.22,123.325,123.38,123.37,123.45,123.45500000000001,123.38,123.465,123.58500000000001,123.5,123.545,123.67,123.725,123.75,123.71000000000001,123.71000000000001,123.75,123.775,123.695,123.605,123.505,123.61500000000001,123.565,123.66,123.74000000000001,123.84,123.83,123.805,123.73,123.74,123.7,123.705,123.69,123.63,123.515,123.44999999999999,123.38499999999999,123.43,123.5,123.5,123.48,123.465,123.355,123.355,123.32,123.265,123.225,122.995,123.01,123.07,123.03999999999999,122.99000000000001,122.945,123.03999999999999,123.095,123.14,123.075,122.945,122.89500000000001,122.88499999999999,122.935,122.91999999999999,122.9,122.91499999999999,123.005,123.12,123.13499999999999,123.16,123.145,123.09,123.06,123.065,123.19,123.28,123.26,123.305,123.305,123.25,123.33,123.27000000000001,123.305,123.225,123.03,123.03999999999999,123.125,123.245,123.25999999999999,123.19,123.105,123.045,123.07,123.015,122.925,122.83500000000001,122.70500000000001,122.775,122.735,122.78999999999999,122.85,122.86,122.92,123.005,123.025,123.055,123.06,123.035,123.16499999999999,123.275,123.24,123.245,123.265,123.32,123.25,123.36,123.38,123.33000000000001,123.28999999999999,123.27000000000001,123.27,123.225,123.13,123.13,123.005,123.13499999999999,123.19,123.25999999999999,123.26,123.255,123.275,123.255,123.22,123.305])  # Write the list as a single row
        writer.writerow(glb.stocks_data['NVDA']['volume'])  # Write the list as a single row


    # for idx, stock in enumerate(symbols):
    #     client.req_update_stock_data(stock)
    # time.sleep(5)
    # for idx, stock in enumerate(symbols):
    #     client.cancel_mkt_data(stock)
    # time.sleep(2)
    #
    # client.get_straming_acount(5)
    #
    # for idx, stock in enumerate(symbols):
    #     print(client.stocks_data[stock])
    #
    # status_buy = client.try_buy_sell('NVDA', 'BUY', 200)
    # status_buy = client.try_buy_sell('AAPL', 'BUY', 2)
    # status_buy = client.try_buy_sell('MSFT', 'BUY', 2)

    # status_sell = 'SUCCESS'
    # status_buy = 'FAIL'
    # print(status_sell)
    # x=1
    # while counter<5:
    #     if 'SUCCESS' in status_sell:
    #         status_buy = client.try_buy_sell('NVDA','BUY',2)
    #     if 'SUCCESS' in status_buy:
    #         status_sell = client.try_buy_sell('NVDA','SELL',2)
    #     counter +=1
    # client.collect_historical_data('NVDA')
    # print(client.stocks_data['NVDA'].historical_data)
    # for idx, stock in enumerate(symbols):
    #     threads.append(threading.Thread(target=client.collect_historical_data, args=(stock,)))
    #     threads[idx].start()
    # threads = []
    # for idx, stock in enumerate(symbols):
    #     threads[idx].join()
    # threads = []
    # while counter<3:
    #     for idx,stock in enumerate(symbols):
    #         threads.append(threading.Thread(target=client.req_update_stock_data, args=(stock,)))
    #         threads[idx].start()
    #     for idx,stock in enumerate(symbols):
    #         threads[idx].join()
    #         time.sleep(10)
    #         print(client.stocks_data[stock])
    #     threads =[]
    #     for idx,stock in enumerate(symbols):
    #         threads.append(threading.Thread(target=client.cancel_mkt_data, args=(stock,)))
    #         threads[idx].start()
    #     for idx,stock in enumerate(symbols):
    #         threads[idx].join()
    #     threads =[]
    #     print(f"counter : {counter}")
    #     # price = client.req_update_stock_data(client.available_order_id,symbol)
    #     # print(f"Last price of {symbol}: {price}")
    #     counter +=1
    #     # time.sleep(10)

    # Request market data
    # client.reqMktData(1, nvda_contract, "", False, False, [])

    # Wait for a few seconds to allow data to be fetched
    # time.sleep(5)

    # Disconnect from TWS

    client.disconnection()

    # chart = Chart(toolbox=True, width=1000, inner_width=0.6, inner_height=1)
    # chart.legend(True)
    # chart.topbar.textbox('symbol', INITIAL_SYMBOL)
    # client.reqMarketDataType(3)
    # get_bar_data(INITIAL_SYMBOL, '1 min')
    #
    # time.sleep(1)
    # client.disconnect()
    # chart.show(block=True)
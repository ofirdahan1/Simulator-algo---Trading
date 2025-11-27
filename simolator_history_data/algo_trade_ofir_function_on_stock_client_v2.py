"""
Core Trading Logic and Simulation Engine for Backtesting.

This module is the heart of the backtesting simulator, containing the primary
trading algorithm, the simulation engine, and the data structures for managing
stock information.

Key components:
- `Stock_Object`, `Demo_Stock_Object`, `Real_Stock_Object`: Classes that define
  the data structures for stocks in the simulation.
- `simulate_trading_local_data`: The main simulation loop for a single stock.
- `Safe_Limit_condition_stock_trade_5`: The core trading strategy, implementing a
  trailing stop-loss/take-profit mechanism.
"""
import matplotlib.pyplot as plt
import numpy as np
import datetime
import time
# import yfinance as yf
import os

from scipy import stats
# import logging
import threading
import globals_v2 as glb
from globals_v2 import Real_Stock_actions as SA

key_lock = threading.Lock()


def extract_lists_from_local(stock, start,end,):
    txt =''
    year_month = start[:-3]
    file_name = f"{stock}_{year_month.replace('-', '_')}.txt"
    with open(glb.PATH_STOCKS_DATA + f"{stock}/" + file_name, 'r') as f_input:
        txt = f_input.read()
    rows = txt.split('\n')
    close_list = []
    open_list = []
    avg_list = []
    volume_list = []
    for row in rows:
        if start in row:
            row_data = row.split(',')
            open_list.append(float(row_data[1]))
            close_list.append(float(row_data[4]))
            volume_list.append(float(row_data[5]))
            avg_list.append(np.round((open_list[-1] + close_list[-1]) / 2, 3))
    return avg_list, open_list, close_list, volume_list


def get_slope_linear_regression(y_array):
    x_array = np.arange(len(y_array))
    slope, intercept, r, p, std_err = stats.linregress(x_array, y_array)
    return slope


def predict_next_val_linear_regression(y_array):
    x_array = np.arange(len(y_array))
    slope, intercept, r, p, std_err = stats.linregress(x_array, y_array)
    return intercept + slope * len(y_array)


def predict_poly_regression(y_array, s):
    x_array = np.arange(len(y_array))
    mymodel = np.poly1d(np.polyfit(x_array, y_array, 4))
    return (mymodel(x_array))[-s]


def predict_poly_regression_list(y_array):
    x_array = np.arange(len(y_array))
    mymodel = np.poly1d(np.polyfit(x_array, y_array, 4))
    return (mymodel(x_array))


def update_my_portfolio_files(stock, new_cash_invest_stock, ratio):

    if stock not in glb.stock_that_been_used:
        glb.stock_that_been_used.update({stock:[]})
    if stock in glb.my_portfolio:
        glb.my_portfolio[stock].available_money += new_cash_invest_stock
        glb.my_portfolio[stock].total_stock_net_value += new_cash_invest_stock
        if glb.my_portfolio[stock].init_money == 0:
            glb.my_portfolio[stock].init_money = new_cash_invest_stock
    else:
        glb.my_portfolio.update({stock: Real_Stock_Object(stock,None,new_cash_invest_stock)})
    if new_cash_invest_stock>0:
        glb.my_portfolio[stock].investing_real_money_in_the_stock=True



def divide_available_money(time_stamp):
    def clean_non_potential_stocks_from_portfolio(new_potential_stocks_list):
        pop_stock_list=list()
        for stock in glb.my_portfolio:
            if stock not in new_potential_stocks_list:
                glb.my_portfolio[stock].real_sell_shears(glb.demo_portfolio_treads[stock].real_avg_list[-1][time_stamp],time_stamp,glb.demo_portfolio_treads[stock].real_volume_list[-1][time_stamp])
                pop_stock_list.append(stock)
        for stock in glb.my_portfolio:
                glb.my_portfolio[stock].return_available_real_cash()
        for stock in pop_stock_list:
            glb.my_portfolio.pop(stock)

    def decide_which_stocks_are_possible_to_be_most_profit(time_stamp):
        # if glb.not_first_day :
        if time_stamp>0:
            profit_stocks = [[glb.demo_portfolio_treads[stock].accumulated_amount_percentage_day*glb.demo_portfolio_treads[stock].avg_volume, stock] for stock in glb.demo_portfolio_treads if (200<glb.demo_portfolio_treads[stock].avg_volume )]#glb.demo_portfolio_treads[stock].accumulated_amount_percentage_day>-100 and
            profit_stocks.sort(key=lambda x: x[0], reverse=True)
            if len(profit_stocks) == 0:
                return [],[1],0
            if profit_stocks[-1][0] <=0:
                abs_min = abs(profit_stocks[-1][0])
                for idx,ratio_stock in enumerate(profit_stocks):
                    profit_stocks[idx][0] += abs_min+0.00001
            # profit_stocks= profit_stocks[:3]
            sum_slop = [float(x[0]) for x in profit_stocks]
            idx_lim = len(sum_slop)
        else:
            profit_stocks = [[1, stock] for stock in glb.demo_portfolio_treads if 1<glb.demo_portfolio_treads[stock].avg_volume]
            sum_slop = np.ones(len(profit_stocks))
            idx_lim = len(sum_slop)

        return profit_stocks,sum_slop,idx_lim
    if glb.dbg_on_real_data:
        print('conter', (glb.demo_portfolio_treads[glb.job_by_one_thread].counter))
    # else:
        # print('day num', len(glb.demo_portfolio_treads[glb.job_by_one_thread].minutes_per_day) - 1,'counter:',glb.demo_portfolio_treads[glb.job_by_one_thread].counter)
    profit_stocks,sum_slop,idx_lim = decide_which_stocks_are_possible_to_be_most_profit(time_stamp)
    if len(profit_stocks) == 0:
        clean_non_potential_stocks_from_portfolio(["None"])
        return
    clean_non_potential_stocks_from_portfolio(np.array(profit_stocks)[:, 1])
    partial_money = (glb.my_available_money_dollar-500) / sum(sum_slop) #real: need to get available buying power
    sum_of_sum_slop = sum(sum_slop)
    net_money = glb.my_available_money_dollar-500
    for stock in glb.my_portfolio:
        glb.my_portfolio[stock].total_stock_net_value = glb.my_portfolio[stock].available_money +glb.demo_portfolio_treads[stock].real_avg_list[-1][time_stamp]*glb.my_portfolio[stock].shears
        net_money += glb.my_portfolio[stock].total_stock_net_value
    print(f"net money: {net_money} available_money: {glb.my_available_money_dollar-500}")
    stock_that_got_divide = []
    if partial_money>0:
        for idx, ratio_stock in enumerate(profit_stocks):
            if idx < idx_lim:
                glb.demo_portfolio_treads[ratio_stock[1]].is_this_potential_stock = True
                update_my_portfolio_files(ratio_stock[1], 0, 0)
                price = glb.demo_portfolio_treads[ratio_stock[1]].real_avg_list[-1][time_stamp]
                # new_cash_invest_stock = max(0,min(round(partial_money * ratio_stock[0], 2),glb.demo_portfolio_treads[ratio_stock[1]].avg_volume+price*5-glb.my_portfolio[ratio_stock[1]].total_stock_net_value))
                new_cash_invest_stock = max(0,min(glb.my_available_money_dollar-500,round(partial_money * ratio_stock[0], 2),glb.demo_portfolio_treads[ratio_stock[1]].avg_volume*price-glb.my_portfolio[ratio_stock[1]].total_stock_net_value))
                predict_trade_commission = round(max(1.0, 0.007 * new_cash_invest_stock / price), 3)
                stock_net = glb.my_portfolio[ratio_stock[1]].total_stock_net_value + new_cash_invest_stock
                # if stock_net * 0.0004 < predict_trade_commission * 2:
                #     continue
                glb.my_available_money_dollar -= new_cash_invest_stock
                update_my_portfolio_files(ratio_stock[1], new_cash_invest_stock, profit_stocks[idx][0] / sum_of_sum_slop)
                optional_cash = glb.my_portfolio[ratio_stock[1]].shears * price + glb.my_portfolio[ratio_stock[1]].available_money
                # optional_cash = glb.my_portfolio[ratio_stock[1]].total_stock_net_value
                print(ratio_stock[1], optional_cash,ratio_stock[0]/sum_of_sum_slop)
                stock_that_got_divide.append(ratio_stock[1])


                # if glb.demo_portfolio_treads[ratio_stock[1]].flag_enter_status and glb.demo_portfolio_treads[ratio_stock[1]].amount_limit_flag and not glb.my_portfolio[ratio_stock[1]].flag_enter_status:
                # # if glb.demo_portfolio_treads[ratio_stock[1]].flag_enter_status and glb.demo_portfolio_treads[ratio_stock[1]].amount_limit_flag:
                #     glb.my_portfolio[ratio_stock[1]].real_buy_shears(price,time_stamp,glb.demo_portfolio_treads[ratio_stock[1]].real_volume_list[-1][time_stamp])
        spear_money = glb.my_available_money_dollar - 500
        if spear_money > 1 and len(stock_that_got_divide)>0:
            partioal_money = spear_money / len(stock_that_got_divide)
            print(f"DIVIDE: left {spear_money} cash ,and divide it between {len(stock_that_got_divide)} stocks :{partioal_money} ")
            for stock in stock_that_got_divide:
                update_my_portfolio_files(stock, partioal_money, 0)
            glb.my_available_money_dollar -= spear_money


class Stock_Object():
    """
    A base class representing a stock in the simulation.
    """
    def __init__(self, stock_name, barrier, init_money):
        """
        Initializes a Stock_Object.

        Args:
            stock_name (str): The stock symbol.
            barrier (threading.Barrier): A barrier for thread synchronization.
            init_money (float): The initial capital for this stock object.
        """
        self.stock_name = stock_name
        self.thread_id = None
        self.thread_response = None
        self.barrier = barrier
        self.buy_phase = False
        self.sell_phase = False
        self.flag_enter_status = False
        self.shears = 0
        self.accumulated_amount = 0
        self.accumulated_amount_percentage_day = 0
        self.start_accumulated_amount = -glb.avg_commission_per_shear - 0.001
        self.available_money = init_money
        self.init_money = init_money


class Real_Stock_Object(Stock_Object):
    """
    Represents a stock in the real portfolio, handling actual buy/sell operations.
    """
    def __init__(self, stock_name, barrier, init_money):
        super().__init__(stock_name, barrier, init_money)
        self.real_logs = list()
        self.total_stock_net_value = init_money

    def real_sell_shears(self, price, time_stamp, volume):
        """
        Executes a real sell order for the stock.
        """
        shears_trade_action = int(min(volume * glb.ratio_trade_in_volume_minute, self.shears))
        if shears_trade_action > 0:  # real:sell
            # if self.shears > 0:
            commission = max(1.0, shears_trade_action * glb.avg_commission_per_shear) + glb.real_time_commision * shears_trade_action
            self.available_money = round(self.available_money + shears_trade_action * price - commission, 3)
            self.shears -= shears_trade_action
            self.total_stock_net_value = self.available_money + self.shears * price
            self.store_to_logs_info('SELL', time_stamp, price, shears_trade_action, commission)

        # commission = max(1.0, self.shears * 0.005)
        # self.available_money = round(self.available_money + self.shears * price - commission, 3)
        # self.store_to_logs_info('SELL', time_stamp,price,self.shears, commission)
        # self.shears = 0
        if self.shears == 0:
            self.flag_enter_status = False
        if time_stamp == (glb.min_num_of_time_stamp_in_stocks_current_day - 1) and self.shears != 0:
            RuntimeError("finish day with stocks")

    def real_buy_shears(self, price, time_stamp, volume):
        """
        Executes a real buy order for the stock.
        """
        if self.available_money > 0:  # and glb.demo_portfolio_treads[self.stock_name].avg_volume/price >100
            # if self.available_money > 0:
            buying_power = max(0, min(glb.demo_portfolio_treads[self.stock_name].avg_volume,
                                     glb.ratio_trade_in_volume_minute * volume, self.available_money / price,
                                     glb.demo_portfolio_treads[
                                         self.stock_name].avg_volume - self.shears)) * price
            # buying_power = (200*price + 20) if self.shears == 0 else 0
            predict_trade_commission = round(max(1.0, glb.avg_commission_per_shear * buying_power / price), 3)
            new_shears = max(int((buying_power - predict_trade_commission - 10) / price), 0)  # real:buy
            # predict_trade_commission = round(max(1.0, self.available_money * 0.005 / price), 3)
            # new_shears = max(int((self.available_money - predict_trade_commission - 10) / price), 0)
            if (new_shears * price * 0.0004 > predict_trade_commission * 2) or True:
                # if new_shears>0:
                self.shears += new_shears
                commission = max(1.0,
                                 new_shears * glb.avg_commission_per_shear) + glb.real_time_commision * new_shears
                self.available_money = round(self.available_money - new_shears * price - commission, 3)
                self.total_stock_net_value = self.available_money + self.shears * price
                self.flag_enter_status = True
                self.store_to_logs_info('BUY', time_stamp, price, new_shears, commission)

    def return_available_real_cash(self):
        """
        Returns the available cash from this stock object to the main portfolio.
        """
        if self.available_money > 0:
            with key_lock:
                glb.my_available_money_dollar += self.available_money
        self.available_money = 0

    def store_to_logs_info(self, action, time_stamp, price, shears, commission):
        """
        Stores transaction information to the global logs.
        """
        with key_lock:
            if 'BUY' in action:
                glb.real_logs.append(
                    glb.current_date + ' ' + self.stock_name + ' time stamp:' + str(time_stamp) + ' action:' + action + ' price:' + str(
                        price) + ' shears:' + str(shears) + ' commission:' + str(
                        commission) + ' proff:' + "%.2f" % (glb.my_available_money_dollar))  # "%.2f" %(100*(self.available_money+self.shears*price-self.init_money)/self.init_money
                # glb.real_logs_csv.append([glb.current_date, str(time_stamp), self.stock_name, action, str(price),str(glb.demo_portfolio_treads[self.stock_name].real_volume_list[-1][time_stamp]), str(shears),commission,"%.2f" %(self.total_stock_net_value), "%.2f" %(glb.my_available_money_dollar)])
                glb.real_logs_csv.append([glb.current_date, time_stamp, self.stock_name, action, price,
                                          glb.demo_portfolio_treads[self.stock_name].real_volume_list[-1][
                                              time_stamp], shears, commission, (self.total_stock_net_value),
                                          (glb.my_available_money_dollar)])
            else:
                glb.real_logs.append(
                    glb.current_date + ' ' + self.stock_name + ' time stamp:' + str(time_stamp) + ' action:' + action + ' price:' + str(
                        price) + ' shears:' + str(shears) + ' commission:' + str(
                        commission) + ' proff:' + "%.2f" % (glb.my_available_money_dollar))
                # glb.real_logs_csv.append([glb.current_date,str(time_stamp),self.stock_name,action,str(price),str(glb.demo_portfolio_treads[self.stock_name].real_volume_list[-1][time_stamp]),str(-1*shears),commission,"%.2f" %(self.total_stock_net_value),"%.2f" %(glb.my_available_money_dollar)])
                glb.real_logs_csv.append([glb.current_date, time_stamp, self.stock_name, action, price,
                                          glb.demo_portfolio_treads[self.stock_name].real_volume_list[-1][
                                              time_stamp], -1 * shears, commission,
                                          (self.total_stock_net_value), (glb.my_available_money_dollar)])

    def write_to_log_info(self):
        """
        Writes the logs for this stock to a file.
        """
        import csv
        if not os.path.isdir(glb.PATH_RESULTS):
            os.mkdir(glb.PATH_RESULTS)
        real_log_path = glb.PATH_RESULTS + '/real_log.txt'
        with key_lock:
            with open(real_log_path, 'a') as f:
                for line in self.real_logs:
                    f.write(line + '\n')


class Demo_Stock_Object(Stock_Object):
    """
    Represents a stock in the simulation environment, used for backtesting.
    """
    def __init__(self, stock_name, barrier, init_money):
        super().__init__(stock_name, barrier, init_money)
        self.minutes_per_day = list()
        self.date = ''
        self.flag_enter_status_rec = False
        self.exit_flag = False
        self.flag_first_day = True
        self.flag_last_day = False
        self.is_this_potential_stock = False
        self.investing_real_money_in_the_stock = False
        self.flag_amount_list_rec = True
        self.accumulated_amount_no_gap = 0
        self.accumulated_amount_limit = 0
        self.avg_volume = 0
        self.max_amount = 0
        self.min_per_day = 0
        self.counter = 0
        self.gaps_list = list()
        self.amount_list = list()
        self.amount_list_no_gap = list()
        self.amount_limit = list()
        self.amount_limit_flag = False
        self.amount_limit_num = 0
        self.relative_start_price = 0
        self.avg_list_no_gap = list()
        self.real_avg_list = list()
        self.real_open_list = list()
        self.real_close_list = list()
        self.real_high_list = list()
        self.real_low_list = list()
        self.real_volume_list = list()
        self.short_slope_stock = list()
        self.short_short_slope = list()
        self.mix_slope = list()
        self.slop_mix_slope = list()
        self.short_slope = list()
        self.long_slope = list()
        self.demo_logs = list()
        self.demo_limit_logs = list()
        self.demo_limit_logs_csv = list()
    def data_for_action_trade(self, time_stamp, action, market_time_condition, shears_request):
        if 'open' in market_time_condition:
            price = self.real_open_list[-1][time_stamp]
        elif 'close' in market_time_condition:
            price = self.real_close_list[-1][time_stamp]
        else:
            price = self.real_avg_list[-1][time_stamp]
        if 'buy' in action:
            predict_trade_commission = round(max(1.0, self.available_money * glb.avg_commission_per_shear / price), 3)
            max_shears_can_buy = int((self.available_money - predict_trade_commission - 10) / price)
            shears = min(max_shears_can_buy, shears_request)
        else:
            shears = min(self.shears, shears_request)
        return shears, price

    def sell_shears(self, time_stamp, shears_num_sell, market_time_condition):
        shears_num_sell, price = self.data_for_action_trade(time_stamp, 'sell', market_time_condition, shears_num_sell)
        self.shears -= shears_num_sell
        # if 0 == self.shears:
        #     self.flag_enter_status = False
        if shears_num_sell>0:
            self.available_money = round(self.available_money + shears_num_sell * price - max(1.0, shears_num_sell * glb.avg_commission_per_shear),3)

            self.store_to_logs_info('SELL', time_stamp,price,shears_num_sell)

        # self.sell_phase = False


    def buy_shears(self, time_stamp, shears_num_buy, market_time_condition):
        shears_num_buy, price = self.data_for_action_trade(time_stamp, 'buy', market_time_condition, shears_num_buy)
        # if 0 == self.shears and shears_num_buy > 0:
        #     self.flag_enter_status = True
        self.shears += shears_num_buy
        if shears_num_buy>0:
            self.store_to_logs_info('BUY', time_stamp,price,shears_num_buy)
            self.available_money = round(self.available_money - shears_num_buy * price - max(1.0, shears_num_buy * glb.avg_commission_per_shear),3)
        # self.buy_phase = False
        # self.check_real_invest_in_the_stock_and_action(SA.Buy, price, time_stamp)
        # if self.amount_limit_flag:

    def check_real_invest_in_the_stock_and_action(self, action, price=0,time_stamp=0):
        if self.stock_name in glb.my_portfolio:
            if action in [SA.Buy, SA.Sell] and (glb.min_num_of_time_stamp_in_stocks_current_day - time_stamp) <= 5:
                action = SA.Sell
            if action is SA.Buy : #and not glb.my_portfolio[self.stock_name].flag_enter_status
                glb.my_portfolio[self.stock_name].real_buy_shears(price,time_stamp,self.real_volume_list[-1][time_stamp])
            elif action is SA.Sell and glb.my_portfolio[self.stock_name].flag_enter_status:
                glb.my_portfolio[self.stock_name].real_sell_shears(price,time_stamp,self.real_volume_list[-1][time_stamp])
            elif action is SA.Return_Available_cash:
                if not self.is_this_potential_stock:
                    glb.my_portfolio[self.stock_name].real_sell_shears(price,time_stamp,self.real_volume_list[-1][time_stamp])
                glb.my_portfolio[self.stock_name].return_available_real_cash()
            elif action is SA.Collect_divide_again:
                self.is_this_potential_stock = False
                glb.my_portfolio[self.stock_name].return_available_real_cash()
            glb.my_portfolio[self.stock_name].total_stock_net_value = glb.my_portfolio[self.stock_name].available_money+glb.my_portfolio[self.stock_name].shears*price
    def break_point_to_divide_the_real_money_between_stocks(self,time_stamp):
        if time_stamp < glb.min_num_of_time_stamp_in_stocks_current_day:
            glb.day_barrier.wait()  ########
            if self.stock_name == glb.job_by_one_thread:
                divide_available_money(time_stamp)
            glb.day_barrier.wait()  #####3#

    def detect_pick_fall(self):
        return False

        # if 7 <= extreme_counter < 16:
        #     slope_d = 0
        #     extreme_counter += 1
        #
        # if self.counter == 185:
        #     print(slope_100)
        #
        # # if slope_d < glb.slop_d_num_neg_flag and stock_interval_change<0 and self.flag_enter_status:
        # #     self.sell_phase = True
        # # elif slope_d < glb.slop_d_num_neg_flag and stock_interval_change>0 and not self.flag_enter_status:
        # #     self.buy_phase = True
        # # elif slope_d > glb.slop_num_pos_flag and not self.flag_enter_status:
        # #     self.buy_phase = True
        # # elif slope_m < 0 and slope_d < 0 and self.flag_enter_status:
        # #     self.sell_phase = True
        # # elif (slope >= glb.slop_num_pos_flag and slope_d > 0 and slope_m>0) and not self.flag_enter_status:
        # #     self.buy_phase = True
        #
        # # if (slope_d_long_slop < 0) and slope_d<0 and abs(slope*1000)>0.05 and  self.flag_enter_status:
        # #     self.sell_phase = True
        # # elif (slope_d_long_slop > 0 or slope>0) and abs(slope*1000)>0.05 and slope_d>0 and not self.flag_enter_status:
        # #     self.buy_phase = True
        # slope_val_max = price / 5e5
        # if abs(slope_7) > slope_val_max and 0 == extreme and self.counter > 3 and slope_100 > 0.00005:
        #     extreme_counter = 0
        #     if slope_7 < 0:
        #         extreme = -1
        #         if self.flag_enter_status:
        #             self.sell_phase = True
        #     else:
        #         extreme = 1
        #         min_time_stamp = combine_time_stamp
        #         if not self.flag_enter_status:
        #             self.buy_phase = True
        # elif 0 != extreme:
        #     slope_7_sub = get_slope_linear_regression(
        #         self.short_slope[(self.counter - 2):self.counter])
        #     slope_s = get_slope_linear_regression(combine_avg[max(0, combine_time_stamp - 3):combine_time_stamp])
        #     # slope_time_stamp = get_slope_linear_regression(combine_avg[(min_time_stamp):combine_time_stamp])
        #     if slope_7 < 0 and slope_s > 0.1 and -1 == extreme:
        #         if slope_7_sub > 0:
        #             if not self.flag_enter_status and slope_7 < -slope_val_max:
        #                 self.buy_phase = True
        #             min_time_stamp = combine_time_stamp
        #             extreme = 1
        #     elif (slope_7_sub < 0 or slope_s < 0) and 1 == extreme:
        #         if self.flag_enter_status:
        #             self.sell_phase = True
        #         extreme = -1
        #     if abs(slope_7) < slope_val_max:
        #         extreme_counter += 1
        #     else:
        #         extreme_counter = 0
        #     if 7 == extreme_counter:
        #         extreme = 0


    def analyze_the_histogram_and_set_the_next_action(self,combine_avg,combine_time_stamp,price):
        extreme = 0
        extreme_counter = 0
        # # slope = get_slope_linear_regression((combine_avg[max(0,combine_time_stamp-idle_last_data_amount):combine_time_stamp])/self.real_avg_list[0][0])
        # slope_100 = get_slope_linear_regression((combine_avg[max(0, combine_time_stamp - 100):combine_time_stamp]) / self.real_avg_list[-1][0])
        # slope_80 = get_slope_linear_regression((combine_avg[max(0, combine_time_stamp - 80):combine_time_stamp]) / combine_avg[max(0, combine_time_stamp - 80)])
        # slope_60 = get_slope_linear_regression((combine_avg[max(0, combine_time_stamp - 60):combine_time_stamp]) / self.real_avg_list[-1][0])
        # slope_40 = get_slope_linear_regression((combine_avg[max(0, combine_time_stamp - 40):combine_time_stamp]) / combine_avg[max(0, combine_time_stamp - 40)])
        # slope_30 = get_slope_linear_regression((combine_avg[max(0, combine_time_stamp - 30):combine_time_stamp]) / combine_avg[max(0, combine_time_stamp - 30)])
        # slope_20 = get_slope_linear_regression((combine_avg[max(0, combine_time_stamp - 20):combine_time_stamp]) / combine_avg[max(0, combine_time_stamp - 20)])
        # slope_15 = get_slope_linear_regression(combine_avg[max(0, combine_time_stamp - 15):combine_time_stamp] / combine_avg[max(0, combine_time_stamp - 15)])
        # slope_10 = get_slope_linear_regression(combine_avg[max(0, combine_time_stamp - 10):combine_time_stamp] / combine_avg[max(0, combine_time_stamp - 10)])
        # # slope_s = get_slope_linear_regression(combine_avg[max(0, combine_time_stamp - 5):combine_time_stamp]/self.real_avg_list[0][0])
        # slope_7 = get_slope_linear_regression(combine_avg[max(0, combine_time_stamp - 7):combine_time_stamp] / combine_avg[max(0, combine_time_stamp - 7)])
        # slope_5 = get_slope_linear_regression(combine_avg[max(0, combine_time_stamp - 5):combine_time_stamp] / combine_avg[max(0, combine_time_stamp - 5)])
        # slope_2 = get_slope_linear_regression(combine_avg[max(0, combine_time_stamp - 2):combine_time_stamp] / self.real_avg_list[-1][0])
        # slope_3_long_slop = get_slope_linear_regression(self.long_slope[(self.counter - 3):self.counter]) if len(self.long_slope) > 3 else 0
        # slope_10_long_slop = get_slope_linear_regression(self.long_slope[(self.counter - 10):self.counter]) if len(self.long_slope) > 10 else 0
        # slope_5_mix_slop = get_slope_linear_regression(self.mix_slope[(self.counter - 5):self.counter]) if len(self.mix_slope) > 5 else 0
        # slop_long =slope_20*1e3
        # slop_short = slope_10*1e3
        # slop_short_short = slope_15*1e3
        # # sum_slot = (slope_40+slope_20+slope_10)*1e3/3 if self.stock_name != 'VOO' else (slope_40+slope_20+slope_10)*1e4/3
        # sum_slot = (slope_5+slope_2)*1e3/3
        # sum_slot = sum_slot if self.stock_name != 'VOO' else sum_slot*10
        if not self.detect_pick_fall():
            # x=1
            if not self.flag_enter_status:
                self.buy_phase = True
            # if sum_slot>0.5 and not self.flag_enter_status:
            #     self.buy_phase = True
            #     self.sell_phase = False
            # elif sum_slot<0.5 and self.flag_enter_status:
            #     self.sell_phase = True
            #     self.buy_phase = False

            # if slope_d_long_slop < -0.0000001 and slope_30 < 0 and slope_15 < 0 and (slope_15 < -0.0004 or slope_60 < -0.00001 or slope_100 < -0.00005 or slope_30 < -0.0002) and self.flag_enter_status:
            #     self.sell_phase = True
            # elif slope_d_long_slop > 0.0000001 and slope_30 > 0 and slope_15 > 0 and (slope_15 > 0.0004 or slope_60 > 0.0001 or slope_100 > 0.00005 or slope_30 > 0.0002) and not self.flag_enter_status:
            #     self.buy_phase = True

        # long_slope = 0
        # short_slope = 0
        # if self.counter > 196:
        #     long_slope = get_slope_linear_regression(self.amount_list_no_gap[max(0, self.counter - 195):self.counter])
        # if self.counter > 6:
        #     short_slope = get_slope_linear_regression(self.amount_list_no_gap[max(0, self.counter - 5):self.counter])
        slop_long = 0
        slop_short = 0
        sum_slot = 0
        slope_5_mix_slop = 0
        self.long_slope.append(slop_long/1e3)
        self.short_slope.append(slop_short/1e3)
        self.mix_slope.append(sum_slot/1e3)
        self.slop_mix_slope.append(slope_5_mix_slop*1e5)

    def simulate_the_next_trade(self,price,stock_interval_change,time_stamp):
        if self.buy_phase:
            self.buy_shears(time_stamp, int(self.available_money / self.real_avg_list[-1][time_stamp]), 'avg')  # closeX2
            # if self.amount_limit_flag:
            # diff = round(-1*max(1.0,self.shears*0.005),3)
            diff = -glb.avg_commission_per_shear
            self.accumulated_amount += diff
            self.accumulated_amount_no_gap += diff
            # if self.amount_limit_flag:
            #     # self.buy_shears(time_stamp, int(self.available_money / self.real_avg_list[-1][time_stamp]), 'avg')  # closeX2
            #     self.accumulated_amount_limit += diff
            #     self.store_to_logs_info_limit('BUY', time_stamp, price, 1)
            #     # self.check_real_invest_in_the_stock_and_action(SA.Buy, price, time_stamp)
            self.flag_enter_status = True
            self.buy_phase = False


        elif self.sell_phase:
            # diff = round(stock_interval_change- max(1.0,self.shears*glb.avg_commission_per_shear),4)
            diff = stock_interval_change - glb.avg_commission_per_shear
            self.accumulated_amount += diff
            self.accumulated_amount_no_gap += diff
            # if self.amount_limit_flag:
            #     self.accumulated_amount_limit += diff
            #     self.store_to_logs_info_limit('SELL', time_stamp, price, 1)
            #     # self.check_real_invest_in_the_stock_and_action(SA.Sell, price, time_stamp)
            #     # self.sell_shears(time_stamp, self.shears, 'avg')  # close
            self.flag_enter_status = False
            self.sell_phase = False
            self.sell_shears(time_stamp, self.shears, 'avg')  # close

        elif self.flag_enter_status:
            diff = round(stock_interval_change, 4)
            self.accumulated_amount += diff
            self.accumulated_amount_no_gap += diff
            # if self.amount_limit_flag:
            #     self.accumulated_amount_limit += diff
    def after_hours(self,new_price,last_price):
        relative_amount = new_price - self.relative_start_price
        proff_from_start = (100 * relative_amount / self.relative_start_price)  # in presantage
        if ((new_price - self.relative_start_price) / 100) < self.amount_limit_num and self.amount_limit_flag:
            if self.flag_enter_status and self.amount_limit_flag:
                # self.accumulated_amount_limit += round(self.relative_start_price * (1 + self.amount_limit_num / 100) - price,2)
                # price = self.relative_start_price * (1 + self.amount_limit_num / 100)
                self.accumulated_amount_limit -= glb.avg_commission_per_shear
                diff = self.relative_start_price - last_price
                self.accumulated_amount_limit += diff

                self.store_to_logs_info_limit('SELL', -1, self.relative_start_price, 1)
            # price = self.relative_start_price * (1 + self.amount_limit_num / 100)
            self.check_real_invest_in_the_stock_and_action(SA.Sell, self.relative_start_price, -1)
            self.amount_limit_flag = False
        elif proff_from_start >= self.amount_limit_num and not self.amount_limit_flag:
            # price = round(self.relative_start_price * (1 + self.amount_limit_num / 100),2)
            if self.flag_enter_status and not self.amount_limit_flag:
                self.accumulated_amount_limit -= glb.avg_commission_per_shear
                self.store_to_logs_info_limit('BUY', -1, self.relative_start_price, 1)
                diff = new_price - self.relative_start_price
                self.accumulated_amount_limit += diff
            self.check_real_invest_in_the_stock_and_action(SA.Buy, self.relative_start_price, -1)
            self.amount_limit_flag = True
            if proff_from_start > (self.amount_limit_num + glb.limit_presantage):
                self.relative_start_price *= (1 + glb.limit_presantage / 100)
        elif proff_from_start >= self.amount_limit_num and self.amount_limit_flag:
            self.accumulated_amount_limit += new_price-last_price

    def Safe_Limit_condition_stock_trade_5(self,price,time_stamp,diff):
        close_price = self.real_close_list[-1][time_stamp]
        relative_amount = close_price - self.relative_start_price
        diff = diff if self.amount_limit_flag else 0
        diff_p = glb.diff_p

        pnl_limit_d = (self.amount_limit_num-diff_p)
        pnl_limit_u = (self.amount_limit_num+diff_p)
        pnl = relative_amount*100/self.relative_start_price
        if pnl> self.amount_limit_num:
            if self.flag_enter_status and not self.amount_limit_flag and pnl > pnl_limit_u:
                # price = self.relative_start_price * (1 + pnl_limit_u / 100)
                self.accumulated_amount_limit -= glb.avg_commission_per_shear
                self.store_to_logs_info_limit('BUY', time_stamp, price, 1)
                self.check_real_invest_in_the_stock_and_action(SA.Buy, price, time_stamp)
                self.amount_limit_flag = True

            if pnl >= (self.amount_limit_num + glb.limit_presantage):
                self.amount_limit_num += glb.limit_presantage
        else:
            if self.flag_enter_status and self.amount_limit_flag and pnl < pnl_limit_d:
                # price = self.relative_start_price * (1 + pnl_limit_d / 100)
                self.accumulated_amount_limit -= glb.avg_commission_per_shear
                self.store_to_logs_info_limit('SELL', time_stamp, price, 1)
                self.check_real_invest_in_the_stock_and_action(SA.Sell, price, time_stamp)
                self.amount_limit_flag = False

            if pnl <= (self.amount_limit_num - glb.limit_presantage):
                self.amount_limit_num -= glb.limit_presantage


        self.accumulated_amount_limit += diff

    def Safe_Limit_condition_stock_trade_4(self, price, time_stamp, diff):
        low_price = self.real_low_list[-1][time_stamp]
        high_price = self.real_high_list[-1][time_stamp]
        relative_amount = price - self.relative_start_price
        proff_from_start = (100 * relative_amount / self.relative_start_price)  # in presantage
        if self.amount_limit_flag:
            self.accumulated_amount_limit += diff
        if proff_from_start <= self.amount_limit_num and self.amount_limit_flag:
            if self.flag_enter_status and self.amount_limit_flag:
                # self.accumulated_amount_limit += round(self.relative_start_price * (1 + self.amount_limit_num / 100) - price,2)
                # price = self.relative_start_price * (1 + self.amount_limit_num / 100)
                self.accumulated_amount_limit -= glb.avg_commission_per_shear
                self.store_to_logs_info_limit('SELL', time_stamp, price, 1)
                # price = self.relative_start_price * (1 + self.amount_limit_num / 100)
                self.check_real_invest_in_the_stock_and_action(SA.Sell, price, time_stamp)
            self.amount_limit_flag = False
        elif proff_from_start >= self.amount_limit_num:
            # price = round(self.relative_start_price * (1 + self.amount_limit_num / 100),2)
            if self.flag_enter_status and not self.amount_limit_flag:
                self.accumulated_amount_limit -= glb.avg_commission_per_shear
                self.store_to_logs_info_limit('BUY', time_stamp, price, 1)
                self.check_real_invest_in_the_stock_and_action(SA.Buy, price, time_stamp)
            self.amount_limit_flag = True
            if proff_from_start > (self.amount_limit_num + glb.limit_presantage):
                self.relative_start_price *= (1 + glb.limit_presantage / 100)

    # def Safe_Limit_condition_stock_trade_4(self,price,time_stamp,diff):
    #     low_price = self.real_low_list[-1][time_stamp]
    #     high_price = self.real_high_list[-1][time_stamp]
    #     diff_p = glb.diff_p
    #     pnl_limit_d = (self.amount_limit_num - diff_p)
    #     pnl_limit_u = (self.amount_limit_num + diff_p)
    #     if self.amount_limit_flag:
    #         if low_price<pnl_limit_d and pnl_limit_u<high_price:
    #             closer_to_low_price = True if abs(price-low_price)<abs(price-high_price) else False
    #             if closer_to_low_price:
    #                 diff = pnl_limit_d - self.real_close_list[-1][time_stamp-1]
    #                 #sell
    #             else:
    #                 diff = pnl_limit_d - self.real_close_list[-1][time_stamp-1] +price-pnl_limit_u
    #                 #sell & Buy
    #         elif low_price<pnl_limit_d:
    #                 #sell
    #     else:
    #         if low_price<pnl_limit_d and pnl_limit_u<high_price:
    #             closer_to_low_price = True if abs(price-low_price)<abs(price-high_price) else False
    #             if closer_to_low_price:
    #
    #                 #sell
    #             else:
    #                 diff = pnl_limit_d - self.real_close_list[-1][time_stamp-1] +price-pnl_limit_u
    #                 #sell & Buy
    #         elif low_price<pnl_limit_d:
    #                 #sell
    #
    #     relative_amount = price - self.relative_start_price
    #     proff_from_start = (100 * relative_amount / self.relative_start_price)  # in presantage
    #     pnl= proff_from_start
    #     if self.amount_limit_flag:
    #         self.accumulated_amount_limit += diff
    #
    #     if pnl < pnl_limit_d and self.amount_limit_flag:
    #         if self.flag_enter_status and self.amount_limit_flag:
    #             # self.accumulated_amount_limit += round(self.relative_start_price * (1 + self.amount_limit_num / 100) - price,2)
    #             # price = self.relative_start_price * (1 + self.amount_limit_num / 100)
    #             self.accumulated_amount_limit -= glb.avg_commission_per_shear
    #             self.store_to_logs_info_limit('SELL', time_stamp, price, 1)
    #         # price = self.relative_start_price * (1 + self.amount_limit_num / 100)
    #             self.check_real_invest_in_the_stock_and_action(SA.Sell, price, time_stamp)
    #         self.amount_limit_flag = False
    #     elif pnl >= pnl_limit_u:
    #         # price = round(self.relative_start_price * (1 + self.amount_limit_num / 100),2)
    #         if self.flag_enter_status and not self.amount_limit_flag:
    #             self.accumulated_amount_limit -= glb.avg_commission_per_shear
    #             self.store_to_logs_info_limit('BUY', time_stamp, price, 1)
    #             self.check_real_invest_in_the_stock_and_action(SA.Buy, price, time_stamp)
    #         self.amount_limit_flag = True
    #         if pnl > (self.amount_limit_num + glb.limit_presantage):
    #             self.relative_start_price *= (1+glb.limit_presantage/100)
    #

    def Safe_Limit_condition_stock_trade_3(self,price,time_stamp,diff):
        low_price = self.real_low_list[-1][time_stamp]
        high_price = self.real_high_list[-1][time_stamp]
        open_price = self.real_open_list[-1][time_stamp]
        close_price = self.real_close_list[-1][time_stamp]

        relative_amount_u = high_price - self.relative_start_price
        relative_amount_d = low_price - self.relative_start_price

        proff_from_start_u = (100 * relative_amount_u / self.relative_start_price)  # in presantage
        proff_from_start_d = (100 * relative_amount_d / self.relative_start_price)  # in presantage
        diff = diff if self.amount_limit_flag else 0
        check_in_price = None
        if self.amount_limit_flag:
            if time_stamp>0:
                check_in_price = self.real_close_list[-1][time_stamp-1]
            else:
                check_in_price = self.real_close_list[-2][-1]

        diff_p = glb.diff_p

        pnl_limit_d = (self.amount_limit_num-diff_p)
        pnl_limit_u = (self.amount_limit_num+diff_p)
        flag_2 = False

        if open_price>close_price:
            pnl = proff_from_start_u
            if self.flag_enter_status and not self.amount_limit_flag and pnl>pnl_limit_u:
                price = self.relative_start_price * (1 + pnl_limit_u / 100)
                self.accumulated_amount_limit -= glb.avg_commission_per_shear
                self.store_to_logs_info_limit('BUY', time_stamp, price, 1)
                self.check_real_invest_in_the_stock_and_action(SA.Buy, price, time_stamp)
                self.amount_limit_flag = True
                check_in_price = price
                diff = close_price - price
                flag_2 = True

            if pnl >= (self.amount_limit_num + glb.limit_presantage):
                self.amount_limit_num += glb.limit_presantage
                pnl_limit_d = (self.amount_limit_num - diff_p)

            pnl = proff_from_start_d
            if self.flag_enter_status and self.amount_limit_flag and pnl < pnl_limit_d:
                if flag_2:
                    j=0
                price = self.relative_start_price * (1 + pnl_limit_d / 100)
                self.accumulated_amount_limit -= glb.avg_commission_per_shear
                self.store_to_logs_info_limit('SELL', time_stamp, price, 1)
                self.check_real_invest_in_the_stock_and_action(SA.Sell, price, time_stamp)
                self.amount_limit_flag = False
                diff = price - check_in_price

            if pnl <= (self.amount_limit_num - glb.limit_presantage):
                self.amount_limit_num -= glb.limit_presantage

        elif open_price < close_price:
            pnl = proff_from_start_d
            if self.flag_enter_status and self.amount_limit_flag and pnl < pnl_limit_d:
                price = self.relative_start_price * (1 + pnl_limit_d / 100)
                self.accumulated_amount_limit -= glb.avg_commission_per_shear
                self.store_to_logs_info_limit('SELL', time_stamp, price, 1)
                self.check_real_invest_in_the_stock_and_action(SA.Sell, price, time_stamp)
                self.amount_limit_flag = False
                diff = price - check_in_price
                flag_2 = True


            if pnl <= (self.amount_limit_num - glb.limit_presantage):
                self.amount_limit_num -= glb.limit_presantage
                pnl_limit_u = (self.amount_limit_num + diff_p)

            pnl = proff_from_start_u
            if self.flag_enter_status and not self.amount_limit_flag and pnl > pnl_limit_u:
                if flag_2:
                    j=0
                price = self.relative_start_price * (1 + pnl_limit_u / 100)
                self.accumulated_amount_limit -= glb.avg_commission_per_shear
                self.store_to_logs_info_limit('BUY', time_stamp, price, 1)
                self.check_real_invest_in_the_stock_and_action(SA.Buy, price, time_stamp)
                self.amount_limit_flag = True
                diff += close_price - price

            if pnl >= (self.amount_limit_num + glb.limit_presantage):
                self.amount_limit_num += glb.limit_presantage
        # else:
        #     if proff_from_start_d <= (self.amount_limit_num - glb.limit_presantage):
        #         self.amount_limit_num -= glb.limit_presantage
        #
        #     if proff_from_start_u >= (self.amount_limit_num + glb.limit_presantage):
        #         self.amount_limit_num += glb.limit_presantage


        self.accumulated_amount_limit += diff

            #######################
        # # pnl= proff_from_start
        # pnl= proff_from_start_d if self.amount_limit_flag else proff_from_start_u
        #
        # factor = glb.factor
        # if pnl < pnl_limit_d:
        #     pnl = proff_from_start_d
        #     if self.flag_enter_status and self.amount_limit_flag:
        #         price = self.relative_start_price*(1+pnl_limit_d/100)
        #         diff_n = price-self.real_avg_list[-1][time_stamp-1]
        #         self.accumulated_amount_limit -= diff
        #         self.accumulated_amount_limit += diff_n
        #
        #         # self.accumulated_amount_limit += round(self.relative_start_price * (1 + self.amount_limit_num / 100) - price,2)
        #         # price = self.relative_start_price * (1 + self.amount_limit_num / 100)
        #         self.accumulated_amount_limit -= glb.avg_commission_per_shear
        #         self.store_to_logs_info_limit('SELL', time_stamp, price, 1)
        #     # price = self.relative_start_price * (1 + self.amount_limit_num / 100)
        #         self.check_real_invest_in_the_stock_and_action(SA.Sell, price, time_stamp)
        #     if pnl <= (self.amount_limit_num - factor*glb.limit_presantage):
        #         self.relative_start_price *= (1-factor*glb.limit_presantage/100)
        #     self.amount_limit_flag = False
        # elif pnl >= pnl_limit_u:
        #     pnl = proff_from_start_u
        #     # price = round(self.relative_start_price * (1 + self.amount_limit_num / 100),2)
        #     if self.flag_enter_status and not self.amount_limit_flag:
        #         price = self.relative_start_price *(1+pnl_limit_u/100)
        #         diff_n = self.real_avg_list[-1][time_stamp] - price
        #         self.accumulated_amount_limit += diff_n
        #         self.accumulated_amount
        #         _limit -= glb.avg_commission_per_shear
        #         self.store_to_logs_info_limit('BUY', time_stamp, price, 1)
        #         self.check_real_invest_in_the_stock_and_action(SA.Buy, price, time_stamp)
        #     self.amount_limit_flag = True
        #     if pnl >= (self.amount_limit_num + glb.limit_presantage):
        #         self.relative_start_price *= (1+glb.limit_presantage/100)
        # self.accumulated_amount_limit += diff

    def Safe_Limit_condition_stock_trade_2(self,price,time_stamp,diff):
        low_price = self.real_low_list[-1][time_stamp]
        high_price = self.real_high_list[-1][time_stamp]
        relative_amount = price - self.relative_start_price
        add_limit = glb.limit_presantage
        proff_from_start = (100 * relative_amount / self.relative_start_price)  # in presantage
        if self.amount_limit_flag:
            self.accumulated_amount_limit += diff
        if ((low_price - self.relative_start_price)/100) < self.amount_limit_num and self.amount_limit_flag:
            if self.flag_enter_status and self.amount_limit_flag:
                self.accumulated_amount_limit += round(self.relative_start_price * (1 + self.amount_limit_num / 100) - price,2)
                price = self.relative_start_price * (1 + self.amount_limit_num / 100)
                self.accumulated_amount_limit -= glb.avg_commission_per_shear
                self.store_to_logs_info_limit('SELL', time_stamp, price, 1)
            price = self.relative_start_price * (1 + self.amount_limit_num / 100)
            self.check_real_invest_in_the_stock_and_action(SA.Sell, price, time_stamp)
            # self.sell_shears(time_stamp, self.shears, 'avg')
            self.amount_limit_flag = False
        elif proff_from_start >= self.amount_limit_num:
            price = round(self.relative_start_price * (1 + self.amount_limit_num / 100),2)
            if self.flag_enter_status and not self.amount_limit_flag:
                self.accumulated_amount_limit -= glb.avg_commission_per_shear
                self.store_to_logs_info_limit('BUY', time_stamp, price, 1)
            self.check_real_invest_in_the_stock_and_action(SA.Buy, price, time_stamp)
            # self.buy_shears(time_stamp, int(self.available_money / self.real_avg_list[-1][time_stamp]), 'avg')  # closeX2
            self.amount_limit_flag = True
            if proff_from_start > (self.amount_limit_num + add_limit):
                # add_limit = max(add_limit,proff_from_start)
                self.amount_limit_num = proff_from_start


    def Safe_Limit_condition_stock_trade(self,price,time_stamp,diff):
        relative_amount = self.accumulated_amount - self.start_accumulated_amount
        # relative_amount_min = price - self.min_per_day 5883%-0.1->5274%-0.15
        # relative_amount_min = price - self.min_per_day 19800%-0.1->19800%-0.15->9250%-0.5
        start_limit = 0
        add_limit = glb.limit_presantage
        proff_from_start = (100 * relative_amount / self.relative_start_price) #in presantage
        if self.amount_limit_flag:
            self.accumulated_amount_limit += diff
        if proff_from_start > self.amount_limit_num:
            if self.flag_enter_status and not self.amount_limit_flag:
                self.accumulated_amount_limit -= glb.avg_commission_per_shear
                self.store_to_logs_info_limit('BUY', time_stamp, price, 1)
            self.check_real_invest_in_the_stock_and_action(SA.Buy, price, time_stamp)
                # self.buy_shears(time_stamp, int(self.available_money / self.real_avg_list[-1][time_stamp]), 'avg')  # closeX2
            self.amount_limit_flag = True
            if proff_from_start > (self.amount_limit_num + add_limit):
                # add_limit = max(add_limit,proff_from_start)
                self.amount_limit_num = proff_from_start
        elif proff_from_start < self.amount_limit_num:
            price = self.relative_start_price*(1+ self.amount_limit_num/100)
            if self.flag_enter_status and self.amount_limit_flag:
                self.accumulated_amount_limit -= glb.avg_commission_per_shear
                self.store_to_logs_info_limit('SELL', time_stamp, price, 1)
            self.check_real_invest_in_the_stock_and_action(SA.Sell, price, time_stamp)
                # self.sell_shears(time_stamp, self.shears, 'avg')
            self.amount_limit_flag = False


    def plotting_all_data(self, start, end):
        # bbb = np.round(100 * np.array((self.gaps_list)) / self.real_avg_list[0][0], 3)
        # bbb = [(bbb[i],bbb[:i+1].sum()) for i in range(len(bbb))]
        # list_acumilated_gaps = [sum(self.gaps_list[:i]) for i in range(1,len(self.gaps_list)+1)]
        # for i in range(len(bbb)):
        #     print((bbb[i], bbb[:i + 1].sum()))
        figure, axis = plt.subplots(2, 1)
        figure.suptitle(self.stock_name + '_' + start + '->' + end + ' sum gaps:' + '%.2f' % (np.array((self.gaps_list)).sum()),fontsize=16)
        figure.tight_layout(h_pad=2)
        sub_lines_width = 0.3
        for i in self.minutes_per_day:
            axis[0].axvline(x=i, linewidth=sub_lines_width, color="y", linestyle="--")
            axis[1].axvline(x=i, linewidth=sub_lines_width, color="y", linestyle="--")
            # axis[2].axvline(x=i, linewidth=sub_lines_width, color="y", linestyle="--")
            # axis[3].axvline(x=i, linewidth=sub_lines_width, color="y", linestyle="--")

        real_avg_list = sum(self.real_avg_list, [])
        real_close_list = sum(self.real_close_list, [])
        real_high_list = sum(self.real_high_list, [])
        real_low_list = sum(self.real_low_list, [])
        real_open_list = sum(self.real_open_list, [])

        # for i in range(self.counter):
        #     # High-Low line
        #     axis[0].plot([i, i], [real_low_list[i], real_high_list[i]], color='black', linewidth=0.1)
        #
        #     # Open-Close rectangle
        #     if real_close_list[i] > real_open_list[i]:
        #         # Green bar for bullish candles
        #         color = 'g'
        #         lower = real_open_list[i]
        #         height = real_close_list[i] - real_open_list[i]
        #     else:
        #         # Red bar for bearish candles
        #         color = 'r'
        #         lower = real_close_list[i]
        #         height = real_open_list[i] - real_close_list[i]
        #
        #     axis[0].bar(i, height, bottom=lower, color=color, width=1.2)
        # # axis[2].xticks(self.counter, self.counter, rotation=45)  # Add date labels on the x-axis
        # # axis[2].title("Candlestick Chart (Custom with Matplotlib)")
        # # axis[2].xlabel("Date")
        # # axis[2].ylabel("Price")
        # axis[0].grid(axis='y', linestyle='--', alpha=0.7)

        # axis[0].plot(np.arange(self.counter), real_avg_list, color='y', label="real avg")
        axis[0].plot(np.arange(self.counter), real_close_list, color='y', label="real_close_list")
        gap_list = glb.stocks_data[self.stock_name]['real_close']
        # axis[0].plot(np.arange(self.counter), sum(gap_list, []), color='purple', label="avg no gap",linewidth=0.2)
        axis[0].set_title(
            "start:" + '%.2f' % (real_avg_list[0]) + " end:" + '%.2f' % (real_avg_list[-1]) + ' diff:' + '%.2f' % (
                        real_avg_list[-1] - real_avg_list[0]) + " max/min/end: " + '%.1f' % (
                        100 * ((max(real_avg_list) - real_avg_list[0]) / real_avg_list[0])) + '%,' + '%.1f' % (
                        100 * ((min(real_avg_list) - real_avg_list[0]) / real_avg_list[0])) + '%,' + '%.1f' % (
                        100 * ((real_avg_list[-1] - real_avg_list[0]) / real_avg_list[0])) + '%')

        axis[1].plot(np.arange(self.counter), self.amount_list, color='r')
        axis[1].plot(np.arange(self.counter), self.amount_list_no_gap, color='y')
        axis[1].plot(np.arange(self.counter), self.amount_limit, color='blue')
        # axis[1].plot(self.minutes_per_day, list_acumilated_gaps, color='orange')
        axis[1].axhline(y=0, linewidth=sub_lines_width, color="g", linestyle="--")
        axis[1].set_title("amount-> end val:" + '%.2f' % (self.amount_limit[-1]) + " max/min/end: " + '%.1f' % (100 * ((max(self.amount_limit)) / real_avg_list[0])) + '%,' + '%.1f' % (100 * ((min(self.amount_limit)) / real_avg_list[0])) + '%,' + '%.1f' % (100 * (self.amount_limit[-1] / real_avg_list[0])) + '%,' + '%.1f' % (100 * (self.amount_limit[-1] / real_avg_list[0])) + '%')


        # axis[2].tight_layout()
        # correction_2 = 1e3
        # # axis[2].plot(np.arange(self.counter), np.array(self.long_slope) * correction_2, color='g')
        # # axis[2].plot(np.arange(self.counter), np.array(self.short_slope) * correction_2, color='r')
        # axis[2].plot(np.arange(self.counter), np.array(self.slop_mix_slope) , color='r')
        # axis[2].set_title("long_slope*1e3-> avg" + '%.2f' % (correction_2 * sum(self.long_slope) / self.counter) + " max: " + '%.2f' % (correction_2 * max(self.long_slope)) + ' min:' + '%.2f' % (correction_2 * min(self.long_slope)))
        # axis[2].axhline(y=0, linewidth=sub_lines_width, color="g", linestyle="--")
        # # axis[2].axhline(y=-0.15, linewidth=sub_lines_width, color="g", linestyle="--")
        # # axis[2].axhline(y=0.15, linewidth=sub_lines_width, color="g", linestyle="--")
        #
        # correction_3 = 1e3
        # axis[3].plot(np.arange(self.counter), (np.array(self.mix_slope)) * correction_3, color='r')
        # axis[3].set_title("short_slope*1e3-> avg" + '%.2f' % (correction_3 * sum(self.short_slope) / self.counter) + " max: " + '%.2f' % (correction_3 * max(self.short_slope)) + ' min:' + '%.2f' % (correction_3 * min(self.short_slope)))
        # axis[3].axhline(y=0, linewidth=sub_lines_width, color="g", linestyle="--")
        # # axis[3].axhline(y=-0.5, linewidth=sub_lines_width, color="g", linestyle="--")
        # # axis[3].axhline(y=0.5, linewidth=sub_lines_width, color="g", linestyle="--")

        # axis[3].set_ylim([-0.3, 0.3])
        # dd =np.array(self.short_slope)
        # dd = dd[dd<glb.slop_d_num_neg_flag]
        figure.savefig(glb.PATH_RESULTS +'/'+ self.stock_name+'/'+ self.stock_name + '_' + start + '->' + end,dpi=300)
        all_results_path_dates = glb.PATH_RESULTS + '/ALL_RESULTS'+'/ALL_stocks_for_'+ start + '->' + end
        if not os.path.isdir(all_results_path_dates):
            os.mkdir(all_results_path_dates)
        figure.savefig(all_results_path_dates+'/'+ self.stock_name,dpi=300)
        # plt.show()
        # plt.clf()

        return

    def store_to_logs_info(self,action,time_stamp,price,shears):
        self.demo_logs.append(glb.current_date+' Demo, time stamp:'+str(time_stamp)+' action:'+action+' price:'+str(price)+' shears:'+str(shears)+ ' proff:'+"%.2f" %(100*self.accumulated_amount/self.real_avg_list[0][0]))
    def store_to_logs_info_limit(self,action,time_stamp,price,shears):
        sign = 1 if 'BUY' in action else -1
        self.demo_limit_logs.append(glb.current_date+' Demo limit, time stamp:'+str(time_stamp)+' ,action:'+action+' ,price:'+str(price)+' ,shears:'+str(shears)+ ' ,commission:glb.avg_commission_per_shear ,proff:'+"%.2f" %(100*self.accumulated_amount_limit/self.real_avg_list[0][0]))
        self.demo_limit_logs_csv.append([glb.current_date,time_stamp,action,price,sign*shears,glb.avg_commission_per_shear,round(100*self.accumulated_amount_limit/self.real_avg_list[0][0],2),self.real_close_list[-1][time_stamp]])
        if len(self.demo_limit_logs_csv)>1:
            last_action = self.demo_limit_logs_csv[-2][2]
            if  action == last_action:
                raise RuntimeError
    def write_to_log_info(self):
        import csv
        if not os.path.isdir(glb.PATH_RESULTS):
            os.mkdir(glb.PATH_RESULTS)
        stock_path = glb.PATH_RESULTS + '/'+self.stock_name
        if not os.path.isdir(stock_path):
            os.mkdir(stock_path)
        stock_log_path = stock_path+'/log_Demo_'+self.stock_name+'.txt'
        with open(stock_log_path, 'w') as f:
            for line in self.demo_logs:
                f.write(line + '\n')
        stock_log_path = stock_path+'/log_Demo_Limit_'+self.stock_name+'.txt'
        with open(stock_log_path, 'w') as f:
            for line in self.demo_limit_logs:
                f.write(line + '\n')
        stock_log_path = stock_path+'/log_Demo_Limit_'+self.stock_name+'.xlsx'
        import pandas as pd
        writer = pd.ExcelWriter(stock_log_path, engine='xlsxwriter', mode='w')
        head_lines = ['Dates','min_num','action','stock_price','shears_transaction','commision','algo_profit']
        main_sheet = [head_lines] + self.demo_limit_logs_csv
        df = pd.DataFrame(main_sheet)
        df.to_excel(writer, sheet_name=self.stock_name, index=False)
        writer.close()
        # with open(stock_log_path, 'w') as f:
        #     writer = csv.writer(f)
        #     writer.writerow(['Dates','min_num','action','stock_price','shears_transaction','commision','algo_profit'])
        #     writer.writerows(self.demo_limit_logs_csv)


def simulate_day_trading_local_data(stock_object: Demo_Stock_Object, day_num):
    stock = stock_object.stock_name
    size_a =len(glb.stocks_data[stock]['avg'][day_num])
    if size_a < 385:
        raise RuntimeError(f"{stock} in day : {day_num}/{glb.stocks_data[stock]['days']} have only {size_a} points")
    # gap = (glb.stocks_data[stock]['close'][day_num][0] - stock_object.real_avg_list[-1][-1]) if day_num>0 else 0
    # fixed_arr = (np.array(glb.stocks_data[stock]['close'][day_num])-gap).tolist()
    # stock_object.real_avg_list.append(fixed_arr)
    stock_object.real_avg_list.append(glb.stocks_data[stock]['close'][day_num][:size_a])
    stock_object.real_close_list.append(glb.stocks_data[stock]['close'][day_num][:size_a])
    stock_object.real_open_list.append(glb.stocks_data[stock]['open'][day_num][:size_a])
    stock_object.real_high_list.append(glb.stocks_data[stock]['high'][day_num][:size_a])
    stock_object.real_low_list.append(glb.stocks_data[stock]['low'][day_num][:size_a])
    stock_object.real_volume_list.append(glb.stocks_data[stock]['volume'][day_num][:size_a])
    # if day_num>0:
    #     diff_list = sorted(np.abs(np.array(glb.stocks_data[stock]['close'][day_num-1]) - np.array(glb.stocks_data[stock]['open'][day_num-1])))
    #     glb.diff_p = 2*100*np.mean(diff_list[int(size_a*0.5):int(size_a*0.8)])/glb.stocks_data[stock]['close'][day_num-1][0]
    #     glb.diff_p = 0.5
    simulate_trading_local_data(stock_object,day_num)

    stock_object.barrier.wait()  ###########
    if stock_object.stock_name == glb.job_by_one_thread:
        glb.not_first_day = True
    return True

def binary_tree_search(list_search, val):
    if len(list_search) == 1 or list_search[0] == val:
        idx = 0 if list_search[0] > 0 else 1
        return idx
    size_2 = len(list_search) // 2
    if list_search[size_2] > val:
        return binary_tree_search(list_search[:size_2], val)
    else:
        return size_2 + binary_tree_search(list_search[size_2:], val)


def simulate_trading_local_data(stock_object: Demo_Stock_Object, day_num):
    """
    The main simulation loop for a single stock on a given day.

    This function is executed in a separate thread for each stock. It simulates
    the trading strategy on a minute-by-minute basis using historical data.

    Args:
        stock_object (Demo_Stock_Object): The stock object to simulate.
        day_num (int): The index of the day to simulate.
    """
    if stock_object.stock_name == glb.job_by_one_thread:
        glb.current_date = glb.stocks_data[stock_object.stock_name]['dates'][day_num]
        if glb.dbg_on_real_data:
            glb.current_date = glb.current_date[0]
            # glb.current_date = glb.stocks_data[stock_object.stock_name]['dates'][day_num][0].split(' ')[0]
        glb.min_num_of_time_stamp_in_stocks_current_day = 9999
    stock_object.barrier.wait()

    # avg_list_day_ago = stock_object.real_avg_list[-2]
    avg_list_day = np.array(stock_object.real_avg_list[-1])
    # avg_list_day = np.array(stock_object.real_close_list[-1])
    current_list_day = np.array(stock_object.real_avg_list[-1])
    num_of_elements_in_data = len(avg_list_day)
    with key_lock:
        glb.min_num_of_time_stamp_in_stocks_current_day = min(glb.min_num_of_time_stamp_in_stocks_current_day,
                                                              num_of_elements_in_data)
    stock_object.barrier.wait()
    start_accumulated_amount_limit = 0
    if not stock_object.flag_first_day:
        gap = stock_object.real_avg_list[-1][0] - stock_object.real_avg_list[-2][-1]
        stock_object.minutes_per_day.append(num_of_elements_in_data + stock_object.minutes_per_day[-1])
        stock_object.gaps_list.append(gap)
        stock_object.accumulated_amount = stock_object.amount_list[-1] + gap if stock_object.flag_enter_status else \
        stock_object.amount_list[-1]
        stock_object.start_accumulated_amount = stock_object.accumulated_amount
        stock_object.amount_limit_num = 0
        start_accumulated_amount_limit = stock_object.accumulated_amount_limit
        # stock_object.after_hours(avg_list_day[0],stock_object.real_avg_list[-2][-1])

    else:
        stock_object.gaps_list.append(0)
        stock_object.minutes_per_day.append(num_of_elements_in_data)
        stock_object.relative_start_price = avg_list_day[0]
        stock_object.amount_limit_num = 0

    stock_object.avg_list_no_gap.append(list(np.array(avg_list_day - (np.array(stock_object.gaps_list)).sum())))
    stock_object.min_per_day = avg_list_day[0]
    if not stock_object.flag_first_day:
        volume_list = stock_object.real_volume_list[-2] + stock_object.real_volume_list[-1]
    else:
        volume_list = stock_object.real_volume_list[-1]

    # avg_list_day_ago = list(np.array(avg_list_day_ago) + avg_list_day[0] - avg_list_day_ago[-1])
    # combine_avg = np.array(avg_list_day_ago + list(avg_list_day))
    # combine_time_stamp_start = len(avg_list_day_ago)

    #### this will be change to 1 min delay and check if the market is closed(1 min before) ###
    for time_stamp in range(num_of_elements_in_data):

        #### request market data ###
        # price = avg_list_day[time_stamp] #real: get stock last price
        price = current_list_day[time_stamp]  # real: get stock last price
        if not stock_object.flag_first_day:
            last_volume_list = sorted(
                volume_list[(-num_of_elements_in_data + time_stamp - 380):(-num_of_elements_in_data + time_stamp)])
            lower_half_volume = last_volume_list[:len(last_volume_list) // 2]
            stock_object.avg_volume = sum(lower_half_volume) / len(lower_half_volume)
        elif glb.dbg_on_real_data:
            last_volume_list = sorted(volume_list)
            lower_half_volume = last_volume_list[:len(last_volume_list) // 2]
            stock_object.avg_volume = sum(lower_half_volume) / len(lower_half_volume)
        else:
            stock_object.avg_volume = sum(volume_list[:time_stamp + 1]) / (time_stamp + 1)

        #### i think this part should be in the end of the minute ####
        if stock_object.flag_first_day and time_stamp == 0 and time_stamp < glb.min_num_of_time_stamp_in_stocks_current_day:  # time_stamp % 5 == 0 and
            stock_object.check_real_invest_in_the_stock_and_action(SA.Collect_divide_again,
                                                                    time_stamp)  #### real: no needed
            stock_object.break_point_to_divide_the_real_money_between_stocks(time_stamp)

        if stock_object.accumulated_amount > stock_object.max_amount:
            stock_object.max_amount = stock_object.accumulated_amount
        # if price < stock_object.min_per_day and False:
        #     stock_object.min_per_day = price
        #     if 100*(avg_list_day[0]-price)/avg_list_day[0] > glb.limit_presantage:
        #         stock_object.start_accumulated_amount = stock_object.accumulated_amount
        #         stock_object.amount_limit_num = glb.limit_presantage
        #         stock_object.relative_start_price = price
        # if price < (stock_object.relative_start_price*(100-glb.limit_presantage)/100):
        #     stock_object.relative_start_price = stock_object.relative_start_price*(100-glb.limit_presantage)/100

        # 43814%-1->2800%-2->53426%-0.5
        # 28190%->0
        stock_object.analyze_the_histogram_and_set_the_next_action(avg_list_day, time_stamp, price)
        stock_interval_change = round((float(avg_list_day[time_stamp] - avg_list_day[time_stamp - 1])),
                                      2) if time_stamp > 0 else 0

        #### this part need to change to order requests ####
        stock_object.simulate_the_next_trade(price, stock_interval_change, time_stamp)
        stock_object.Safe_Limit_condition_stock_trade_5(price, time_stamp, stock_interval_change)

        #### this will help me devide the money with the potntial stocks ####
        stock_object.accumulated_amount_percentage_day = 100 * (
                    stock_object.accumulated_amount_limit - start_accumulated_amount_limit) / \
                                                          stock_object.real_avg_list[0][0]
        # stock_object.accumulated_amount_percentage_day = 100*(stock_object.accumulated_amount-stock_object.start_accumulated_amount)/stock_object.real_avg_list[0][0]

        #### collect statistic data ####
        stock_object.amount_list.append(stock_object.accumulated_amount)
        stock_object.amount_list_no_gap.append(stock_object.accumulated_amount_no_gap)
        stock_object.amount_limit.append(stock_object.accumulated_amount_limit)

        # stock_object.pull_spare_money()
        stock_object.counter += 1
        # print(stock_object.stock_name+' time_stamp:'+str(time_stamp))

        if time_stamp < glb.min_num_of_time_stamp_in_stocks_current_day:
            glb.day_barrier.wait()

    #### 1 min before end of the day close postion ###
    # stock_object.check_real_invest_in_the_stock_and_action(SA.Sell, stock_object.real_avg_list[-1][-1], num_of_elements_in_data-1)
    # if stock_object.amount_limit_flag:
    #     stock_object.accumulated_amount_limit += -glb.avg_commission_per_shear
    #     stock_object.store_to_logs_info_limit('SELL', num_of_elements_in_data-1, stock_object.real_avg_list[-1][-1], 1)
    #     stock_object.amount_limit_flag = False

    stock_object.flag_first_day = False
    #### in case i would like to hold the stock during the night(need to cancel the section before)
    # if not stock_object.flag_enter_status and not stock_object.flag_last_day:
    #     stock_object.buy_shears(-1, int(stock_object.available_money / stock_object.real_avg_list[-1][-1]),'avg')  # closeX2
    #     #if not stock_object.amount_limit_flag:
    #     stock_object.sell_phase = True
    #     # stock_object.amount_list[-1] -= max(1.0,stock_object.shears*glb.avg_commission_per_shear)
    #     stock_object.amount_list[-1] -= glb.avg_commission_per_shear
    # if stock_object.stock_name in glb.my_portfolio:
    #     glb.my_portfolio[stock_object.stock_name].return_available_real_cash()





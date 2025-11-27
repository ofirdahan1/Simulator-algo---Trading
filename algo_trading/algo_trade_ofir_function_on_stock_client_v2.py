import numpy as np
import datetime as dt

import time
# import yfinance as yf
import os
import copy

from scipy import stats
# import logging
import threading
import globals_v2 as glb
from globals_v2 import Real_Stock_actions as SA
from ibkr_connection import *


key_lock_money_divide = threading.Lock()


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
        with glb.my_portfolio[stock].key_lock_available_money:
            glb.my_portfolio[stock].available_money += new_cash_invest_stock
            glb.my_portfolio[stock].init_money += new_cash_invest_stock
    else:
        glb.my_portfolio.update({stock: glb.Real_Stock_Object(stock,None,new_cash_invest_stock)})


def divide_available_money(time_stamp:int,timeout = 15):
    if time_stamp>0:
        with glb.condition_clock_start:
            diff_time = glb.time_next_minute_break_ten_sec_before - dt.datetime.now()
        if diff_time.days == 0 and diff_time.seconds < 60:
            time.sleep(diff_time.seconds + diff_time.microseconds / 1e6)
    start_time = time.time()
    glb.request_stream_data_collection = True
    time.sleep(1)
    while len(glb.client.ordId_active)>0 and glb.client.active:
        glb.client.reqGlobalCancel()
        time.sleep(1)
    glb.request_stream_data_collection = False

    end_time = start_time+timeout
    def clean_non_potential_stocks_from_portfolio(new_potential_stocks_list):
        stock_return_money = []
        # selling_threads = []
        for stock in glb.my_portfolio:
            if stock in new_potential_stocks_list:
                glb.my_portfolio[stock].flag_invest_in_this_stock = True
            else:
                glb.my_portfolio[stock].flag_invest_in_this_stock = False
                if stock not in glb.client.stocks_data:
                    sub_thread = threading.Thread(target=glb.client.add_stock_to_stock_list, args=(stock,))
                    sub_thread.start()
                    sub_thread.join()
                if glb.my_portfolio[stock].shears>0:
                    sub_thread = threading.Thread(target=glb.client.try_buy_sell, args=(stock, 'SELL', glb.my_portfolio[stock].shears, 60,))
                    sub_thread.start()
            if glb.my_portfolio[stock].shears < 0:
                sub_thread = threading.Thread(target=glb.client.try_buy_sell, args=(stock, 'BUY', -1*glb.my_portfolio[stock].shears, 60,))
                # selling_threads.append(sub_thread)
                sub_thread.start()
        if len(stock_return_money) > 0:
            time.sleep(6)
        for stock in glb.my_portfolio:
            glb.my_portfolio[stock].return_available_real_cash()

        #         pop_stock_list.append(stock)
        # for stock in pop_stock_list:
        #     glb.my_portfolio.pop(stock)

    def decide_which_stocks_are_possible_to_be_most_profit(time_stamp:int):
        if time_stamp>0:
            profit_stocks = [[glb.demo_portfolio_treads[stock].accumulated_amount_percentage_day*glb.demo_portfolio_treads[stock].avg_volume, stock] for stock in glb.demo_portfolio_treads if ((200<glb.demo_portfolio_treads[stock].avg_volume)) ]#  and glb.demo_portfolio_treads[stock].amount_limit_flag)      glb.demo_portfolio_treads[stock].accumulated_amount_percentage_day>-100 and
            profit_stocks.sort(key=lambda x: x[0], reverse=True)
            if len(profit_stocks) == 0:
                return [],[1],0
            if profit_stocks[-1][0] <= 0:
                abs_min = abs(profit_stocks[-1][0])
                for idx, ratio_stock in enumerate(profit_stocks):
                    profit_stocks[idx][0] += abs_min + 0.00001
            # profit_stocks= profit_stocks[:4] if len(profit_stocks)>4 else profit_stocks
            sum_slop = [float(x[0]) for x in profit_stocks]
            idx_lim = len(sum_slop)
        else:
            profit_stocks = [[1, stock] for stock in glb.demo_portfolio_treads if 1 < glb.demo_portfolio_treads[stock].avg_volume]
            sum_slop = np.ones(len(profit_stocks))
            idx_lim = len(sum_slop)
        return profit_stocks,sum_slop,idx_lim
    stock = next(iter(glb.demo_portfolio_treads))
    glb.client.write_to_file(f"DIVIDE: conter' {glb.demo_portfolio_treads[stock].counter}")
    # print('DIVIDE: conter', (glb.demo_portfolio_treads[stocks[0]].counter))
    profit_stocks,sum_slop,idx_lim = decide_which_stocks_are_possible_to_be_most_profit(time_stamp)
    if len(profit_stocks) == 0:
        clean_non_potential_stocks_from_portfolio(["None"])
        return
    timeout_a = end_time - time.time()
    if not glb.client.get_straming_acount(timeout_a):
        return
    clean_non_potential_stocks_from_portfolio(np.array(profit_stocks)[:, 1])
    with glb.client.key_lock:
        if not glb.client.active:
            return
    sum_of_sum_slop = sum(sum_slop)
    with glb.key_lock_available_money:
        total_money_to_divide = (glb.my_available_money_dollar-500)
    partial_money = total_money_to_divide / sum_of_sum_slop #real: need to get available buying power
    glb.client.write_to_file(f"DIVIDE: divide total money of: {total_money_to_divide}")
    stock_that_got_divide = []
    for idx, ratio_stock in enumerate(profit_stocks):
        if total_money_to_divide > 0:
            if idx < idx_lim:
                # update_my_portfolio_files(ratio_stock[1], 0, 0)
                price = glb.demo_portfolio_treads[ratio_stock[1]].current_price
                # price = 115
                # new_cash_invest_stock = max(0,min(round(partial_money * ratio_stock[0], 2),glb.demo_portfolio_treads[ratio_stock[1]].avg_volume+price*5-glb.my_portfolio[ratio_stock[1]].total_stock_net_value))
                glb.my_portfolio[ratio_stock[1]].total_stock_net_value = glb.my_portfolio[ratio_stock[1]].shears * price + glb.my_portfolio[ratio_stock[1]].available_money
                stock_current_net = glb.my_portfolio[ratio_stock[1]].total_stock_net_value if ratio_stock[1] in glb.my_portfolio else 0
                with glb.key_lock_available_money:
                    new_cash_invest_stock = max(0, min(glb.my_available_money_dollar - 500, round(partial_money * ratio_stock[0], 2), glb.demo_portfolio_treads[ratio_stock[1]].avg_volume * price - stock_current_net))
                    predict_trade_commission = round(max(1.0, 0.007 * new_cash_invest_stock / price), 3)
                    stock_net = glb.my_portfolio[ratio_stock[1]].total_stock_net_value+new_cash_invest_stock
                    if stock_net*0.0004 < predict_trade_commission*2:
                        continue
                    glb.my_available_money_dollar -= new_cash_invest_stock
                update_my_portfolio_files(ratio_stock[1], new_cash_invest_stock, profit_stocks[idx][0] / sum_of_sum_slop)
                glb.my_portfolio[ratio_stock[1]].flag_invest_in_this_stock = True
                glb.my_portfolio[ratio_stock[1]].total_stock_net_value = glb.my_portfolio[ratio_stock[1]].shears * price + glb.my_portfolio[ratio_stock[1]].available_money
                optional_cash = glb.my_portfolio[ratio_stock[1]].total_stock_net_value
                glb.client.write_to_file(f"DIVIDE: {ratio_stock[1]},stock net: {optional_cash}, new invest:{round(new_cash_invest_stock,2)},ratio from start: {round(optional_cash/glb.my_available_money_dollar_start,2)}")
                stock_that_got_divide.append(ratio_stock[1])
                # if glb.demo_portfolio_treads[ratio_stock[1]].flag_enter_status and glb.demo_portfolio_treads[ratio_stock[1]].amount_limit_flag and not glb.my_portfolio[ratio_stock[1]].flag_enter_status:
                # # if glb.demo_portfolio_treads[ratio_stock[1]].flag_enter_status and glb.demo_portfolio_treads[ratio_stock[1]].amount_limit_flag:
                #     glb.my_portfolio[ratio_stock[1]].real_buy_shears(price,time_stamp,glb.demo_portfolio_treads[ratio_stock[1]].real_volume_list[-1][time_stamp])

        else:
            optional_cash = glb.my_portfolio[ratio_stock[1]].total_stock_net_value
            glb.client.write_to_file(f"DIVIDE: {ratio_stock[1]},stock net: {optional_cash}, new invest:0 ,ratio from start: {round(optional_cash / glb.my_available_money_dollar_start, 2)}")
    with glb.key_lock_available_money:
        spear_money = glb.my_available_money_dollar-500
    if spear_money>1 and len(stock_that_got_divide)>0 :
        partioal_money = spear_money/len(stock_that_got_divide)
        glb.client.write_to_file(f"DIVIDE: left {spear_money} cash ,and divide it between {len(stock_that_got_divide)} stocks :{partioal_money} ")
        for stock in stock_that_got_divide:
            update_my_portfolio_files(stock, partioal_money, 0)
        with glb.key_lock_available_money:
            glb.my_available_money_dollar -= spear_money


def simulate_day_trading_local_data(stock_object: glb.Demo_Stock_Object):
    simulate_trading_local_data(stock_object)

    stock_object.barrier.wait()  ###########
    # if stock_object.stock_name == glb.job_by_one_thread:
    #     glb.not_first_day = True
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


def simulate_trading_local_data(stock_object: glb.Demo_Stock_Object):
    avg_list_day = []
    stock_object.real_avg_list = []
    volume_list = stock_object.real_volume_list
    last_volume_list = sorted(volume_list)
    lower_half_volume = last_volume_list[:len(last_volume_list) // 2]
    lower_half_volume = np.array(lower_half_volume) / len(lower_half_volume)
    stock_object.avg_volume = lower_half_volume.sum()
    if glb.dbg_local:
        stock_log_price_times_path = glb.PATH_RESULTS.replace('debug','day_trade')+f"{stock_object.stock_name}/log_price_times" + stock_object.stock_name + '.csv'
        with open(stock_log_price_times_path, "r") as file:
            import csv
            reader = csv.reader(file)
            lists = []
            for row in reader:
                lists.append(row)
            stock_object.real_avg_list_times= copy.deepcopy(lists[0])#'dates'
            avg_list_day = [float(val) for val in lists[1]]#'avg'
            stock_object.real_avg_list = copy.deepcopy(avg_list_day)
            # volume_list =[float(val) for val in lists[2]]#'volume'
            stock_object.current_price = avg_list_day[0]
    else:
        with glb.condition_clock_start:
            if not glb.clock_start:
                glb.condition_clock_start.wait()
    stock_object.gaps_list.append(0)
    # stock_object.break_point_to_divide_the_real_money_between_stocks(stock_object.counter)
    # with glb.condition_one_minute:
    #     glb.condition_one_minute.wait()
    stock_object.start_price = stock_object.current_price
    minimum_price = stock_object.current_price
    current_time = dt.datetime.now()

    #### this will be change to 1 min delay and check if the market is closed(1 min before) ###
    # try:
    while current_time < glb.time_end_of_trading_day:
        #### request market data ###
        # price = stock_object.current_price
        # avg_list_day.append(price)
        # stock_object.real_avg_list.append(price)
        if not glb.dbg_local:
            print(f"{stock_object.stock_name} start round at time  {current_time.hour} : {current_time.minute} : {current_time.second}")
            while True:
                price, status = stock_object.get_last_price("LAST_PRICE")  # real: get stock last price
                # price, status = stock_object.get_last_price("CLOSE")  # real: get stock last price
                if stock_object.counter == 0:
                    stock_object.start_price = price
                    stock_object.relative_start_price = price
                    minimum_price = price
                if 'SUCCESS' in status:
                    avg_list_day.append(price)
                    glb.my_portfolio[stock_object.stock_name].last_price = price
                    break
        else:
            print(f"{stock_object.stock_name} start round counter  {stock_object.counter}")
            price = avg_list_day[stock_object.counter]
        # if stock_object.counter % 10 == 0:
        #     last_volume_list = sorted(volume_list)
        #     lower_half_volume = last_volume_list[:len(last_volume_list)//2]
        #     lower_half_volume = np.array(lower_half_volume)/len(lower_half_volume)
        #     stock_object.avg_volume = lower_half_volume.sum()


        #### i think this part should be in the end of the minute ####
        # stock_object.break_point_to_divide_the_real_money_between_stocks(stock_object.counter)

        if stock_object.accumulated_amount > stock_object.max_amount:
            stock_object.max_amount = stock_object.accumulated_amount
        if price < minimum_price:
            minimum_price = price
            if 100*(stock_object.start_price-price)/stock_object.start_price > glb.limit_presantage:
                stock_object.start_accumulated_amount = stock_object.accumulated_amount
                stock_object.amount_limit_num = glb.limit_presantage
                stock_object.relative_start_price = price

        # stock_object.analyze_the_histogram_and_set_the_next_action()
        if not glb.dbg_local:
            stock_interval_change = round((float(price-avg_list_day[-2])),2) if stock_object.counter > 0 else 0
        else:
            stock_interval_change = round((float(price-avg_list_day[stock_object.counter-1])),2) if stock_object.counter > 0 else 0

        #### this part need to change to order requests ####
        stock_object.simulate_the_next_trade(price,stock_interval_change,stock_object.counter)
        stock_object.Safe_Limit_condition_stock_trade(price,stock_object.counter)

        #### this will help me devide the money with the potntial stocks ####
        stock_object.accumulated_amount_percentage_day = 100 * stock_object.accumulated_amount_limit / stock_object.start_price

        #### collect statistic data ####
        stock_object.amount_list.append(stock_object.accumulated_amount)
        stock_object.amount_list_no_gap.append(stock_object.accumulated_amount_no_gap)
        stock_object.amount_limit.append(stock_object.accumulated_amount_limit)

        if not glb.dbg_local:
            current_time = dt.datetime.now()
            with glb.condition_clock_start:
                diff_time = glb.time_next_minute_break - current_time
                if diff_time.days == 0 and diff_time.seconds < 60 and current_time < glb.time_end_of_trading_day:
                    glb.condition_clock_start.wait()
            # diff_time = glb.time_next_minute_break - current_time
            # diff_time_end = glb.time_end_of_trading_day - current_time
            # secound_wait = min(diff_time.seconds,diff_time_end.seconds)
            # if diff_time.days == 0 and diff_time.seconds < 60 and current_time < glb.time_end_of_trading_day:
            #     time.sleep(secound_wait+diff_time.microseconds/1e6)
                # with glb.condition_one_minute:
                #     glb.condition_one_minute.wait()
            # else:
            #     time.sleep(3)
            current_time = dt.datetime.now()
        else:
            if stock_object.counter == (len(avg_list_day)-1):
                current_time = glb.time_end_of_trading_day
        stock_object.counter += 1
        if glb.flag_time_of_last_five_min:
            if glb.my_portfolio[stock_object.stock_name].shears == 0:
                break
    # except:
    #     x=1

    stock_object.flag_first_day = False
    #### in case i would like to hold the stock during the night(need to cancel the section before)
    # if not stock_object.flag_enter_status and not stock_object.flag_last_day:
    #     stock_object.buy_shears(-1, int(stock_object.available_money / stock_object.real_avg_list[-1][-1]),'avg')  # closeX2
    #     #if not stock_object.amount_limit_flag:
    #     stock_object.sell_phase = True
    #     # stock_object.amount_list[-1] -= max(1.0,stock_object.shears*0.005)
    #     stock_object.amount_list[-1] -= 0.005




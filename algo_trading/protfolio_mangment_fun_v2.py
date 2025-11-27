import os
import time
import copy
import numpy as np

import ibkr_connection
# import yfinance as yf
from algo_trade_ofir_function_on_stock_client_v2 import *
from ibkr_connection import *
import globals_v2 as glb
import datetime as dt

def fill_stock_1D_previous_data(stock):
    stock_data = {'open':[],'close':[],'avg':[],'volume':[],'dates':[],'last_price':float(0)}
    with glb.key_lock_stocks_data:
        glb.stocks_data.update({stock:stock_data})
    glb.day_barrier.wait()
    # yesterday = dt.datetime.now() - dt.timedelta(days=10)
    # end_date_time = yesterday.strftime("%Y%m%d 23:59:59")  # End time set to end of the previous day

    sub_thread = threading.Thread(target=glb.client.collect_historical_data, args=(stock,))
    sub_thread.start()
    sub_thread.join()
    # glb.demo_portfolio_treads[stock].real_avg_list = copy.deepcopy(glb.stocks_data[stock]['avg'])
    # glb.demo_portfolio_treads[stock].real_close_list = copy.deepcopy(glb.stocks_data[stock]['close'])
    # glb.demo_portfolio_treads[stock].real_open_list = copy.deepcopy(glb.stocks_data[stock]['open'])
    glb.demo_portfolio_treads[stock].current_price = glb.stocks_data[stock]['avg'][-1]
    glb.demo_portfolio_treads[stock].real_volume_list = copy.deepcopy(glb.stocks_data[stock]['volume'])
    last_volume_list = sorted(glb.demo_portfolio_treads[stock].real_volume_list)
    lower_half_volume = last_volume_list[:len(last_volume_list) // 2]
    glb.demo_portfolio_treads[stock].avg_volume = sum(lower_half_volume) / len(lower_half_volume)

def fill_stocks_data(stocks_list):
    threads = []
    for idx, stock in enumerate(stocks_list):
        threads.append(threading.Thread(target=glb.client.add_stock_to_stock_list, args=(stock,)))
        threads[idx].start()
    for idx, stock in enumerate(stocks_list):
        threads[idx].join()
    threads =[]
    for idx, stock in enumerate(stocks_list):
        threads.append(threading.Thread(target=fill_stock_1D_previous_data, args=(stock,)))
        threads[idx].start()
    for idx, stock in enumerate(stocks_list):
        threads[idx].join()
def fill_portfolio_dict(stocks_list):
    barrier = threading.Barrier(len(stocks_list))
    glb.day_barrier = threading.Barrier(len(stocks_list))
    for stock in stocks_list:
        glb.demo_portfolio_treads.update({stock: glb.Demo_Stock_Object(stock, barrier, glb.my_init_demo_available_money_dollar)})
        update_my_portfolio_files(stock,0,0)
def write_to_real_log_info():
    import  csv
    import pandas as pd
    if not os.path.isdir(glb.PATH_RESULTS):
        os.mkdir(glb.PATH_RESULTS)
    all_results_path = glb.PATH_RESULTS + '/ALL_RESULTS'
    if not os.path.isdir(all_results_path):
        os.mkdir(all_results_path)
    real_log_path = all_results_path + '/real_log.txt'
    with glb.key_lock_stocks_data:
        with open(real_log_path, 'w') as f:
            for line in glb.real_logs:
                f.write(line + '\n')
            f.write(f"init money:{glb.my_available_money_dollar_start}, end money: {glb.my_available_money_dollar} ,P&L {round(glb.my_available_money_dollar - glb.my_available_money_dollar_start,3)} | {round(100 * (glb.my_available_money_dollar - glb.my_available_money_dollar_start) / glb.my_available_money_dollar_start,3)}% ")
            print(glb.my_available_money_dollar_start, glb.my_available_money_dollar, glb.my_available_money_dollar - glb.my_available_money_dollar_start, 100 * (glb.my_available_money_dollar - glb.my_available_money_dollar_start) / glb.my_available_money_dollar_start, '%')
    real_log_path = all_results_path + '/real_log.xlsx'
    for row in glb.real_logs_csv:
        glb.stock_that_been_used[row[2]].append(row)
    writer = pd.ExcelWriter(real_log_path, engine='xlsxwriter',mode='w')
    head_lines = ['Dates', 'min_num','stock_name','action', 'transaction_price','wanted_price','diff_prices','volume', 'shears_transaction_amount', 'commission','stock_net_value' ,'cash']
    main_sheet = [head_lines]+glb.real_logs_csv
    df = pd.DataFrame(main_sheet)
    df.to_excel(writer, sheet_name='Main', index=False)
    for stock in glb.stock_that_been_used:
        glb.stock_that_been_used[stock] =[head_lines]+glb.stock_that_been_used[stock]
        df = pd.DataFrame(glb.stock_that_been_used[stock])
        df.to_excel(writer, sheet_name=stock,index=False)
    writer.close()

    if len(glb.demo_portfolio_treads) == 1:
        for stock in glb.demo_portfolio_treads:
            if not os.path.isdir(glb.PATH_RESULTS+ '/' + stock):
                os.mkdir(glb.PATH_RESULTS+ '/' + stock)
            log_path = glb.PATH_RESULTS + '/' + stock + '/' + stock + '_log.xlsx'
            writer = pd.ExcelWriter(log_path, engine='xlsxwriter', mode='w')
            main_sheet = [head_lines] + glb.real_logs_csv
            df = pd.DataFrame(main_sheet)
            df.to_excel(writer, sheet_name=stock, index=False)
            writer.close()

def plotting_stocks_summary(start, end):
    init_money = (glb.my_available_money_dollar_start-500)/len(glb.my_portfolio)
    for stock_name in glb.my_portfolio:
        # glb.my_portfolio[stock_name].real_sell_shears(glb.demo_portfolio_treads[stock_name].real_avg_list[-1],-1,99999999999)#max volume to sell all
        txt = f"stock:{stock_name} init money: {init_money} in the end: {glb.my_portfolio[stock_name].available_money} P&L:{round(100*(glb.my_portfolio[stock_name].available_money-init_money)/init_money,2)}%"
        glb.client.write_to_file(txt)
        glb.my_portfolio[stock_name].return_available_real_cash()
    write_to_real_log_info()
    for stock_object in glb.demo_portfolio_treads:
        # glb.demo_portfolio_treads[stock_object].real_avg_list = glb.demo_portfolio_treads[stock_object].real_avg_list[2:]
        glb.demo_portfolio_treads[stock_object].write_to_log_info()
        glb.demo_portfolio_treads[stock_object].plotting_all_data(start, end)

def checking_if_continue_or_stop():
    file_path = '/Users/ofirdahan/Desktop/interactive brokers/stock_analyzer/paper_trading_data_result/run_status.txt'
    flag = False
    with open(file_path, 'r') as file:
        for line in file:
            if '1' in line:
                glb.time_end_of_trading_day = glb.time_next_minute_break + dt.timedelta(minutes=2)
                glb.time_of_last_five_min = dt.datetime.now()
                flag= True
                break
    if flag:
        with open(file_path, 'w') as f:
            f.write('end')
def create_continue_or_stop_file():
    file_path = '/Users/ofirdahan/Desktop/interactive brokers/stock_analyzer/paper_trading_data_result/run_status.txt'
    with open(file_path, 'w') as f:
        f.write('to stop write the num one.')

def time_clock_update_thread():
    counter = 0
    divide_available_money(counter)
    diff_time = glb.time_start_of_trading_day - dt.datetime.now()
    if diff_time.days == 0:
        time.sleep(diff_time.seconds+diff_time.microseconds/1e6)
    with glb.condition_clock_start:
        current_time = dt.datetime.now()
        if current_time.second>30:
            print(f"clock program will start in {60-current_time.second} sec ")
            time.sleep(60-current_time.second)
        current_time = dt.datetime.now()
        glb.time_of_last_five_min = glb.time_end_of_trading_day - dt.timedelta(minutes=5)
        glb.time_next_minute_break = dt.datetime(current_time.year, current_time.month, current_time.day, current_time.hour, current_time.minute, 0) + dt.timedelta(minutes=1)
        glb.time_next_minute_break_ten_sec_before = glb.time_next_minute_break - dt.timedelta(seconds=8)
        print(f"current time  {current_time.hour} : {current_time.minute} : {current_time.second}")
        print(f"next minut  {glb.time_next_minute_break.hour} : {glb.time_next_minute_break.minute}")
        glb.clock_start = True
        glb.condition_clock_start.notify_all()
    try:
        while current_time < glb.time_end_of_trading_day and glb.client.active:
            diff_time = glb.time_next_minute_break - dt.datetime.now()
            if diff_time.days == 0 and diff_time.seconds < 60:
                time.sleep(diff_time.seconds+diff_time.microseconds/1e6)
            checking_if_continue_or_stop()
            counter += 1
            with glb.condition_clock_start:
                current_time = dt.datetime.now()
                glb.time_next_minute_break = dt.datetime(current_time.year, current_time.month, current_time.day, current_time.hour, current_time.minute, 0) + dt.timedelta(minutes=1)
                glb.time_next_minute_break_ten_sec_before = glb.time_next_minute_break - dt.timedelta(seconds=8)
                if current_time > glb.time_of_last_five_min:
                    glb.flag_time_of_last_five_min = True
                    if current_time >= glb.time_end_of_trading_day:
                        break
            print(f"current time  {current_time.hour} : {current_time.minute} : {current_time.second}")
            print(f"next minut  {glb.time_next_minute_break.hour} : {glb.time_next_minute_break.minute}")
            # if glb.client.active:
            #     sub_thread = threading.Thread(target=divide_available_money, args=(counter,))
            #     sub_thread.start()
            # else:
            #     break
            with glb.condition_clock_start:
                glb.condition_clock_start.notify_all()
        with glb.condition_clock_start:
            glb.condition_clock_start.notify_all()
    except:
        with glb.condition_clock_start:
            glb.condition_clock_start.notify_all()
        # divide_available_money(counter)
    # for i in range(10):
    #     with glb.condition_one_minute:
    #         glb.condition_one_minute.notify_all()
    #     time.sleep(10)

def trade_and_update_portfolio_local_data(stocks_list):
    # import necessary packages
    from dateutil import rrule
    current_time = dt.datetime.now()
    tomorrow = current_time + dt.timedelta(days=1)
    yesterday = current_time - dt.timedelta(days=1)
    glb.time_start_of_trading_day = dt.datetime(current_time.year, current_time.month, current_time.day, 16, 30, 0)

    # glb.time_start_of_trading_day = current_time####

    glb.time_end_of_trading_day = dt.datetime(current_time.year, current_time.month, current_time.day, 23, 0, 0)
    if glb.include_pre_post_mkt:
        glb.time_start_of_trading_day = dt.datetime(current_time.year, current_time.month, current_time.day, 11, 0, 0) if current_time.hour >= 3 else dt.datetime(current_time.year, current_time.month, current_time.day, current_time.hour, current_time.minute, 0)
        glb.time_end_of_trading_day = dt.datetime(current_time.year, current_time.month, current_time.day, 3, 0, 0) if current_time.hour < 3 else dt.datetime(tomorrow.year, tomorrow.month, tomorrow.day, 3, 0, 0)

    glb.time_next_minute_break = glb.time_start_of_trading_day+dt.timedelta(minutes=1)
    glb.time_next_minute_break_ten_sec_before = glb.time_next_minute_break - dt.timedelta(seconds=8)
    time_to_start_prepare = glb.time_start_of_trading_day - dt.timedelta(minutes=3)

    if glb.debug_mode:
        glb.time_end_of_trading_day = current_time + dt.timedelta(minutes=20)
    # dates
    start_date = dt.datetime.today().strftime('%d_%mM_%Y') if current_time.hour>=3 else yesterday.strftime('%d_%mM_%Y')
    end_date = dt.datetime.today().strftime('%d_%mM_%Y') if current_time.hour<3 else tomorrow.strftime('%d_%mM_%Y')
    glb.PATH_RESULTS += f"/Program_runs/{start_date}->{end_date}"
    if not os.path.exists(glb.PATH_RESULTS):
        os.mkdir(glb.PATH_RESULTS)
    if not (glb.dbg_local or glb.include_pre_post_mkt):
        glb.PATH_RESULTS +=f"/day_trade/"
    elif glb.include_pre_post_mkt:
        glb.PATH_RESULTS +=f"/with_pre_post_trade/"
    elif glb.dbg_local:
        glb.PATH_RESULTS +=f"/debug/"

    if not os.path.exists(glb.PATH_RESULTS):
        os.mkdir(glb.PATH_RESULTS)
    ibkr_connection.LOG_FILE_PATH = glb.PATH_RESULTS
    if not glb.dbg_local:
        glb.client = IBClient()
    create_continue_or_stop_file()
    fill_portfolio_dict(stocks_list)
    if not glb.dbg_local:
        fill_stocks_data(stocks_list)
    if os.path.exists(glb.PATH_RESULTS+'/real_log.txt'):
        os.remove(glb.PATH_RESULTS+'/real_log.txt')
    if os.path.exists(glb.PATH_RESULTS+'/real_log.xlsx'):
        os.remove(glb.PATH_RESULTS+'/real_log.xlsx')
    flag = True
    if not glb.dbg_local:
        sub_thread_clock = threading.Thread(target=time_clock_update_thread, args=())
        sub_thread_clock.start()
        current_time = dt.datetime.now()
        if time_to_start_prepare>current_time:
            diff_time = time_to_start_prepare - current_time
            print(f"stocks program will start in {diff_time.seconds} sec")
            time.sleep(diff_time.seconds+diff_time.microseconds/1e6)
        # time.sleep(10)
    for stock_object in glb.demo_portfolio_treads:
        glb.demo_portfolio_treads[stock_object].flag_last_day = True
        glb.demo_portfolio_treads[stock_object].thread_id = threading.Thread(target=simulate_trading_local_data, args=(glb.demo_portfolio_treads[stock_object],))
        if flag:
            glb.job_by_one_thread = stock_object
            flag = False
        glb.demo_portfolio_treads[stock_object].thread_id.start()
    for stock_object in glb.demo_portfolio_treads:
        glb.demo_portfolio_treads[stock_object].thread_id.join()

    # exit_and_collect_money(-1)
    plotting_stocks_summary(start_date, end_date)
    print(glb.my_available_money_dollar_start, glb.my_available_money_dollar, glb.my_available_money_dollar - glb.my_available_money_dollar_start ,100 * (glb.my_available_money_dollar - glb.my_available_money_dollar_start) / glb.my_available_money_dollar_start,'%')
    glb.time_end_of_trading_day = dt.datetime.now()
    if not glb.dbg_local:
        sub_thread_clock.join()
        glb.client.disconnection()

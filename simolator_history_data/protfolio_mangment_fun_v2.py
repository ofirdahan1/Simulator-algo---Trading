import os
import time

import numpy as np
# import yfinance as yf
from algo_trade_ofir_function_on_stock_client_v2 import *
import globals_v2 as glb

def fill_stocks_data(stock,year_month_list,start,end):
    stock_data = {'open':[],'close':[],'high':[],'low':[],'avg':[],'volume':[],'days': 0,'dates':[],'real_close':[]}
    if glb.dbg_on_real_data:
        # stock_path = f"/Users/ofirdahan/Desktop/interactive brokers/stock_analyzer/paper_trading_data_result/Program_runs/30_09M_2024->01_10M_2024/day_trade/{stock}/"
        stock_path = glb.local_path_file+f"{stock}/"
        stock_log_price_times_path = stock_path + 'log_price_times' + stock + '.csv'
        with open(stock_log_price_times_path ,"r") as file:
            import csv
            reader = csv.reader(file)
            counter =0
            tags = ['dates','avg','volume']
            for row in reader:
                if counter==0:
                    stock_data[tags[counter]].append(row)
                else:
                    stock_data[tags[counter]].append([float(val) for val in row])
                counter+=1
        stock_data['days'] = 1
    else:
        flag_add = False
        for year_month in year_month_list:
            file_name = f"{stock}_{year_month}.txt"
            txt = ''
            with open(glb.PATH_STOCKS_DATA + f"{stock}/" + file_name, 'r') as f_input:
                txt = f_input.read()
            rows = txt.split('\n')
            for row in reversed(rows):
                if end in row or 'timestamp' in row:
                    break
                if (flag_add or start in row) and ':' in row:
                    flag_add = True
                    row_data = row.split(',')
                    date = row_data[0].split(' ')[0]
                    if len(stock_data['dates']) == 0 or date not in stock_data['dates'][-1]:
                        stock_data['days'] += 1
                        stock_data['open'].append([])
                        stock_data['close'].append([])
                        stock_data['real_close'].append([])
                        stock_data['high'].append([])
                        stock_data['low'].append([])
                        stock_data['volume'].append([])
                        stock_data['avg'].append([])
                        stock_data['dates'].append(date)
                        day_num = stock_data['days']-1
                        gap = 0 if day_num == 0 else ( (float(row_data[4]) - stock_data['close'][day_num - 1][-1]))
                        # gap = 0
                    stock_data['open'][day_num].append(float(row_data[1])-gap)
                    stock_data['close'][day_num].append(float(row_data[4])-gap)
                    stock_data['real_close'][day_num].append(float(row_data[4]))
                    stock_data['high'][day_num].append(float(row_data[2])-gap)
                    stock_data['low'][day_num].append(float(row_data[3])-gap)
                    stock_data['volume'][day_num].append(float(row_data[5]))
                    # stock_data['avg'][day_num].append(np.round(float(row_data[4]), 3))
                    stock_data['avg'][day_num].append(np.round((float(row_data[1]) + float(row_data[4])) / 2, 3))
                    # stock_data['avg'][day_num].append(np.round((float(row_data[2]) + float(row_data[3])) / 2, 3))
    # print("gap:",gap)
    glb.stocks_data.update({stock:stock_data})

def fill_portfolio_dict(stocks_list):
    barrier = threading.Barrier(len(stocks_list))
    glb.day_barrier = threading.Barrier(len(stocks_list))
    for stock in stocks_list:
        glb.demo_portfolio_treads.update({stock: Demo_Stock_Object(stock, barrier, glb.my_init_demo_available_money_dollar)})
def write_to_real_log_info():
    import  csv
    import pandas as pd
    if not os.path.isdir(glb.PATH_RESULTS):
        os.mkdir(glb.PATH_RESULTS)
    all_results_path = glb.PATH_RESULTS + '/ALL_RESULTS'
    if not os.path.isdir(all_results_path):
        os.mkdir(all_results_path)
    real_log_path = all_results_path + '/real_log_hist.txt'
    with key_lock:
        with open(real_log_path, 'w') as f:
            for line in glb.real_logs:
                f.write(line + '\n')
    real_log_path = all_results_path + '/real_log_hist.xlsx'
    for row in glb.real_logs_csv:
        glb.stock_that_been_used[row[2]].append(row)
    writer = pd.ExcelWriter(real_log_path, engine='xlsxwriter',mode='w')
    head_lines = ['Dates', 'min_num','stock_name','action', 'stock_price','volume', 'shears_transaction_amount', 'commission','stock_net_value' ,'cash']
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
            head_lines = ['Dates', 'min_num', 'stock_name', 'action', 'stock_price', 'volume', 'shears_transaction_amount', 'commission', 'stock_net_value', 'cash']
            main_sheet = [head_lines] + glb.real_logs_csv
            df = pd.DataFrame(main_sheet)
            df.to_excel(writer, sheet_name=stock, index=False)
            writer.close()

def plotting_stocks_summary(start, end):
    init_money = (glb.my_available_money_dollar_start-500)/len(glb.demo_portfolio_treads)

    for stock_name in glb.my_portfolio:
        glb.my_portfolio[stock_name].real_sell_shears(glb.demo_portfolio_treads[stock_name].real_avg_list[-1][-1],-1,99999999999)#max volume to sell all
        txt = f"stock:{stock_name} init money: {init_money} in the end: {glb.my_portfolio[stock_name].available_money} P&L:{round(100 * (glb.my_portfolio[stock_name].available_money - init_money) / init_money, 2)}%"
        print(txt)
        glb.my_portfolio[stock_name].return_available_real_cash()
    if not glb.statistic_flag:
        write_to_real_log_info()
        for stock_object in glb.demo_portfolio_treads:
            # glb.demo_portfolio_treads[stock_object].real_avg_list = glb.demo_portfolio_treads[stock_object].real_avg_list[2:]
            glb.demo_portfolio_treads[stock_object].write_to_log_info()
            glb.demo_portfolio_treads[stock_object].plotting_all_data(start, end)



# def trade_and_update_portfolio(stocks_list, end, wanted_num_days, interval):
#     start, end = get_dates_for_working_days(end, wanted_num_days)
#     start_date = [int(num) for num in start.split('-')]
#     start_week_day = datetime.date(start_date[0], start_date[1], start_date[2]).weekday()
#     start_date_timestamp = time.mktime(datetime.datetime.strptime(start, "%Y-%m-%d").timetuple())
#     end_date_timestamp = time.mktime(datetime.datetime.strptime(end, "%Y-%m-%d").timetuple())
#     fill_portfolio_dict(stocks_list)
#     # divide_available_money()
#     if glb.data_request == 'YHAOO':
#         for stock_object in glb.demo_portfolio_treads:
#             glb.demo_portfolio_treads[stock_object].thread_id = threading.Thread(target=get_first_2d_for_training, args=(glb.demo_portfolio_treads[stock_object], start, interval))
#             glb.demo_portfolio_treads[stock_object].thread_id.start()
#         for stock_object in glb.demo_portfolio_treads:
#             glb.demo_portfolio_treads[stock_object].thread_id.join()
#             if not glb.demo_portfolio_treads[stock_object].thread_response:
#                 raise ValueError(f"didn't get the first 2 days for {stock_object}")
#     elif glb.data_request == 'LOCAL':
#         for stock_object in glb.demo_portfolio_treads:
#             glb.demo_portfolio_treads[stock_object].thread_id = threading.Thread(target=get_first_2d_for_training_from_local, args=(glb.demo_portfolio_treads[stock_object], start))
#             glb.demo_portfolio_treads[stock_object].thread_id.start()
#         for stock_object in glb.demo_portfolio_treads:
#             glb.demo_portfolio_treads[stock_object].thread_id.join()
#             if not glb.demo_portfolio_treads[stock_object].thread_response:
#                 raise ValueError(f"didn't get the first 2 days for {stock_object}")
#
#     if os.path.exists(glb.PATH_RESULTS+'/real_log.txt'):
#         os.remove(glb.PATH_RESULTS+'/real_log.txt')
#     while (end_date_timestamp - start_date_timestamp) > 0:
#         if start_week_day not in [5, 6]:
#             test_algo_date_end = datetime.datetime.fromtimestamp(start_date_timestamp + glb.day_timestamp).isoformat().split('T')[0]
#             flag = True
#             for stock_object in glb.demo_portfolio_treads:
#                 if (end_date_timestamp - start_date_timestamp) == glb.day_timestamp:
#                     glb.demo_portfolio_treads[stock_object].flag_last_day = True
#                 # simulate_day_trading_slope_linear_regression_2(glb.demo_portfolio_treads[stock_object],test_algo_date_end,1,interval)
#                 glb.demo_portfolio_treads[stock_object].thread_id = threading.Thread(target=simulate_day_trading_slope_linear_regression_2,args=(glb.demo_portfolio_treads[stock_object], test_algo_date_end, 1, interval))
#                 if flag:
#                     glb.job_by_one_thread = stock_object
#                     flag = False
#                 glb.demo_portfolio_treads[stock_object].thread_id.start()
#             for stock_object in glb.demo_portfolio_treads:
#                 glb.demo_portfolio_treads[stock_object].thread_id.join()
#         start_date_timestamp += glb.day_timestamp
#         start_week_day = (1 + start_week_day) % 7
#     # exit_and_collect_money(-1)
#     plotting_stocks_summary(start, end)
#     print(glb.my_available_money_dollar_start, glb.my_available_money_dollar,100 * (glb.my_available_money_dollar - glb.my_available_money_dollar_start) / glb.my_available_money_dollar_start,'%')
#
def trade_and_update_portfolio_local_data(stocks_list, start,end):
    # import necessary packages
    from datetime import datetime
    from dateutil import rrule

    # dates
    start_date = datetime(int(start.split('-')[0]), int(start.split('-')[1]), 1)
    end_date = datetime(int(end.split('-')[0]), int(end.split('-')[1]), 1)
    if glb.dbg_on_real_data:
        test_month_dates = 0
    else:
        test_month_dates = [(str(dt.year)+'_'+str(dt.month).zfill(2)) for dt in rrule.rrule(rrule.MONTHLY, dtstart=start_date, until=end_date)]
        if len(test_month_dates) == 0:
            raise RuntimeError(f"invalid dates start {start} end {end}")
        for stock in stocks_list:
            for date in test_month_dates:
                year =date.split('_')[0]
                month =date.split('_')[1]
                file_name = f"{stock}_{year}_{month}.txt"
                if not os.path.exists(glb.PATH_STOCKS_DATA + f"{stock}/" + file_name):
                    raise RuntimeError(f"stock data of {stock} in date of {year}-{month} not founded")

    for stock in stocks_list:
        fill_stocks_data(stock,test_month_dates,start,end)
    fill_portfolio_dict(stocks_list)
    if os.path.exists(glb.PATH_RESULTS+'/real_log_hist.txt'):
        os.remove(glb.PATH_RESULTS+'/real_log_hist.txt')
    if os.path.exists(glb.PATH_RESULTS+'/real_log_hist.xlsx'):
        os.remove(glb.PATH_RESULTS+'/real_log_hist.xlsx')
    total_days_number = glb.stocks_data[stocks_list[0]]['days']
    if glb.dbg_on_real_data:
        glb.not_first_day = True
    for day_num in range(total_days_number):
        flag = True
        for stock_object in glb.demo_portfolio_treads:
            if day_num == (total_days_number-1):
                glb.demo_portfolio_treads[stock_object].flag_last_day = True
            # simulate_day_trading_slope_linear_regression_2(glb.demo_portfolio_treads[stock_object],test_algo_date_end,1,interval)
            glb.demo_portfolio_treads[stock_object].thread_id = threading.Thread(target=simulate_day_trading_local_data, args=(glb.demo_portfolio_treads[stock_object],day_num))
            if flag:
                glb.job_by_one_thread = stock_object
                flag = False
            glb.demo_portfolio_treads[stock_object].thread_id.start()
        for stock_object in glb.demo_portfolio_treads:
            glb.demo_portfolio_treads[stock_object].thread_id.join()

    # exit_and_collect_money(-1)
    plotting_stocks_summary(start, end)
    if glb.statistic_flag:
        pnl = round(100 * (glb.my_available_money_dollar - glb.my_available_money_dollar_start) / glb.my_available_money_dollar_start,2)
        txt = f"P&L: {pnl} ,glb.limit_presantage: {glb.limit_presantage} ,glb.diff_p: {glb.diff_p} ,glb.factor:{glb.factor}"
        glb.statistic_list.append([pnl, txt])
        print(txt)
    else:
        print(glb.my_available_money_dollar_start, glb.my_available_money_dollar, glb.my_available_money_dollar - glb.my_available_money_dollar_start, 100 * (glb.my_available_money_dollar - glb.my_available_money_dollar_start) / glb.my_available_money_dollar_start, '%')

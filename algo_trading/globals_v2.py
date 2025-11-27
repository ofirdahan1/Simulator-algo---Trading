import threading
import datetime as dt
import os
import time
import matplotlib.pyplot as plt
import numpy as np

clock_start= False
night_mode = False
include_pre_post_mkt = True
debug_mode = False
dbg_local =False

job_by_one_thread = ''
my_available_money_dollar_start = 1000000
ratio_trade_in_volume_minute = 0.1
limit_presantage=5
key_lock_available_money = threading.Lock()
key_lock_times = threading.Lock()
my_available_money_dollar = my_available_money_dollar_start
not_first_day = True
current_date = ''
demo_portfolio_treads = {}
demo_portfolio_treads_Limit = {}
my_portfolio = {}
stock_that_been_used = {}
my_init_demo_available_money_dollar = 2e5
day_timestamp = 60 * 60 * 24
flag_first_day = True
counter = 0
real_logs = list()
real_logs_csv = list()
day_barrier = threading.Barrier(0)
flag_money_divide = True
flag_time_of_last_five_min = False
time_next_minute_break = 0
time_next_minute_break_ten_sec_before = 0
time_of_last_five_min = 0
time_end_of_trading_day = 0
time_start_of_trading_day = 0
slop_d_num_neg_flag = -0.002
slop_d_num_pos_flag = 0
slop_num_pos_flag = 0
PATH_RESULTS = '/Users/ofirdahan/Desktop/interactive brokers/stock_analyzer/paper_trading_data_result'
PATH_STOCKS_DATA = '/Users/ofirdahan/Desktop/interactive brokers/stock_data/'
stocks_data = {}
key_lock_stocks_data = threading.Lock()
data_request = 'LOCAL'
condition_one_minute = threading.Condition()
condition_clock_start = threading.Condition()

request_stream_data_collection = False
client = None
class Real_Stock_actions:
    Buy = 0
    Sell = 1
    Return_Available_cash = 2
    Collect_divide_again = 3
SA =Real_Stock_actions()

class Stock_Object():
    def __init__(self, stock_name, barrier, init_money):

        self.stock_name = stock_name
        self.thread_id = None
        self.thread_response = None
        self.barrier = barrier
        self.buy_phase = True
        self.sell_phase = False
        self.flag_enter_status = False
        self.shears = 0
        self.accumulated_amount = 0
        self.accumulated_amount_percentage_day = 0
        self.start_accumulated_amount = -0.008
        self.available_money = init_money
        self.key_lock_available_money = threading.Lock()
        self.init_money = init_money
        self.last_price = 0
        self.diff_from_wanted_buy_sell = []


class Real_Stock_Object(Stock_Object):

    def __init__(self, stock_name, barrier, init_money):
        super().__init__(stock_name, barrier,init_money)
        self.real_logs = list()
        self.total_stock_net_value = init_money
        self.flag_invest_in_this_stock = False

    def real_sell_shears(self, price,time_stamp,volume,command_timeout:int=0):
        global time_next_minute_break_ten_sec_before
        global client
        # shears_trade_action = int(min(volume * ratio_trade_in_volume_minute, self.shears))
        shears_trade_action = self.shears
        if shears_trade_action > 0:#real:sell
            if command_timeout == 0:
                diff_time = time_next_minute_break_ten_sec_before - dt.datetime.now()
                if diff_time.days == 0 and diff_time.seconds < 60:
                    sub_thread = threading.Thread(target=client.try_buy_sell, args=(self.stock_name, 'SELL', shears_trade_action, diff_time.seconds,))
                    sub_thread.start()
                    sub_thread.join(timeout=diff_time.seconds)
            else:
                sub_thread = threading.Thread(target=client.try_buy_sell, args=(self.stock_name, 'SELL', shears_trade_action, command_timeout,))
                sub_thread.start()

    def real_buy_shears(self, price,time_stamp,volume,command_timeout:int=0):
        global demo_portfolio_treads
        global time_next_minute_break_ten_sec_before
        global client
        if self.available_money > 0 and self.shears == 0: #and demo_portfolio_treads[self.stock_name].avg_volume/price >100
        # if self.available_money > 0:
            buying_power = max(0,min(self.available_money/price,demo_portfolio_treads[self.stock_name].avg_volume-self.shears))*price
            # buying_power = (200*price + 20) if self.shears == 0 else 0
            predict_trade_commission = round(max(1.0, 0.007 * buying_power / price), 3)
            new_shears = max(int((buying_power - predict_trade_commission) / price), 0) #real:buy
            # predict_trade_commission = round(max(1.0, self.available_money * 0.007 / price), 3)
            # new_shears = max(int((self.available_money - predict_trade_commission - 10) / price), 0)
            if new_shears*price*0.0004 > predict_trade_commission*2:
                if command_timeout == 0:
                    diff_time = time_next_minute_break_ten_sec_before - dt.datetime.now()
                    if diff_time.days == 0 and diff_time.seconds < 60:
                        sub_thread = threading.Thread(target= client.try_buy_sell, args=(self.stock_name,'BUY',new_shears,diff_time.seconds,))
                        sub_thread.start()
                        sub_thread.join(timeout=diff_time.seconds)

                        # self.shears += new_shears
                        # commission = max(1.0, new_shears * 0.007)
                        # self.available_money = round(self.available_money - new_shears * price - commission, 3)
                        # self.total_stock_net_value = self.available_money + self.shears * price
                        # if self.shears > 0:
                        #     self.flag_enter_status = True
                        # self.store_to_logs_info('BUY', time_stamp,price,new_shears,commission)
                else:
                    sub_thread = threading.Thread(target=client.try_buy_sell, args=(self.stock_name, 'BUY', new_shears, command_timeout,))
                    sub_thread.start()

    def return_available_real_cash(self):
        global key_lock_available_money
        global my_available_money_dollar
        if self.available_money > 0:
            with key_lock_available_money:
                my_available_money_dollar += self.available_money
            self.available_money = 0

    def store_to_logs_info(self,action,time_stamp,price,shears,commission):
        global key_lock_available_money
        global real_logs
        global real_logs_csv
        global current_date
        global demo_portfolio_treads
        global my_available_money_dollar
        with key_lock_available_money:
            volume = -1 if self.stock_name not in demo_portfolio_treads else demo_portfolio_treads[self.stock_name].real_volume_list[-1]
            if 'BUY' in action or 'BOT' in action:
                real_logs.append(time_stamp+' '+self.stock_name+' time stamp:'+str(demo_portfolio_treads[self.stock_name].counter)+' action:'+action+' price:'+str(price)+' shears:'+str(shears) + ' commission:'+str(commission)+' proff:'+"%.2f" %(my_available_money_dollar)) #"%.2f" %(100*(self.available_money+self.shears*price-self.init_money)/self.init_money
                # real_logs_csv.append([current_date, str(time_stamp), self.stock_name, action, str(price),str(demo_portfolio_treads[self.stock_name].real_volume_list[-1][time_stamp]), str(shears),commission,"%.2f" %(self.total_stock_net_value), "%.2f" %(my_available_money_dollar)])
                real_logs_csv.append([time_stamp, demo_portfolio_treads[self.stock_name].counter, self.stock_name, action, price,self.last_price,self.last_price-price,volume, shears,commission,(self.total_stock_net_value),(my_available_money_dollar)])
            else:
                real_logs.append(time_stamp+' '+self.stock_name+' time stamp:'+str(demo_portfolio_treads[self.stock_name].counter)+' action:'+action+' price:'+str(price)+' shears:'+str(shears) + ' commission:'+str(commission)+' proff:'+"%.2f" %(my_available_money_dollar))
                # real_logs_csv.append([current_date,str(time_stamp),self.stock_name,action,str(price),str(demo_portfolio_treads[self.stock_name].real_volume_list[-1][time_stamp]),str(-1*shears),commission,"%.2f" %(self.total_stock_net_value),"%.2f" %(my_available_money_dollar)])
                real_logs_csv.append([time_stamp, demo_portfolio_treads[self.stock_name].counter, self.stock_name, action, price,self.last_price,price-self.last_price,volume, -1*shears,commission,(self.total_stock_net_value),(my_available_money_dollar)])

    def write_to_log_info(self):
        global PATH_RESULTS
        global key_lock_available_money
        import csv
        if not os.path.isdir(PATH_RESULTS):
            os.mkdir(PATH_RESULTS)
        real_log_path = PATH_RESULTS+'/real_log.txt'
        with key_lock_available_money:
            with open(real_log_path, 'a') as f:
                for line in self.real_logs:
                    f.write(line + '\n')


class Demo_Stock_Object(Stock_Object):

    def __init__(self, stock_name, barrier, init_money):
        super().__init__(stock_name, barrier,init_money)
        self.minutes_per_day = list()
        self.date = ''
        self.flag_enter_status_rec = False
        self.exit_flag = False
        self.flag_first_day = True
        self.flag_last_day = False
        self.is_this_potential_stock = False
        self.flag_amount_list_rec = True
        self.accumulated_amount_no_gap = 0
        self.accumulated_amount_limit = 0
        self.avg_volume=0
        self.max_amount = 0
        self.min_per_day = 0
        self.start_price = 0
        self.relative_start_price = 0
        self.limit_price = 0
        self.current_price = 0
        self.counter = 0
        self.gaps_list = list()
        self.amount_list = list()
        self.amount_list_no_gap = list()
        self.amount_limit = list()
        self.amount_limit_flag = True
        self.amount_limit_num = 0
        self.limit_points_buy_sell = {"BUY":[],"SELL":[]}
        self.avg_list_no_gap = list()
        self.real_avg_list = list()
        self.real_avg_list_times = list()
        self.real_open_list = list()
        self.real_close_list = list()
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
    def get_last_price(self,label):
        global client
        global limit_presantage
        sub_thread = threading.Thread(target=client.req_update_stock_data, args=(self.stock_name,label,))
        sub_thread.start()
        sub_thread.join()
        status = 'FAIL'
        new_label_val = 0
        for i in range(10):
            if label in client.stocks_data[self.stock_name].Data:
            # if 'CLOSE' in client.stocks_data[self.stock_name].Data:
                sub_thread = threading.Thread(target=client.cancel_mkt_data, args=(self.stock_name,))
                sub_thread.start()
                sub_thread.join()
                new_label_val = client.stocks_data[self.stock_name].Data[label]
                # last_price = client.stocks_data[self.stock_name].Data['CLOSE']
                if 'LAST_PRICE' in label:
                    self.current_price = new_label_val
                    self.real_avg_list.append(new_label_val)
                    time_txt = dt.datetime.today().strftime('%Y-%m-%d %H:%M:%S').split(' ')[1]
                    self.real_avg_list_times.append(time_txt)
                client.write_to_file(f"{self.stock_name}, lable {label} new val:{new_label_val} ,sell under: {self.limit_price} increase after: {self.limit_price*(1+limit_presantage/100)}")
                status ='SUCCESS'
                break
            time.sleep(1)
        return new_label_val,status
    def data_for_action_trade(self, time_stamp, action, market_time_condition, shears_request):
        if 'open' in market_time_condition:
            price = self.real_open_list[-1]
        elif 'close' in market_time_condition:
            price = self.real_close_list[-1]
        else:
            price = self.real_avg_list[-1]
        if 'buy' in action:
            predict_trade_commission = round(max(1.0, self.available_money * 0.007 / price), 3)
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
            self.available_money = round(self.available_money + shears_num_sell * price - max(1.0, shears_num_sell * 0.007),3)

            self.store_to_logs_info('SELL', time_stamp,price,shears_num_sell)

        # self.sell_phase = False


    def buy_shears(self, time_stamp, shears_num_buy, market_time_condition):
        shears_num_buy, price = self.data_for_action_trade(time_stamp, 'buy', market_time_condition, shears_num_buy)
        # if 0 == self.shears and shears_num_buy > 0:
        #     self.flag_enter_status = True
        self.shears += shears_num_buy
        if shears_num_buy>0:
            self.store_to_logs_info('BUY', time_stamp,price,shears_num_buy)
            self.available_money = round(self.available_money - shears_num_buy * price - max(1.0, shears_num_buy * 0.007),3)
        # self.buy_phase = False
        # self.check_real_invest_in_the_stock_and_action(SA.Buy, price, time_stamp)
        # if self.amount_limit_flag:

    def check_real_invest_in_the_stock_and_action(self, action, price=0,time_stamp=0):
        global my_portfolio
        global SA
        global flag_time_of_last_five_min
        global dbg_local
        # return
        if not dbg_local:
            if my_portfolio[self.stock_name].flag_invest_in_this_stock:
                if action in [SA.Buy, SA.Sell] and flag_time_of_last_five_min:
                    action = SA.Sell
                if action is SA.Buy : #and not my_portfolio[self.stock_name].flag_enter_status
                    my_portfolio[self.stock_name].real_buy_shears(price,time_stamp,self.real_volume_list[-1])
                elif action is SA.Sell:#and not my_portfolio[self.stock_name].flag_enter_status
                    my_portfolio[self.stock_name].real_sell_shears(price,time_stamp,self.real_volume_list[-1])
                elif action is SA.Return_Available_cash:
                    if not self.is_this_potential_stock:
                        my_portfolio[self.stock_name].real_sell_shears(price,time_stamp,self.real_volume_list[-1])
                    my_portfolio[self.stock_name].return_available_real_cash()
                elif action is SA.Collect_divide_again:
                    self.is_this_potential_stock = False
                    my_portfolio[self.stock_name].return_available_real_cash()
                my_portfolio[self.stock_name].total_stock_net_value = my_portfolio[self.stock_name].available_money+my_portfolio[self.stock_name].shears*price
    # def break_point_to_divide_the_real_money_between_stocks(self,time_stamp):
    #     if flag_money_divide:
    #         if flag_time_of_last_five_min:
    #             with key_lock_money_divide:
    #                 if flag_money_divide:
    #                     divide_available_money(time_stamp)
    #                     flag_money_divide = False

    def detect_pick_fall(self):
        return False




    def analyze_the_histogram_and_set_the_next_action(self):
        if not self.detect_pick_fall():
            if not self.flag_enter_status:
                self.buy_phase = True
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
            # self.buy_shears(time_stamp, int(self.available_money / self.real_avg_list[-1]), 'avg')  # closeX2
            # if self.amount_limit_flag:
            # diff = round(-1*max(1.0,self.shears*0.007),3)
            diff = -0.007
            self.accumulated_amount += diff
            self.accumulated_amount_no_gap += diff
            if self.amount_limit_flag:
                # self.buy_shears(time_stamp, int(self.available_money / price), 'avg')  # closeX2
                self.accumulated_amount_limit += diff
                self.store_to_logs_info_limit('BUY', time_stamp, price, 1)
                # self.check_real_invest_in_the_stock_and_action(SA.Buy, price, time_stamp)
            self.flag_enter_status = True
            self.buy_phase = False


        elif self.sell_phase:
            # diff = round(stock_interval_change- max(1.0,self.shears*0.007),4)
            diff = stock_interval_change - 0.007
            self.accumulated_amount += diff
            self.accumulated_amount_no_gap += diff
            if self.amount_limit_flag:
                self.accumulated_amount_limit += diff
                self.store_to_logs_info_limit('SELL', time_stamp, price, 1)
                # self.check_real_invest_in_the_stock_and_action(SA.Sell, price, time_stamp)
                # self.sell_shears(time_stamp, self.shears, 'avg')  # close
            self.flag_enter_status = False
            self.sell_phase = False
            # self.sell_shears(time_stamp, self.shears, 'avg')  # close

        elif self.flag_enter_status:
            diff = round(stock_interval_change, 4)
            self.accumulated_amount += diff
            self.accumulated_amount_no_gap += diff
            if self.amount_limit_flag:
                self.accumulated_amount_limit += diff

    def Safe_Limit_condition_stock_trade(self,price,time_stamp):
        global limit_presantage
        # a= time_stamp%2
        # if a == 0:
        #     self.check_real_invest_in_the_stock_and_action(SA.Buy, price, time_stamp)
        # else:
        #     self.check_real_invest_in_the_stock_and_action(SA.Sell, price, time_stamp)
        # return
        relative_amount = self.accumulated_amount - self.start_accumulated_amount
        # relative_amount_min = price - self.min_per_day
        start_limit = 0
        add_limit = limit_presantage
        proff_from_start = (100 * relative_amount / self.relative_start_price) #in presantage
        if proff_from_start > self.amount_limit_num:
            if self.flag_enter_status and not self.amount_limit_flag:
                self.accumulated_amount_limit -= 0.007
                self.store_to_logs_info_limit('BUY', time_stamp, price, 1)
            self.amount_limit_flag = True
            if proff_from_start > (self.amount_limit_num + add_limit):
                self.amount_limit_num = proff_from_start
            self.check_real_invest_in_the_stock_and_action(SA.Buy, price, time_stamp)
                # self.buy_shears(time_stamp, int(self.available_money / self.real_avg_list[-1][time_stamp]), 'avg')  # closeX2

        elif proff_from_start < self.amount_limit_num:
            if self.flag_enter_status and self.amount_limit_flag:
                self.accumulated_amount_limit -= 0.007
                self.store_to_logs_info_limit('SELL', time_stamp, price, 1)
            self.amount_limit_flag = False
            self.check_real_invest_in_the_stock_and_action(SA.Sell, price, time_stamp)

        self.limit_price = (1 + self.amount_limit_num / 100) * self.relative_start_price

    def plotting_all_data(self, start, end):
        global PATH_RESULTS
        figure, axis = plt.subplots(2, 1)
        figure.suptitle(self.stock_name + '_' + start + '->' + end,fontsize=16)
        figure.tight_layout(h_pad=2)
        sub_lines_width = 0.3
        for i in range(len(self.real_avg_list)):
            axis[0].axvline(x=i, linewidth=sub_lines_width, color="y", linestyle="--")
            axis[1].axvline(x=i, linewidth=sub_lines_width, color="y", linestyle="--")

        real_avg_list = self.real_avg_list
        start_price = self.start_price
        axis[0].plot(np.arange(self.counter), real_avg_list, color='g', label="real avg")


        # axis[0].plot(np.arange(self.counter), self.avg_list_no_gap[], color='y', label="avg no gap")
        axis[0].set_title("start:" + '%.2f' % (start_price) + " end:" + '%.2f' % (real_avg_list[-1]) + ' diff:' + '%.2f' % (
                        real_avg_list[-1] - start_price) + " max/min/end: " + '%.2f' % (
                        100 * ((max(real_avg_list) - start_price) / start_price)) + '%,' + '%.2f' % (
                        100 * ((min(real_avg_list) - start_price) / start_price)) + '%,' + '%.2f' % (
                        100 * ((real_avg_list[-1] - start_price) / start_price)) + '%')
        try:
            x, y = zip(*self.limit_points_buy_sell["BUY"])
            x, y = list(x), list(y)
            axis[0].plot(x, y, marker='s', linestyle=' ', color='b', markersize=3)
            x, y = zip(*self.limit_points_buy_sell["SELL"])
            x, y = list(x), list(y)
            axis[0].plot(x, y, marker='^', linestyle=' ', color='r', markersize=3)
        except:
            x=1

        axis[1].plot(np.arange(self.counter), self.amount_list, color='r')
        # axis[1].plot(np.arange(self.counter), self.amount_list_no_gap, color='y')
        axis[1].plot(np.arange(self.counter), self.amount_limit, color='blue')

        # axis[1].plot(self.minutes_per_day, list_acumilated_gaps, color='orange')
        axis[1].axhline(y=0, linewidth=sub_lines_width, color="g", linestyle="--")
        axis[1].set_title("amount-> end val:" + '%.2f' % (self.amount_limit[-1]) + " max/min/end: " + '%.2f' % (100 * ((max(self.amount_limit)) / start_price)) + '%,' + '%.2f' % (100 * ((min(self.amount_limit)) / start_price)) + '%,' + '%.2f' % (100 * (self.amount_limit[-1] / start_price)) + '%,' + '%.2f' % (100 * (self.amount_limit[-1] / start_price)) + '%')

        figure.savefig(PATH_RESULTS +'/'+ self.stock_name+'/'+ self.stock_name + '_' + start + '->' + end,dpi=300)
        all_results_path_dates = PATH_RESULTS + '/ALL_RESULTS'+'/ALL_stocks_for_'+ start + '->' + end
        if not os.path.isdir(all_results_path_dates):
            os.mkdir(all_results_path_dates)
        figure.savefig(all_results_path_dates+'/'+ self.stock_name,dpi=300)
        # plt.show()
        # plt.clf()

        return

    def store_to_logs_info(self,action,time_stamp,price,shears):
        global current_date
        self.demo_logs.append(current_date+' Demo, time stamp:'+str(time_stamp)+' action:'+action+' price:'+str(price)+' shears:'+str(shears)+ ' proff:'+"%.2f" %(100*self.accumulated_amount/self.start_price))
    def store_to_logs_info_limit(self,action,time_stamp,price,shears):
        global current_date
        current_time = dt.datetime.today().strftime('%H:%M:%S')
        self.demo_limit_logs.append(current_time+' Demo limit, time stamp:'+str(time_stamp)+' ,action:'+action+' ,price:'+str(price)+' ,shears:'+str(shears)+ ' ,commission:0.007 ,proff:'+"%.2f" %(100*self.accumulated_amount_limit/self.start_price))
        self.demo_limit_logs_csv.append([current_time,time_stamp,action,price,shears,0.007,round(100*self.accumulated_amount_limit/self.start_price,2)])
        if len(self.demo_limit_logs_csv)>1:
            last_action = self.demo_limit_logs_csv[-2][2]
            if  action == last_action:
                raise RuntimeError
    def write_to_log_info(self):
        global PATH_RESULTS
        import csv
        if not os.path.isdir(PATH_RESULTS):
            os.mkdir(PATH_RESULTS)
        stock_path = PATH_RESULTS + '/'+self.stock_name
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
        stock_log_price_times_path = stock_path + '/log_price_times' + self.stock_name + '.csv'
        with open(stock_log_price_times_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(self.real_avg_list_times)  # Write the list as a single row
            writer.writerow(self.real_avg_list)  # Write the list as a single row
            writer.writerow(self.real_volume_list)  # Write the list as a single row

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




def update_my_portfolio_files(stock, new_cash_invest_stock, ratio):
    global stock_that_been_used
    global my_portfolio
    if stock not in stock_that_been_used:
        stock_that_been_used.update({stock:[]})
    if stock in my_portfolio:
        with my_portfolio[stock].key_lock_available_money:
            my_portfolio[stock].flag_invest_in_this_stock = True
            my_portfolio[stock].available_money += new_cash_invest_stock
            my_portfolio[stock].total_stock_net_value += new_cash_invest_stock
            if my_portfolio[stock].init_money == 0:
                my_portfolio[stock].init_money = new_cash_invest_stock
    else:
        my_portfolio.update({stock: Real_Stock_Object(stock,None,new_cash_invest_stock)})
    if new_cash_invest_stock>0:
        my_portfolio[stock].flag_invest_in_this_stock=True
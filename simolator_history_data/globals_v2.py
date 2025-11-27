import threading
#50000 23876701.20093375 23826701.20093375 47653.402401867505 %->0.2

dbg_on_real_data = False
local_path_file = ''
job_by_one_thread = ''
my_available_money_dollar_start = 50000
ratio_trade_in_volume_minute = 0.1
limit_presantage = 1
factor = 1
diff_p = 0.3
statistic_flag = True
statistic_list = []
real_time_commision =0.03
avg_commission_per_shear = 0.0075
my_available_money_dollar = my_available_money_dollar_start
not_first_day = False
current_date = ''
demo_portfolio_treads = {}
my_portfolio = {}
stock_that_been_used ={}
my_init_demo_available_money_dollar = 2e5
day_timestamp = 60 * 60 * 24
flag_first_day = True
counter = 0
real_logs = list()
real_logs_csv = list()
day_barrier = threading.Barrier(0)
min_num_of_time_stamp_in_stocks_current_day = 9999
slop_d_num_neg_flag = -0.002
slop_d_num_pos_flag = 0
slop_num_pos_flag = 0
PATH_RESULTS = '/Users/ofirdahan/Desktop/interactive_brokers/stock_analyzer/local_data_result'
PATH_STOCKS_DATA = '/Users/ofirdahan/Desktop/interactive_brokers/stock_data/'
stocks_data = {}
data_request = 'LOCAL'
class Real_Stock_actions:
    Buy = 0
    Sell = 1
    Return_Available_cash = 2
    Collect_divide_again = 3


import requests
import csv
import os

PATH_STOCKS_DATA = '/Users/ofirdahan/Desktop/interactive brokers/stock_data/'

# with open(PATH_STOCKS_DATA+'/AAPL_2020_02.csv', 'r') as f_input:
#     for row in csv.reader(f_input):
#         txt += row[0]
#     #     data_chart.append(np.array(list(map(float, row))))
#     #     data_chart.append(np.array(list(map(float, row))))
#     # data_chart = np.array(data_chart)
# txt = txt.replace('\n\n','\n')
# print(txt)
#     data_chart = np.array([list(map(float, row)) if ':' not in row[0] else [] for row in csv.reader(f_input)])
# with open(PATH_STOCKS_DATA+'/AAPL_2020_02.txt', 'w') as output:
#     output.write(txt)
stocks_check = ['AAPL','AMD','TQQQ','VOO','DIS','ITB','TSLA','LLY','MSTR']
stocks_check += ['TSM','NFLX','GOOG','NVDA','AMZN','AVGO','NVO','MA','PG','MRK','HD','AMT','SOXL','MCD']
stocks_check += ['META','MAGS','MSFT','TQQQ']
# stocks_check = ['JNJ','V','MA','CVX']

# stocks_check = ['SOXL','AAPL','SEDG','NKE','NVDA','CAR']

# dates = ["2022-01","2022-02","2022-03","2022-04","2022-05","2022-06","2022-07","2022-08","2022-09"]
dates = ["2022-07","2022-08","2022-09","2022-10","2022-11","2022-12"]
dates += ["2023-01","2023-02","2023-03","2023-04","2023-05","2023-06","2023-07","2023-08","2023-09","2023-10","2023-11","2023-12"]
dates += ["2024-01","2024-02","2024-03","2024-04","2024-05","2024-06","2024-07"]
# dates = ["2022-04","2022-05"]
# replace the "demo" apikey below with your own key from https://www.alphavantage.co/support/#api-key
# https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=NVDA&interval=1min&month=2022-04&extended_hours=false&outputsize=full&apikey=VD30K55BBWA3Z6YF&datatype=csv
def create_data_file(stocks_list,dates):
    ALpha_Key_2 = ""
    key = ALpha_Key_2
    txt = ''
    counter = 0
    for stock in stocks_list:
        for year_month in dates:
            file_name = f"{stock}_{year_month.replace('-','_')}.txt"
            if os.path.exists(PATH_STOCKS_DATA + f"{stock}/" + file_name):
                continue
            try:
                url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={stock}&interval=1min&month={year_month}&extended_hours=false&outputsize=full&apikey={key}&datatype=csv"
                r = requests.get(url)
                txt = r.text
                if "Our standard API rate limit is 25 requests per day." in txt:
                    return f"exceedded the 25 amount at stock:{stock} date:{year_month}\n"+txt,counter
            except:
                print("can't pull data from web")
                pass
            if not os.path.exists(PATH_STOCKS_DATA + f"{stock}"):
                os.mkdir(PATH_STOCKS_DATA + f"{stock}")
            with open(PATH_STOCKS_DATA + f"{stock}/" + file_name, 'w+') as output:
                output.write(txt)
            counter+=1
    return "success!",counter

def convert_csv_to_txt_file(dir_path):
    import glob
    csv_file_paths = glob.glob(dir_path+"*/*.csv")
    for csv_file_path in csv_file_paths:
        with open(csv_file_path, 'r') as f_input:
            txt = f_input.read()
            txt_path = csv_file_path.replace('csv','txt')
            with open(txt_path, 'w+') as f_output:
                f_output.write(txt)
        os.remove(csv_file_path)

convert_csv_to_txt_file(PATH_STOCKS_DATA)
status,used = create_data_file(stocks_check,dates)
print(f"pull used: {used}")
print(status)

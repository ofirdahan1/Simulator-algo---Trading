#start 1,024,233 30/9/24
import time
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

# a= np.array([1,2,3,4])
# print(a)
# a = np.append(a,5)
# print(a)
# a= [1,3,6,55]
# print(a[-1])
# Get the current time
print(round(3.126456,2))
a= sum([1.65,4.90909,6])
for i in range(1000):
    print(i)
    time.sleep(10)
x= datetime.today().strftime('%Hh_%Mm_%Ss')
g = set([x for x in range(10) if x%2==0])
symbol_position_updated = {1, 2, 3,4}
my_portfolio ={1:'a',3:'c',2:'b',4:'g',5:'x'}
my_portfolio =set(my_portfolio)
print(symbol_position_updated.issubset(set(my_portfolio)))
print(my_portfolio.issubset(set(symbol_position_updated)))
# current_time = datetime.datetime.now()
#
# time_next_minute_break = datetime.datetime(current_time.year, current_time.month, current_time.day, current_time.hour, current_time.minute, 0) + datetime.timedelta(minutes=1)
# time_next_minute_break = current_time
# time_10_sec_prep = time_next_minute_break-datetime.timedelta(hours=1)
# diff = time_10_sec_prep - datetime.datetime.now()
# diff_t =datetime.datetime.now() - time_10_sec_prep
# print(diff>datetime.timedelta(seconds=10))

if 0:
    print('0')

x= [1,3,5]
y= [2,4,6]
plt.plot(x,y ,marker='^', linestyle=' ', color='r', markersize=3)
plt.plot(y,x ,marker='s', linestyle=' ', color='b', markersize=3)

# Add labels and title
plt.xlabel('X-axis')
plt.ylabel('Y-axis')
plt.title('Plot points using plt.plot()')

# Show plot
plt.show()
current_time = datetime.datetime.now()
# time.sleep(0.9)
# Set a specific time (e.g., 15:30:00 or 3:30 PM)
specific_time = datetime.datetime(current_time.year, current_time.month, current_time.day, 22, 0, 0)
new_time = current_time + datetime.timedelta(seconds=70)
print(current_time)
print(new_time)
current_time = datetime.datetime.now()
time.sleep(1)
# specific_time =current_time+datetime.timedelta(milliseconds=0)
diff = specific_time - datetime.datetime.now()
print(diff.seconds)
time.sleep(diff.seconds)
# Compare current time with the specific time
if current_time > specific_time:
    print("The specific time has already passed.")
elif current_time < specific_time:
    print("The specific time is in the future.")
else:
    print("It's exactly the specific time!")
print(current_time)
# %%
import os
import json
import sys
import datetime
import time
import pymysql
import requests
import matplotlib
import statistics
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import numpy as np
import jieba
from jieba import analyse
import enum

# %%
data = []


class Status(enum.Enum):
    readingText = 1
    idle = 2


tmp = {'pid': None, 'time': None, 'text': '',
       'likenum': None, 'reply': None, 'deleted': False}
list_dirs = os.walk('./archive')
for root, dirs, files in list_dirs:
    for f in files:
        print('analyzing %s' % os.path.join(root, f), end="\r")
        status = Status.idle
        with open(os.path.join(root, f), "r", encoding='utf8') as f:
            for line in f:
                if line.startswith('#p'):
                    tmp['text'] = tmp['text'][0:-2]  # Delete \n\n
                    if tmp['pid']:
                        data.append(tmp)
                    strs = line.split(' ')
                    status = Status.readingText
                    tmp = {'pid': int(strs[1]), 'time': datetime.datetime.strptime(
                        strs[2] + ' ' + strs[3], '%Y-%m-%d %H:%M:%S'), 'text': '', 'likenum': int(strs[4]), 'reply': int(strs[5]), 'deleted': False}
                elif line.startswith('#c'):
                    status = Status.idle
                elif line.startswith('#DELETED'):
                    tmp['deleted'] = True
                else:
                    if status == Status.readingText:
                        tmp['text'] += line
                        if line.startswith('#MISSED'):
                            tmp['deleted'] = True
            if status == Status.readingText:
                tmp['text'] = tmp['text'][0:-2]
                data.append(tmp)

data.sort(key=lambda x: x['pid'], reverse=False)  # 排列，根据pid
print(len(data))

# %%

print(len(data))
print(data[-99])

# %%
print(len([i for i in data if (i['text'] == '#MISSED')]))
len([i for i in data if (i['deleted'])])
# reduce(lambda count, i: count + my_condition(i), l, 0)

# %%
plt.rcParams["figure.figsize"] = (10, 5)
barWidth = 0.2

plotdata16 = np.zeros(24)
plotdata17 = np.zeros(24)
plotdata18 = np.zeros(24)
plotdata19 = np.zeros(24)
for i in data:
    if i['time'].year == 2016:
        plotdata16[i['time'].hour] += 1
    elif i['time'].year == 2017:
        plotdata17[i['time'].hour] += 1
    elif i['time'].year == 2018:
        plotdata18[i['time'].hour] += 1
    elif i['time'].year == 2019:
        plotdata19[i['time'].hour] += 1

plotdata16 = plotdata16 / np.linalg.norm(plotdata16)
plotdata17 = plotdata17 / np.linalg.norm(plotdata17)
plotdata18 = plotdata18 / np.linalg.norm(plotdata18)
plotdata19 = plotdata19 / np.linalg.norm(plotdata19)

fig, ax = plt.subplots()
ax.bar([i + 1 * barWidth for i in range(24)], plotdata16, barWidth,
       label='2016, N=%d' % len([0 for i in data if i['time'].year == 2016]))
ax.bar([i + 2 * barWidth for i in range(24)], plotdata17, barWidth,
       label='2017, N=%d' % len([0 for i in data if i['time'].year == 2017]))
ax.bar([i + 3 * barWidth for i in range(24)], plotdata18, barWidth,
       label='2018, N=%d' % len([0 for i in data if i['time'].year == 2018]))
ax.bar([i + 4 * barWidth for i in range(24)], plotdata19, barWidth,
       label='2019, N=%d' % len([0 for i in data if i['time'].year == 2019]))
ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
plt.title(
    'PKUHole Posts Sending Hour Statistics')
plt.xlabel('Hour')
plt.ylabel('(Normalized) Posts Count')
ax.set_xlim(0, 24)
ax.legend()
plt.show()


# %%
plt.rcParams["figure.figsize"] = (16, 9)

plotdata = []
plotx = []
now_yearmonth = None
for i in data:
    if [i['time'].year, i['time'].month] != now_yearmonth:
        now_yearmonth = [i['time'].year, i['time'].month]
        plotx.append(i['time'])
        plotdata.append(0)
    plotdata[-1] += 1

plotx = matplotlib.dates.date2num(plotx)

fig, ax = plt.subplots()
ax.bar(plotx, plotdata, 24*0.8)
ax.xaxis.set_major_locator(mdates.MonthLocator([1, 3, 5, 7, 9, 11]))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%y/%m'))
plt.title('PKUHole Heat Statistics, N=%d' % len(data))
plt.xlabel('Time')
plt.ylabel('Heat')
plt.show()

# %%
plt.rcParams["figure.figsize"] = (16, 9)

plotdata = []
plotx = []
now_yearmonth = None
for i in data:
    if [i['time'].year, i['time'].month] != now_yearmonth:
        now_yearmonth = [i['time'].year, i['time'].month]
        plotx.append(i['time'])
        plotdata.append([])
    plotdata[-1].append(1 if i['deleted'] else 0)

plotx = matplotlib.dates.date2num(plotx)
plotdata2 = [statistics.mean(i) for i in plotdata]
average = np.average(plotdata2, weights=[len(i) for i in plotdata])

fig, ax = plt.subplots()
ax.plot(plotx, np.full(len(plotx), average),
        'y--', label='Average=%s' % str(average*100)[0:4] + '%')
ax.bar(plotx, plotdata2, 24*0.8)
ax.xaxis.set_major_locator(mdates.MonthLocator([1, 3, 5, 7, 9, 11]))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%y/%m'))
plt.title('PKUHole Deletion Rate Statistics, N=%d' % len(data))
plt.xlabel('Time')
plt.ylabel('Deletion Rate')
ax.legend()
plt.show()
# %%
plt.rcParams["figure.figsize"] = (16, 9)

plotdata = []
plotx = []
now_yearmonth = None
for i in data:
    if [i['time'].year, i['time'].month] != now_yearmonth:
        now_yearmonth = [i['time'].year, i['time'].month]
        plotx.append(i['time'])
        plotdata.append([])
    if i['reply'] >= 0:
        plotdata[-1].append(i['reply'])

plotx = matplotlib.dates.date2num(plotx)
plotdata2 = [(statistics.mean(i)if len(i) > 0 else 0) for i in plotdata]
average = np.average(plotdata2, weights=[len(i) for i in plotdata])

fig, ax = plt.subplots()
ax.plot(plotx, np.full(len(plotx), average),
        'y--', label='Average=%s' % str(average)[0:4])
ax.bar(plotx, plotdata2, 24*0.8)
ax.xaxis.set_major_locator(mdates.MonthLocator([1, 3, 5, 7, 9, 11]))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%y/%m'))
plt.title(
    'PKUHole Average Number of Replies Statistics, N=%d' % len([0 for i in data if i['reply'] >= 0]))
plt.xlabel('Time')
plt.ylabel('Average Number of Replies')
ax.legend()
plt.show()
# %%
plt.rcParams["figure.figsize"] = (16, 9)

plotdata = []
plotx = []
now_yearmonth = None
for i in data:
    if [i['time'].year, i['time'].month] != now_yearmonth:
        now_yearmonth = [i['time'].year, i['time'].month]
        plotx.append(i['time'])
        plotdata.append([])
    if i['likenum'] >= 0:
        plotdata[-1].append(i['likenum'])

plotx = matplotlib.dates.date2num(plotx)
plotdata2 = [(statistics.mean(i)if len(i) > 0 else 0) for i in plotdata]
average = np.average(plotdata2, weights=[len(i) for i in plotdata])

fig, ax = plt.subplots()
ax.plot(plotx, np.full(len(plotx), average),
        'y--', label='Average=%s' % str(average)[0:4])
ax.bar(plotx, plotdata2, 24*0.8)
ax.xaxis.set_major_locator(mdates.MonthLocator([1, 3, 5, 7, 9, 11]))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%y/%m'))
plt.title(
    'PKUHole Average Number of Attentions Statistics, N=%d' % len([0 for i in data if i['likenum'] >= 0]))
plt.xlabel('Time')
plt.ylabel('Average Number of Attentions')
ax.legend()
plt.show()

# %%
plt.rcParams["figure.figsize"] = (10, 5)
barWidth = 0.2

plotdata16 = []
plotdata17 = []
plotdata18 = []
plotdata19 = []
for i in range(24):
    plotdata16.append([])
    plotdata17.append([])
    plotdata18.append([])
    plotdata19.append([])
for i in data:
    if i['time'].year == 2016:
        plotdata16[i['time'].hour].append(1 if i['deleted'] else 0)
    elif i['time'].year == 2017:
        plotdata17[i['time'].hour].append(1 if i['deleted'] else 0)
    elif i['time'].year == 2018:
        plotdata18[i['time'].hour].append(1 if i['deleted'] else 0)
    elif i['time'].year == 2019:
        plotdata19[i['time'].hour].append(1 if i['deleted'] else 0)

plotdata16n = [statistics.mean(i) for i in plotdata16]
plotdata17n = [statistics.mean(i) for i in plotdata17]
plotdata18n = [statistics.mean(i) for i in plotdata18]
plotdata19n = [statistics.mean(i) for i in plotdata19]

fig, ax = plt.subplots()
ax.bar([i + 1 * barWidth for i in range(24)], plotdata16n, barWidth,
       label='2016, N=%d' % len([0 for i in data if i['time'].year == 2016]))
ax.bar([i + 2 * barWidth for i in range(24)], plotdata17n, barWidth,
       label='2017, N=%d' % len([0 for i in data if i['time'].year == 2017]))
ax.bar([i + 3 * barWidth for i in range(24)], plotdata18n, barWidth,
       label='2018, N=%d' % len([0 for i in data if i['time'].year == 2018]))
ax.bar([i + 4 * barWidth for i in range(24)], plotdata19n, barWidth,
       label='2019, N=%d' % len([0 for i in data if i['time'].year == 2019]))
ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
plt.title(
    'PKUHole Deletion Rate Statistics')
plt.xlabel('Hour')
plt.ylabel('Deletion Rate')
ax.set_xlim(0, 24)
ax.legend()
plt.show()

# %%
plt.rcParams["figure.figsize"] = (10, 5)
barWidth = 0.2

plotdata16 = []
plotdata17 = []
plotdata18 = []
plotdata19 = []
for i in range(24):
    plotdata16.append([])
    plotdata17.append([])
    plotdata18.append([])
    plotdata19.append([])
for i in data:
    if i['likenum'] >= 0 and i['deleted']:
        if i['time'].year == 2016:
            plotdata16[i['time'].hour].append(i['likenum'])
            print(i['time'].hour)
        elif i['time'].year == 2017:
            plotdata17[i['time'].hour].append(i['likenum'])
        elif i['time'].year == 2018:
            plotdata18[i['time'].hour].append(i['likenum'])
        elif i['time'].year == 2019:
            plotdata19[i['time'].hour].append(i['likenum'])

plotdata16n = [(statistics.mean(i)if len(i) > 0 else 0) for i in plotdata16]
plotdata17n = [statistics.mean(i) for i in plotdata17]
plotdata18n = [statistics.mean(i) for i in plotdata18]
plotdata19n = [statistics.mean(i) for i in plotdata19]

fig, ax = plt.subplots()
ax.bar([i + 1 * barWidth for i in range(24)], plotdata16n, barWidth,
       label='2016, N=%d' % len([0 for i in data if (i['time'].year == 2016 and i['deleted'] and i['likenum'] >= 0)]))
ax.bar([i + 2 * barWidth for i in range(24)], plotdata17n, barWidth,
       label='2017, N=%d' % len([0 for i in data if (i['time'].year == 2017 and i['deleted'] and i['likenum'] >= 0)]))
ax.bar([i + 3 * barWidth for i in range(24)], plotdata18n, barWidth,
       label='2018, N=%d' % len([0 for i in data if (i['time'].year == 2018 and i['deleted'] and i['likenum'] >= 0)]))
ax.bar([i + 4 * barWidth for i in range(24)], plotdata19n, barWidth,
       label='2019, N=%d' % len([0 for i in data if (i['time'].year == 2019 and i['deleted'] and i['likenum'] >= 0)]))
ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
plt.title(
    'PKUHole Deleted Posts Average Number of Attention Statistics')
plt.xlabel('Hour')
plt.ylabel('Average Number of Attention')
ax.set_xlim(0, 24)
ax.legend()
plt.show()


# %%
plt.rcParams["figure.figsize"] = (10, 5)
barWidth = 0.2

plotdata16 = []
plotdata17 = []
plotdata18 = []
plotdata19 = []
for i in range(24):
    plotdata16.append([])
    plotdata17.append([])
    plotdata18.append([])
    plotdata19.append([])
for i in data:
    if i['reply'] >= 0 and i['deleted']:
        if i['time'].year == 2016:
            plotdata16[i['time'].hour].append(i['reply'])
            print(i['time'].hour)
        elif i['time'].year == 2017:
            plotdata17[i['time'].hour].append(i['reply'])
        elif i['time'].year == 2018:
            plotdata18[i['time'].hour].append(i['reply'])
        elif i['time'].year == 2019:
            plotdata19[i['time'].hour].append(i['reply'])

plotdata16n = [(statistics.mean(i)if len(i) > 0 else 0) for i in plotdata16]
plotdata17n = [statistics.mean(i) for i in plotdata17]
plotdata18n = [statistics.mean(i) for i in plotdata18]
plotdata19n = [statistics.mean(i) for i in plotdata19]

fig, ax = plt.subplots()
ax.bar([i + 1 * barWidth for i in range(24)], plotdata16n, barWidth,
       label='2016, N=%d' % len([0 for i in data if (i['time'].year == 2016 and i['deleted'] and i['reply'] >= 0)]))
ax.bar([i + 2 * barWidth for i in range(24)], plotdata17n, barWidth,
       label='2017, N=%d' % len([0 for i in data if (i['time'].year == 2017 and i['deleted'] and i['reply'] >= 0)]))
ax.bar([i + 3 * barWidth for i in range(24)], plotdata18n, barWidth,
       label='2018, N=%d' % len([0 for i in data if (i['time'].year == 2018 and i['deleted'] and i['reply'] >= 0)]))
ax.bar([i + 4 * barWidth for i in range(24)], plotdata19n, barWidth,
       label='2019, N=%d' % len([0 for i in data if (i['time'].year == 2019 and i['deleted'] and i['reply'] >= 0)]))
ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
plt.title(
    'PKUHole Deleted Posts Average Number of Reply Statistics')
plt.xlabel('Hour')
plt.ylabel('Average Number of Reply')
ax.set_xlim(0, 24)
ax.legend()
plt.show()

# %%

import datetime
# import os
import time

from flask import Flask, render_template, request, redirect, url_for
from forms import *
from spider import Basic, BiliLottery
import webbrowser

app = Flask(__name__)

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

basicinfo = {}


# BLottery = BiliLottery(basicinfo)


@app.route('/')
def index():
    form = LoginForm(request.form)
    return render_template('forms/login.html', form=form)


@app.route('/login', methods=['POST'])
def login():
    global basicinfo
    uid = request.form.get('uid')
    sessdata = request.form.get('sessdata')
    csrf = request.form.get('csrf')
    tagid = request.form.get('tagid')
    basic = Basic()
    path = basic.folder_path()
    verify = basic.verify(sessdata, csrf)
    basicinfo = {'uid': uid, 'tagid': [tagid], 'folder_path': path, 'verify': verify}  #
    return redirect(url_for('home'))


@app.route('/home')
def home():
    global BLottery
    BLottery = BiliLottery(basicinfo)
    df = BLottery.readcsv(file_name='data')
    if df.empty:
        return render_template('sb/index.html', total=0, new_lottery_number=0, new_lottery=[],
                               today_closed_lottery_number=0, today_closed_lottery=[], all = 0)
    else:
        alllottery = len(df)
        total_repost_lottery = df[df['是否已转发'] == 1]
        total = len(total_repost_lottery)
        todaystamp = int(time.mktime(datetime.date.today().timetuple()))
        # todaystamp = 1610769000
        tomorrowstamp = todaystamp + 86400
        today_closed_lottery = df[(todaystamp <= df['时间戳']) & (df['时间戳'] < tomorrowstamp)]
        today_closed_lottery_number = len(today_closed_lottery)
        today_closed_lottery = today_closed_lottery.iterrows()
        new_lottery = df[df['设奖时间'] == todaystamp]
        new_lottery_num = len(new_lottery)
        new_lottery = new_lottery.iterrows()

        return render_template('sb/index.html', total=total, new_lottery_number=new_lottery_num, new_lottery=new_lottery,
                               today_closed_lottery_number=today_closed_lottery_number,
                               today_closed_lottery=today_closed_lottery, all=alllottery)


@app.route('/lottery')
def lottery():
    BLottery.get_lottery_using_api()
    return redirect(url_for('record'))


@app.route('/record')
def record():
    df = BLottery.readcsv(file_name='data')
    if df.empty:
        return render_template('sb/records.html', lottery=[])
    else:
        df = BLottery.readcsv(file_name='data')
        return render_template('sb/records.html', lottery=df.iterrows())


@app.route('/unfollow_and_delrepo')
def unfollow_and_delrepo():
    num = BLottery.unfollow_and_delrepo()
    return render_template('sb/unfollow_and_delrepo.html', num=num)


@app.route('/repost')
def repost():
    num = BLottery.repost()
    return render_template('sb/repost.html', num=num)


@app.route('/info')
def info():
    return render_template('sb/info.html')


if __name__ == '__main__':
    webbrowser.open("http://127.0.0.1:5000", new=0, autoraise=True)
    app.run(debug=True)



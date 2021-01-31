import datetime
import random
import re
import sys
from bilibili_api import Verify, dynamic, user
from selenium import webdriver  # 导入Selenium
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup  # 导入BeautifulSoup 模块
import time
import csv
import pandas as pd


class Basic:
    def __init__(self):
        self.path = sys.path[0]
        # print(self.path)

    def verify(self, sessdata, csrf):
        return Verify(sessdata=sessdata, csrf=csrf)

    def folder_path(self):
        return self.path


def getqualifieduser(basicinfo, uid_range):
    folder_path = basicinfo['folder_path']
    verify = basicinfo['verify']

    now = datetime.datetime.now()
    delta = datetime.timedelta(days=366)
    year_before = now - delta
    year_before = time.mktime(year_before.timetuple())

    f_all = open('%s\\alluser.csv' % folder_path, 'a', encoding='GB18030', newline="")
    alluser_writer = csv.writer(f_all)
    f_official = open('%s\\officialuser.csv' % folder_path, 'a', encoding='GB18030', newline="")
    officialuser_writer = csv.writer(f_official)
    # csv_writer.writerow(["uid", "用户名", "lv", "role-type", "粉丝数"])
    for uid in uid_range:
        print(uid)
        o = user.get_user_info(uid=uid)
        if o is None or o == []:
            print('None')
            continue
        role_type = o['official']['role']
        role_title = o['official']['title']
        nickname = o["name"]
        lv = o["level"]
        vip_type = o["vip"]["type"]
        alluser_writer.writerow([uid, nickname, lv, vip_type, role_type, role_title])
        if role_type != 0:
            v = user.get_videos(uid=uid, limit=1, verify=verify)
            if v is None or v == []:
                print('None')
                continue
            if v[0]["created"] < year_before:
                continue
            officialuser_writer.writerow([uid, nickname, lv, vip_type, role_type, role_title])

    f_all.close()
    f_official.close()


class BiliLottery:
    def __init__(self, basicinfo):  # 类的初始化操作
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/87.0.4280.88 Safari/537.36'}  # 给请求指定一个请求头来模拟chrome浏览器
        self.folder_path = basicinfo['folder_path']
        self.verify = basicinfo['verify']
        self.uid = basicinfo['uid']
        self.tagid = basicinfo['tagid']

    def setdriver(self):
        # 使用Chrome_headless通过selenium来进行网络请求
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        # chrome_options.add_argument("--auto-open-devtools-for-tabs")
        chrome_options.add_argument("start-maximized")
        driver = webdriver.Chrome('%s//chromedriver' % self.folder_path, options=chrome_options)
        # driver = webdriver.Chrome()
        return driver

    def get_dynamic(self):
        origin_existed_lottery = self.readcsv('data')
        if origin_existed_lottery.empty:
            titlerow = ["rid", "uid", "用户名", "开奖时间", "时间戳", "奖品", "设奖时间", "链接", "是否已转发", "是否已取关"]
            self.createcsv('data', titlerow)
        new_lottery = []
        new_lottery_cnt = 0
        ouser = self.readcsv('officialuser')
        uid_range = ouser['uid']
        uid_range = [928123, 394205865, 16794231]

        init_num = len(origin_existed_lottery)
        driver = self.setdriver()
        for uid in uid_range:
            self.get_dynamic_raw(uid=uid, driver=driver)
        existed_lottery = self.readcsv('data')
        existed_lottery = existed_lottery.drop_duplicates('rid')
        new_lottery = existed_lottery[init_num:]
        new_lottery_cnt = len(new_lottery)
        existed_lottery.to_csv("%s\\data.csv" % self.folder_path, index=False, encoding="GB18030")
        driver.quit()
        return [new_lottery, new_lottery_cnt]

    def get_dynamic_raw(self, uid, driver):
        new_lottery = []
        new_lottery_cnt = 0
        print(uid)
        web_url = 'https://space.bilibili.com/%d/dynamic' % uid  # 要访问的网页地址
        driver.get(web_url)
        time.sleep(0.5)

        self.scroll_down(driver=driver, times=2)  # 执行网页下拉到底部操作，执行1次
        cnt1 = 0
        cnt2 = 0
        cnt3 = 0
        cnt4 = 0
        soup = BeautifulSoup(driver.page_source, 'lxml').find_all(class_='card')  # 获取网页
        for item in soup:
            cnt1 = cnt1 + 1
            up_dynamic = item.find(class_='content-full')  # 获取动态
            if up_dynamic:
                cnt2 = cnt2 + 1
                if up_dynamic.find(attrs={"click-title": "抽奖详情"}):  # 获取抽奖动态
                    rid = item['data-did']  # 获取dynamic_id
                    cnt3 = cnt3 + 1
                    nickname = item.find(class_="user-name").get_text()  # 获取用户名
                    href = 'https://t.bilibili.com/lottery/h5/index/#/result?business_id=%s&business_type=1&isWeb=1' % rid  # 获取抽奖详情页链接
                    js = 'window.open("%s");' % href  # 新开一个窗口，通过执行js来新开一个窗口
                    driver.execute_script(js)
                    driver.switch_to.window(driver.window_handles[-1])
                    time.sleep(0.5)

                    lottery_detail = BeautifulSoup(driver.page_source, 'lxml')  # 获取抽奖详情页
                    # print(href)
                    # print(lottery_detail.prettify())
                    # print('\n\n')
                    if lottery_detail.find(class_='title'):  # 根据有无title这个类来判断该抽奖是否过期
                        cnt4 = cnt4 + 1
                        detail = lottery_detail.find_all(class_='config-row')  # 获取开奖的时间和条件
                        draw_time = detail[0].get_text().split('：')[1]  # 取出开奖时间
                        timestamp = time.strptime(draw_time, '%Y年%m月%d日 %H:%M')
                        # 转换成时间戳
                        timestamp = int(time.mktime(timestamp))
                        draw_condition = detail[1].get_text()  # 取出抽奖条件
                        prizes = lottery_detail.find_all(class_='prize-desc')  # 获取奖品
                        prize = []
                        for Prize in prizes:
                            prize.append(Prize.get_text())

                        # dynamic.repost(dynamic_id=rid, verify=self.verify)      # 转发
                        self.writecsv('data', [rid, uid, nickname, draw_time, timestamp, draw_condition, prize, 0])
                        new_lottery.append([rid, uid, nickname, draw_time, timestamp, draw_condition, prize])
                        new_lottery_cnt += 1
                        # print([uid, rid, nickname, draw_time, draw_condition, prize])
                        # print('\n\n\n')
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
        if cnt4 > 0:
            user.set_subscribe(uid=uid, verify=self.verify)  # 关注
            # user.move_user_subscribe_group(uid=uid, group_ids=self.tagid, verify=self.verify)

        print(cnt1)
        print(cnt2)
        print(cnt3)
        print(cnt4)
        return [new_lottery, new_lottery_cnt]
        # driver.close()

    def createcsv(self, file_name, titlerow):
        f = open('%s\\%s.csv' % (self.folder_path, file_name), 'w', encoding='GB18030', newline="")
        csv_writer = csv.writer(f)
        csv_writer.writerow(titlerow)
        f.close()

    def writecsv(self, file_name, data):  # 写入csv
        f = open('%s\\%s.csv' % (self.folder_path, file_name), 'a', encoding='GB18030', newline="")
        csv_writer = csv.writer(f)
        csv_writer.writerow(data)
        f.close()

    def overwritecsv(self, file_name, titlerow):  # 写入csv
        f = open('%s\\%s.csv' % (self.folder_path, file_name), 'w', encoding='GB18030', newline="")
        csv_writer = csv.writer(f)
        csv_writer.writerow(titlerow)
        f.close()

    def readcsv(self, file_name):
        df = pd.read_csv('%s\\%s.csv' % (self.folder_path, file_name), encoding='GB18030')
        df = pd.DataFrame(df)
        return df

    def scroll_down(self, driver, times):
        for i in range(times):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")  # 执行JavaScript实现网页下拉倒底部
            time.sleep(0.5)  # 等待0.5秒，页面加载出来再执行下拉操作

    def unfollow_and_delrepo(self):
        self.get_subscribe()
        df = pd.read_csv('%s\\%s.csv' % (self.folder_path, 'data'), encoding='GB18030', dtype='str')
        df = pd.DataFrame(df)
        if '转发rid' not in df.columns:
            df['转发rid'] = ''
        sub = self.readcsv('subscribe')
        nowstamp = str(time.time())
        closed_lottery = df[(nowstamp >= df['时间戳']) & (df['是否已取关'] == '0') & (df['是否已转发'] == '1')]
        num = 0
        for line in closed_lottery.iterrows():
            issub = sub[sub['uid'] == line[1][1]]
            print(issub)
            if issub.empty:
                user.cancel_subscribe(uid=line[1][1], verify=self.verify)
                df.loc[df[df['uid'].isin([line[1][1]])].index[0], '是否已取关'] = '1'
                if pd.notnull(line[1][10]):
                    dynamic.delete(int(line[1][10]), verify=self.verify)
                num = num + 1
                time.sleep(random.randint(1, 3))
        df.to_csv("%s\\data.csv" % self.folder_path, index=False, encoding="GB18030")
        # print(num)
        return num

    def get_lottery_using_api(self):
        df = self.readcsv('data')
        if df.empty:
            titlerow = ["rid", "uid", "用户名", "开奖时间", "时间戳", "奖品", "设奖时间", "链接", "是否已转发", "是否已取关", "转发rid"]
            self.createcsv('data', titlerow)
            self.get_subscribe()

        articles = user.get_articles(uid=2295698, limit=1)
        # print(articles)
        cvs = []
        for i in range(0, len(articles)):
            cvs.append(articles[i]['id'])
        driver = self.setdriver()
        descriptions = []
        for cv in cvs:
            web_url = 'https://www.bilibili.com/read/cv%d' % cv  # 要访问的网页地址
            driver.get(web_url)
            time.sleep(0.5)
            descriptions.append(BeautifulSoup(driver.page_source, 'lxml').find(class_='article-holder').get_text())

        gifts = []
        due_time = []
        rids = []
        for description in descriptions:
            patterngifts = re.compile(r'%s(.+?)%s' % ("奖品：", "截止："))
            gifts.append(patterngifts.findall(description))
            patterntime = re.compile(r'%s(.+?)%s' % ("截止：", "链接："))
            due_time.append(patterntime.findall(description))
            patternrid = re.compile(r'(?<=https://t.bilibili.com/)\d*')
            rids.append(patternrid.findall(description))
        driver = self.setdriver()
        for i in range(0, len(gifts)):  #
            for j in range(0, len(gifts[i])):  #
                web_url = 'https://t.bilibili.com/%s?tab=2' % rids[i][j]  # 要访问的网页地址
                driver.get(web_url)
                time.sleep(0.4)
                self.scroll_down(driver=driver, times=1)
                soup = BeautifulSoup(driver.page_source, 'lxml').find_all(class_='c-pointer',
                                                                          href=re.compile("space.bilibili.com"),
                                                                          target="_blank")
                if not soup:
                    continue
                # 最后一项是我们要的 用户名在get_text里， uid在href里
                # print(soup[-1])
                username = soup[-1].get_text()
                uid = soup[-1]['href']
                patternrid = re.compile(r'(?<=//space.bilibili.com/)\d*')
                uid = patternrid.findall(uid)[0]
                timestamp = time.strptime(due_time[i][j], '%Y-%m-%d %H:%M:%S')
                # 转换成时间戳
                timestamp = int(time.mktime(timestamp))
                todaystamp = int(time.mktime(datetime.date.today().timetuple()))
                self.writecsv("data",
                              [rids[i][j], uid, username, due_time[i][j], timestamp, gifts[i][j], todaystamp, web_url,
                               0, 0, ''])
                time.sleep(1)

        driver.quit()
        existed_lottery = self.readcsv('data')
        existed_lottery = existed_lottery.drop_duplicates('rid')
        existed_lottery.to_csv("%s\\data.csv" % self.folder_path, index=False, encoding="GB18030", float_format='str')

    # def repost(self):
    #     random.seed()
    #     repostword = ['感谢感谢！！！欧皇就是我本人 提前恭喜这个b     站用户', '大手笔', '希望中奖', '冲冲冲', '能邮过来让我康康吗',
    #                   '别转了 昨晚up说内定我了', '中！', '热乎的', '好多人啊', '这么多中奖活动都抽过，虽然没有中过但从来没放弃',
    #                   '从未中奖，从未放弃', '我可以拥有的！', '中一次呗', '万一呢', '祝我好运', '抽我！', '(=・ω・=)', '加油',
    #                   '还走什么流程啊，直接寄不就好了？', '转转转', '就让我来当个分母吧', '我该选哪个呢', '我来', '试一试', '好耶！',
    #                   '人与人的体质是不能相提并论的，我曾在极度愤怒的情况下暴转了一万条互动抽奖，又在极度暴怒的情况下成了柠檬精',
    #                   '重在参与', '拉低中奖率', '啊这', '分母集合', '下次一定中', '欧克欧克', '中奖是不可能中奖的 这辈子都不可能的',
    #                   '从未中，从未停', '中奖绝缘体', '好家伙', '老板大气', '我要白嫖', '我要', '这牛啊', '奥力给', '非酋9段的第1761！！！次实验',
    #                   '我要中啦', '我最喜欢这个了,我也想要', '秋梨膏', '啊啊啊啊啊啊啊啊啊啊啊', '大家都散了吧，已经抽完了，是我的',
    #                   '众所周知是抽奖有黑幕的，如果没有敢不敢抽到我', '看看我吧', '求一个！哈哈哈', '转发动态', '我的我的还是我的', 'ヾ(•ω•`)o',
    #                   '\\(@^0^@)/', '(｡･∀･)ﾉﾞ嗨', '']
    #     df = self.readcsv('data')
    #     to_be_reposted = df
    #     num = 0
    #     length = len(repostword) - 1
    #     for item in to_be_reposted.iterrows():
    #         if item[1][8] == 0:
    #             rid = item[1][0]
    #             user.set_subscribe(uid=item[1][1], verify=self.verify)  # 关注 + 转发
    #             to_be_reposted.loc[to_be_reposted[to_be_reposted['rid'].isin([rid])].index[0], '是否已转发'] = '1'
    #             dynamic.repost(dynamic_id=rid, text=repostword[random.randint(0, length)],
    #                            verify=self.verify)  # 转发
    #             user.move_user_subscribe_group(uid=item[1][1], group_ids=self.tagid, verify=self.verify)
    #             time.sleep(random.randint(30, 180))
    #             num = num + 1
    #     # print(to_be_reposted)
    #     to_be_reposted.to_csv("%s\\data.csv" % self.folder_path, index=False, encoding="GB18030", float_format='str')
    #     # df = self.readcsv('data')
    #     # print('\n\n')
    #     # print(df)
    #     return num

    def repost_list(self, to_be_reposted):
        random.seed()
        repostword = ['感谢感谢！！！欧皇就是我本人 提前恭喜这个b     站用户', '大手笔', '希望中奖', '冲冲冲', '能邮过来让我康康吗',
                      '别转了 昨晚up说内定我了', '中！', '热乎的', '好多人啊', '这么多中奖活动都抽过，虽然没有中过但从来没放弃',
                      '从未中奖，从未放弃', '我可以拥有的！', '中一次呗', '万一呢', '祝我好运', '抽我！', '(=・ω・=)', '加油',
                      '还走什么流程啊，直接寄不就好了？', '转转转', '就让我来当个分母吧', '我该选哪个呢', '我来', '试一试', '好耶！',
                      '人与人的体质是不能相提并论的，我曾在极度愤怒的情况下暴转了一万条互动抽奖，又在极度暴怒的情况下成了柠檬精',
                      '重在参与', '拉低中奖率', '啊这', '分母集合', '下次一定中', '欧克欧克', '中奖是不可能中奖的 这辈子都不可能的',
                      '从未中，从未停', '中奖绝缘体', '好家伙', '老板大气', '我要白嫖', '我要', '这牛啊', '奥力给', '非酋9段的第1761！！！次实验',
                      '我要中啦', '我最喜欢这个了,我也想要', '秋梨膏', '啊啊啊啊啊啊啊啊啊啊啊', '大家都散了吧，已经抽完了，是我的',
                      '众所周知是抽奖有黑幕的，如果没有敢不敢抽到我', '看看我吧', '求一个！哈哈哈', '转发动态', '我的我的还是我的', 'ヾ(•ω•`)o',
                      '\\(@^0^@)/', '(｡･∀･)ﾉﾞ嗨', '']
        df = self.readcsv('data')
        sub = self.readcsv('subscribe')
        df.loc[df['是否已转发'] == 0, '是否已转发'] = -1
        if '转发rid' not in df.columns:
            df['转发rid'] = ''
        num = 0
        length = len(repostword) - 1
        for item in to_be_reposted:
            rid = item.split(',')[0]
            uid = item.split(',')[1]
            if sub[sub["uid"].isin([int(uid)])].empty:      # 用户不在非抽奖列表中，关注 + 转发
                user.set_subscribe(uid=uid, verify=self.verify)
                df.loc[df[df['rid'].isin([int(rid)])].index[0], '是否已转发'] = 1
                dynamic.repost(dynamic_id=rid, text=repostword[random.randint(0, length)],
                               verify=self.verify)  # 转发
                user.move_user_subscribe_group(uid=uid, group_ids=self.tagid, verify=self.verify)
            else:                                           # 在，只转发
                df.loc[df[df['rid'].isin([int(rid)])].index[0], '是否已转发'] = 1
                dynamic.repost(dynamic_id=rid, text=repostword[random.randint(0, length)],
                               verify=self.verify)
            time.sleep(1)
            repost_rid = user.get_dynamic(self.uid, limit=1, verify=self.verify)
            repost_rid = repost_rid[0]['desc']['dynamic_id']
            df.loc[df[df['rid'].isin([int(rid)])].index[0], '转发rid'] = str(repost_rid)
            time.sleep(random.randint(30, 180))
            num = num + 1
        time.sleep(1)
        df.to_csv("%s\\data.csv" % self.folder_path, index=False, encoding="GB18030")  # , float_format='str'
        return num

    def get_subscribe(self):
        f = user.get_followings(uid=self.uid, verify=self.verify)
        self.overwritecsv('subscribe', ["uid", "用户名"])
        for item in f:
            g = user.get_user_in_which_subscribe_groups(uid=item['mid'], verify=self.verify)
            if g and (list(g.keys())[0] == '%s' % self.tagid[0]):
                continue
            self.writecsv('subscribe', [item['mid'], item['uname']])


# basic = Basic()
# path = basic.folder_path()
# verify = basic.verify(sessdata="4a6ceb3a%2C1626099556%2C7e8f7*11", csrf="e98cb389ea19df8d2b62d2f53d501ab3")
# basicinfo = {'uid': 12311708, 'folder_path': path, 'verify': verify, 'tagid': [329352]}
# BLottery = BiliLottery(basicinfo)  # 创建类的实例
# repost_rid = user.get_dynamic(12311708, limit=1, verify=verify)
# repost_rid = repost_rid[0]['desc']['dynamic_id']
# print(repost_rid)
# df = BLottery.readcsv('data')
# # print(df[df['rid'].isin([int(485955676732677313)])])
# df.loc[df[df['rid'].isin([int(485955676732677313)])].index[0], '转发rid'] = repost_rid
# for line in df.iterrows():
#     print(line)
# df.to_csv("%s\\data.csv" % path, index=False, encoding="GB18030", float_format='str')
# BLottery.get_subscribe()

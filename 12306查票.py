import requests
import re
import time
import itchat
import calendar

headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 '
                      'Safari/537.36'
    }
class Ticket_Query(object):
    # 获取车站名称及对应简称
    def msg_station(self):
        response = requests.get('https://kyfw.12306.cn/otn/resources/js/framework/station_name.js?station_version'
                                '=1.8392', headers=headers)
        station_list = response.text.split('|')
        station_dict = {}
        i = 1
        while True:
            try:
                station_dict[station_list[i]] = station_list[i+1]
                i += 5
            except IndexError:
                break
        return station_dict

    # 避免中英文打印对不齐的问题
    def align(self, str1, distance=12, alignment='left'):
        length = len(str1.encode('gbk'))
        space_to_fill = distance - length if distance > length else 0
        if alignment == 'left':
            str1 = str1 + ' '* space_to_fill
        elif alignment == 'right':
            str1 = ' ' * space_to_fill + str1
        elif alignment == 'center':
            str1 = ' ' * (distance // 2) + str1 + ' ' * (distance - distance // 2)
        return str1

    def add_zero(self, data):
        if len(data) == 4:
            data = '0' + data
        if len(data) == 1:
            data = '0' + data + ':00'
        if len(data) == 2:
            data = data + ':00'
        return data

    # 设置出发日期
    def set_day(self):
        try:
            self.date = input("请输入您的出发日期（例：3-1,直接按回车则为当日）:")
            if self.date == '':
                self.date = time.strftime('%m-%d', time.localtime(time.time()))
            t = self.date.split('-')
            try:
                self.which_weekday = calendar.weekday(2019, int(t[0]), int(t[1]))
                if self.which_weekday == 0:
                    self.which_weekday = '周一'
                if self.which_weekday == 1:
                    self.which_weekday = '周二'
                if self.which_weekday == 2:
                    self.which_weekday = '周三'
                if self.which_weekday == 3:
                    self.which_weekday = '周四'
                if self.which_weekday == 4:
                    self.which_weekday = '周五'
                if self.which_weekday == 5:
                    self.which_weekday = '周六'
                if self.which_weekday == 6:
                    self.which_weekday = '周日'

                if len(t[0]) == 1:
                    t[0] = '0' + t[0]
                if len(t[1]) == 1:
                    t[1] = '0' + t[1]
                self.date = t[0] + '-' + t[1]
                url = 'https://kyfw.12306.cn/otn/leftTicket/query?leftTicketDTO.train_date=2019-' + self.date + \
                      '&leftTicketDTO.from_station=' + self.start_short + '&leftTicketDTO.to_station=' + \
                      self.end_short + '&purpose_codes=ADULT'
                response = requests.get(url, headers=headers)

                if response.json()['data']['result'] == []:
                    print('很抱歉，按您的查询条件，当前未找到从{0} 到{1} 的列车。'.format(self.start, self.end))
                    self.set_place()
                self.q = response.json()['data']['result']
            except ValueError:
                print("您输入的日期有误，请您核对后重新输入")
                self.set_day()
        except Exception as e:
            print(e)
            print("您输入的日期有误，请您核对后重新输入")
            self.set_day()

    # 设置出发时间段
    def time_selection(self):
        t = input("请输入您的出发时间段，如不进行设置请直接按回车键(例：5-14，8:24-13:20, 0:00-24:00):")
        if t == '':
            self.is_set_time = 0
            return None
        tt = t.split('-')
        try:
            tt[0] = self.add_zero(tt[0])
            tt[1] = self.add_zero(tt[1])

            # 防止用户输入的冒号为中文符
            if tt[0][2] == ':':
                tt_start = tt[0].split(':')
            if tt[0][2] == '：':
                tt_start = tt[0].split('：')

            if tt[1][2] == ':':
                tt_end = tt[1].split(':')
            if tt[1][2] == '：':
                tt_end = tt[1].split('：')

            self.set_gotime_start = tt_start[0] + ':' + tt_start[1]
            self.set_gotime_end = tt_end[0] + ':' + tt_end[1]
            if self.date + ' ' + self.set_gotime_end < time.strftime('%m-%d %H:%M', time.localtime(time.time())):
                self.is_set_time = 0
                print("请勿输入过去时间")
                self.time_selection()
            if self.set_gotime_start > self.set_gotime_end:
                raise Exception()
            else:
                self.is_set_time = 1
            return None
        except:
            print("您输入的出发时间段有误，请重新输入")
            self.time_selection()

    # 设置座位类型
    def seat_selection(self):
        msg_seat = input("请输入您要乘坐的座位（二等座，一等座，商务座，硬座，硬卧，软卧，高级软卧，动卧，无座)，"
                         "可选择多个，中间以逗号隔开，如不选择请按回车（例如：二等座，一等座）：")
        all_seat = ['二等座', '一等座', '商务座', '硬座', '硬卧', '软卧', '高级软卧', '动卧', '无座']
        # global seat, is_seat_selection
        if msg_seat == '':
             self.is_seat_selection = 0
             return None
        self.seat = re.split('[,， ]', msg_seat)
        if (set(self.seat) <= set(all_seat)) == False:
            print("您输入的座位有误，请重新输入")
            self.seat_selection()
        else:
            self.is_seat_selection = 1

    # 设置查询间隔时间
    def set_search_period(self):
        try:
            self.search_period = input("请输入您的查询时间间隔（例：1s, 1min, 1h，连续不间断查询则输入0）：")
            i = 0
            for each in self.search_period:
                if each == 's':
                    self.search_period = self.search_period[0:i]
                if each == 'm':
                    self.search_period = float(self.search_period[0:i]) * 60
                if each == 'h':
                    self.search_period = float(self.search_period[0:i]) * 3600
                i += 1
            self.search_period = float(self.search_period)
            if self.search_period < 0:
                raise Exception
        except:
            print("您输入的查询时间间隔有误，请重新输入")
            self.set_search_period()

    def display(self):
        if self.is_set_time == 0:
            self.set_gotime_start = '00:00'
            self.set_gotime_end = '24:00'
        print("*" * 170)
        if self.is_seat_selection == 0:
            self.seat = ['二等座', '一等座', '商务座', '硬座', '硬卧', '软卧', '高级软卧', '动卧', '无座']

        print("您查看的火车为    2019-{0:8}{6:6}{1:>5}==>{2:<5}      出发时间为{3}-{4}      选择的座位为{5}".
              format(self.date, self.start, self.end, self.set_gotime_start, self.set_gotime_end, self.seat,
                     self.which_weekday))
        search_time = 1
        isallticket = 0
        time_seat_setting = False# 防止用户设置时间内根本没有车的情况,True表示正常

        while isallticket == 0:
            # 判断所有列车是否有票
            for i in self.q:
                tem_list = i.split('|')
                train_num = {}
                train_num['出发时间'] = tem_list[8]
                if train_num['出发时间'] >= self.set_gotime_start and train_num['出发时间'] <= self.set_gotime_end:
                    pass
                else:
                    continue

                ticket = {}
                ticket['二等座'] = tem_list[30]
                ticket['一等座'] = tem_list[31]
                ticket['商务座'] = tem_list[32]
                ticket['硬座'] = tem_list[29]
                ticket['硬卧'] = tem_list[28]
                ticket['软卧'] = tem_list[23]
                ticket['高级软卧'] = tem_list[21]
                ticket['动卧'] = tem_list[33]
                ticket['无座'] = tem_list[26]

                # 判断是否有票
                for k, v in ticket.items():
                    if k in self.seat:
                        if v == '':
                            pass
                        elif v == '无':
                            time_seat_setting = True
                        else:
                            time_seat_setting = True
                            isallticket = 1
                            break

            if time_seat_setting == False:
                print("您选择的时间段内无相应座位列车，请您核对后重新设置时间和座位")
                self.display()
                break

            now = time.strftime('%H:%M:%S', time.localtime(time.time()))
            print("{1}  第{0}次查询结果为:".format(search_time, now))
            search_time += 1
            if isallticket == 0:
                print("对不起，您查看的车票暂时没有")
                time.sleep(self.search_period)
            else:
                itchat.send('您查询的以下列车有票，请您尽快至12306官方购买', 'filehelper')
                print(self.align('车次'), self.align('出发站'), self.align('到达站'), self.align('出发时间'),
                      self.align('到达时间'), self.align('历时'), end='')
                for i in self.seat:
                    print(self.align(i), end='')
                print('')

                for i in self.q:
                    tem_list = i.split('|')
                    # 给每个数据做标记，3是车次，4是起点缩写，5是终点缩写，6是乘客起点，7是乘客终点8是出发时间，
                    # 9是到达时间，10是用时，13是日期，30是二等座，31是一等座，32是商务特等座，23为软卧一等卧，26为无座
                    # 21为高级软卧，29为硬座，28为硬卧二等卧，33为动卧
                    train_num = {}
                    train_num['出发时间'] = tem_list[8]
                    if train_num['出发时间'] >= self.set_gotime_start and train_num['出发时间'] <= self.set_gotime_end:
                        pass
                    else:
                        continue

                    train_num['车次'] = tem_list[3]
                    train_num['起点'] = list(self.station_dict.keys())[list(self.station_dict.values()).
                        index(tem_list[6])]
                    train_num['终点'] = list(self.station_dict.keys())[list(self.station_dict.values()).
                        index(tem_list[7])]
                    train_num['到达时间'] = tem_list[9]
                    train_num['用时'] = tem_list[10]
                    train_num['日期'] = tem_list[13]

                    ticket = {}
                    ticket['二等座'] = tem_list[30]
                    ticket['一等座'] = tem_list[31]
                    ticket['商务座'] = tem_list[32]
                    ticket['硬座'] = tem_list[29]
                    ticket['硬卧'] = tem_list[28]
                    ticket['软卧'] = tem_list[23]
                    ticket['高级软卧'] = tem_list[21]
                    ticket['动卧'] = tem_list[33]
                    ticket['无座'] = tem_list[26]

                    # 判断本次列车是否有票
                    for k, v in ticket.items():
                        if k in self.seat:
                            if v == '' or v == '无':
                                isthisticket = 0
                            else:
                                isthisticket = 1
                                break

                    if isthisticket == 0:
                        continue

                    for k, v in ticket.items():
                        if v == '':
                            ticket[k] = '-'

                    if train_num['出发时间'] > train_num['到达时间']:
                        train_num['到达时间'] = '次日' + train_num['到达时间']
                    print(self.align(train_num['车次']), self.align(train_num['起点']), self.align(train_num['终点']),
                          self.align(train_num['出发时间']),
                          self.align(train_num['到达时间']), self.align(train_num['用时']), end='')
                    for i in self.seat:
                        print(self.align(ticket[i]), end='')
                    print('')
                    itchat.send('车次：' + train_num['车次'] + '\r\n起点：' + train_num['起点'] + '\r\n终点：' +
                                train_num['终点'] + '\r\n出发时间：' + train_num['出发时间'] + '\r\n到达时间：' +
                                              train_num['到达时间'], 'filehelper')

    # 设置起点及终点
    def set_place(self):
        # 获取车站名称及对应简称
        self.station_dict = self.msg_station()
        self.start = input("请输入您的出发地(例:北京):")
        self.end = input("请输入您的终点地:")
        try:
            self.start_short = self.station_dict[self.start]
            self.end_short = self.station_dict[self.end]
        except KeyError:
            print("您输入的地点有误，请重新输入")
            self.set_place()

if __name__ == '__main__':
    itchat.auto_login(hotReload=True)
    print("--------欢迎登录使用12306查票系统--------\r\n本系统可实现连续自动查票功能，并可自主选择您的出行时间"
          "及座位类型，当查询到您所需要的票时，会自动将车票信息发送至您的微信文件传输助手提醒。")
    is_continue_search = 'Y'
    train_ticket = Ticket_Query()
    while is_continue_search == 'y' or is_continue_search == 'Y':
        train_ticket.set_place()    # 设置出发地及目的地
        train_ticket.set_day()  # 设置出发日期
        train_ticket.time_selection()   # 设置出发时间
        train_ticket.seat_selection()   # 设置座位
        train_ticket.set_search_period()    # 设置查询间隔时间
        train_ticket.display()  # 进行查询
        is_continue_search = input("您需要继续查询吗？Y/N：")




 
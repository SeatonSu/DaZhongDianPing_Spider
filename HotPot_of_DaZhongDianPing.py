# -*- coding:utf-8 -*-
"""
爬取大众点评上的所有火锅店的以下内容：
店名、点评人数、价格、地址
"""
import re
import requests
from bs4 import BeautifulSoup
import sys
import xlwt
import datetime
reload(sys)
sys.setdefaultencoding("utf-8")


# 获取大众点评上火锅店的网页数据，以便下一步解析
def get_result_of_url():
    result_of_url = []
    headers = {
        'Host': 'www.dianping.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Langeuage': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept- Encoding': 'gzip, deflate, br',
        'Cookie': 'cy=94; cye=nantong; _hc.v=68b4fbb9-fd71-7146-3534-499b7d14a6a7.1493085400; __utma=1.121961894.1493085400.1493085400.1493085400.1; __utmz=1.1493085400.1.1.utmcsr=baidu|utmccn=(organic)|utmcmd=organic; JSESSIONID=D709DC6EB4C09B733E492FE6443E2783; s_ViewType=10; aburl=1; PHOENIX_ID=0a01678e-15ba3a54e39-de5b6f4',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    print "开始爬取相关网页"
    for i in range(1, 51):
        url = ('http://www.dianping.com/search/category/94/10/g110p{0}'
               '?aid=73563184%2C90313819%2C69713380%2C22000250%2C67431668%2C13897853'.format(i))
        result_of_url.append(requests.get(url, headers=headers).content)
    print "爬取网页完成，共%d个相关网页" % len(result_of_url)
    return result_of_url


# 挖掘网页数据中的关键数据
def parser_result_of_url(content, i):
    soup = BeautifulSoup(content, 'lxml')
    p_shop = soup.find_all('div', class_='tit')
    shop_li = []
    addr_general_li = []
    addr_detail_li = []
    for sibling in p_shop:
        # 判断tag中是否有a标签
        if sibling.a:
            shop_li.append(sibling.a['title'])
    p_addrs = soup.find_all("div", class_='tag-addr')
    for p_addr in p_addrs:
        addr_general = p_addr.select('span[class="tag"]')[1].string
        addr_detail = p_addr.select('span[class="addr"]')[0].string
        addr_general_li.append(addr_general)
        addr_detail_li.append(addr_detail)
    # 合并数据
    HotPot_Shop = zip(shop_li, addr_general_li, addr_detail_li)
    for item in HotPot_Shop:
        item = list(item)
        # print "%s   %s    %s" % (item[0], item[1], item[2])
    print "第%d个解析网页完成" % i
    return HotPot_Shop


# 获取输入地区坐标
def get_coordinate(address="南大街文峰大世界8楼"):
    url = 'http://api.map.baidu.com/geocoder/v2/'
    city = '南通市'
    # address = address
    ret_coordtype = 'gcj02ll'
    ak = 'YvOiLofaKxbTC7bEwT3BnwUOS5uynSAe'
    params = {
        'city': city,
        'address': address,
        'ak': ak,
        'ret_coordtype': ret_coordtype,
        # 'output': 'xml'
        'output': 'json'
    }
    r = requests.get(url=url, params=params)
    # API调用结果
    result_of_API = r.content
    # print result_of_API
    # 正则表达式
    pattern = re.compile(r'.*?"lng":(.*?),"lat":(.*?)}.*?"level":"(.*?)".*')
    result_of_search = pattern.search(result_of_API)
    if result_of_search:
        (lng, lat, land_type) = result_of_search.group(1), result_of_search.group(2), result_of_search.group(3)
        print 'lng: ', lng, " "*8, 'lat: ', lat, " "*8, "land_type: ", land_type
        result = (lng, lat)
        return result
    else:
        result = (0, 0)
        return result


# 根据百度API获取火锅店的坐标，将坐标数据添加到原列表中，返回完整的火锅信息列表
def get_hotpot_coordinate(HotPot_Shop):
    print "开始调用百度API获取火锅店经纬度"
    coordinate = []
    for each_item in HotPot_Shop:
        s = get_coordinate(each_item[0])
        if s != (0, 0):
            coordinate.append(s)
        elif get_coordinate(each_item[2]) != (0, 0):
            coordinate.append(get_coordinate(each_item[0]))
        else:
            coordinate.append(get_coordinate(each_item[1]))
    HotPot_Shop = zip(HotPot_Shop, coordinate)
    result = []
    result_error = []
    for each_item in HotPot_Shop:
        # 删除列表中没有找到坐标的
        if not (each_item[1][0] == 0 and each_item[1][1] == 0):
            sub_result = each_item[0] + each_item[1]
            result.append(sub_result)
        else:
            result_error.append("%s   %s   %s\n" % (each_item[0][0], each_item[0][1], each_item[0][2]))
    try:
        text = open("NoCoordinateHotPot.txt", "w")
        for i in range(len(result_error)):
            text.write(result_error[i])
    finally:
        text.close()
    print "经纬度获取完毕"
    return result


# 将文件写入excel表中
def save_result(HotPot_Shop):
    wb = xlwt.Workbook()
    ws = wb.add_sheet("test2")
    print "开始写入"
    ws.write(0, 0, u"店名")
    ws.write(0, 1, u"区位")
    ws.write(0, 2, u"地址")
    ws.write(0, 3, u"经度")
    ws.write(0, 4, u"纬度")
    for i in range(len(HotPot_Shop)):
        for j in range(len(HotPot_Shop[i])):
            ws.write(i+1, j, HotPot_Shop[i][j])
        print "第%d条记录写入完成" % i
    wb.save("test2.xls")
    print "写入完成"


if __name__ == '__main__':
    starttime = datetime.datetime.now()
    content = get_result_of_url()
    HotPot_Shop = []
    i = 1
    for each_item in content:
        HotPot_Shop += parser_result_of_url(each_item, i)
        i += 1
    result = get_hotpot_coordinate(HotPot_Shop)
    save_result(result)
    endtime = datetime.datetime.now()
    print "运行结束"
    print "共耗时{0}秒".format((endtime - starttime).seconds)
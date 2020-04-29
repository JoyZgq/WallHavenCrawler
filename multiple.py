# -*- coding: utf-8 -*-
# wallhaven爬取
import os
from urllib.parse import urlencode
from requests import codes
import random
import requests
import threading # 导入threading模块
from queue import Queue #导入queue模块
import time  #导入time模块
from lxml import etree


# 定义创建文件路径函数，将下载的文件存储到该路径
def CreatePath(filepath):
    if not os.path.exists(filepath):
        os.makedirs(filepath)


# 定义获取url函数，这里是通过urlencode方法把url的各个部分拼接起来的，拼接起来的url
# 像是这样的：https://wallhaven.cc/search?q=girls&categories=111&purity=110&sorting=toplist&order=desc
def GetUrl(keyword, category):
    params = {
        'q': keyword,
        'categories': category,
        'purity': '111',  # 100\010\110
        'sorting': 'favorites',  # relevance\random\date_added\views\favorites\toplist\toplist-beta
        'topRange': '1y',  # 1y\6M\3M\1w\3d\1d
        # 'atleast':'1920x1080',
        'order': 'desc'
    }
    base_url = 'https://wallhaven.cc/search?'
    url = base_url + urlencode(params)
    print(url)
    return url


# 获取查找到的图片数
def GetPictureNum(url):
    allpic = " "
    try:
        html = requests.get(url)
        if codes.ok == html.status_code:
            selector = etree.HTML(html.text)
            pageInfo = selector.xpath('//header[@class="listing-header"]/h1[1]/text()')  # 提取出文本
            string = str(pageInfo[0])  # 图片数是文本中的第一个
            numlist = list(filter(str.isdigit, string))  # 有些数字是这样的，11,123,所以需要整理。
            for item in numlist:
                allpic += item
            totalPicNum = int(allpic)  # 把拼接起来的字符串进行整数化
            return totalPicNum
    except requests.ConnectionError:
        return None


# 获取图片链接
def GetLinks(url, number):
    urls = url + '&page=' + str(number)
    try:
        html = requests.get(urls)
        selector = etree.HTML(html.text)
        PicLink = selector.xpath('//a[@class="preview"]/@href')  # 这里寻找图片的链接地址，以求得到图片编号
    except Exception as e:
        print('Error', e.args)
    return PicLink


# 下载函数
def Download(filepath, keyword, url, count, headers):  # 其中count是你要下载的图片数
    # 此函数用于图片下载。其中参数url是形如：https://wallhaven.cc/w/eyyoj8 的网址
    # 因为wallheaven上只有两种格式的图片，分别是png和jpg，所以设置两种最终地址HtmlJpg和HtmlPng，通过status_code来进行判断，状态码为200时请求成功。
    string = url.replace('https://wallhaven.cc/w/', '')  # python3 replace
    # print(string)
    HtmlJpg = 'https://w.wallhaven.cc/full/' + string[0:2] + '/wallhaven-' + string + '.jpg'
    HtmlPng = 'https://w.wallhaven.cc/full/' + string[0:2] + '/wallhaven-' + string + '.png'

    try:
        pic = requests.get(HtmlJpg, headers=headers)
        if codes.ok == pic.status_code:
            pic_path = filepath + 'wallhaven-' + string + '.jpg'
        else:
            pic = requests.get(HtmlPng, headers=headers)
            if codes.ok == pic.status_code:
                pic_path = filepath + 'wallhaven-' + string + '.png'
            else:
                print("Downloaded error:", string)
                return
        with open(pic_path, 'wb') as f:
            f.write(pic.content)
            f.close()
        print("Downloaded image:", string)
        time.sleep(random.uniform(0, 3))  # 这里是让爬虫在下载完一张图片后休息一下，防被侦查到是爬虫从而引发反爬虫机制。

    except Exception as e:
        print(repr(e))

def urlQueue(pageStart,pageNum,url,queue):
    for i in range(pageStart, pageNum):
        PicUrl = GetLinks(url, i + 1)
        for item in PicUrl:
            queue.put(item)
            # print(item)
            # Download(filepath, keyword, item, j, headers)
            # j += 1
            # if (j > Num):  # 如果你下载的图片够用了，那就直接退出循环，结束程序。

def getdetail(filepath,keyword,Num,detail_url_queue, headers,i):
    j=1
    while True:
        item=detail_url_queue.get()

        Download(filepath, keyword, item,j, headers)
        print("thread {id}:download finished".format(id=id))  # 打印线程id和被爬取了文章内容的url
        j += 1
        # if (j > Num):  # 如果你下载的图片够用了，那就直接退出循环，结束程序。


    # 主函数


def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5)\
        AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.104 Safari/537.36",  # 请求头，这个可以通过查看你自己的浏览器得到。
    }
    filepath = ('E:/wallpaper/Multiple/')  # 存储路径。
    keyword = input('请输入关键词:')
    category = input('请输入图片分类，共有三种，分别为Gneral,Anime,People三种\
                   ，如果你想要只想选择Anime，就键入010,如果全选就键入111,以此类推:')
    theadnumber=input('请输入线程数:')
    CreatePath(filepath)  # 创建保存路径
    url = GetUrl(keyword, category)  # 获取url

    PicNum = GetPictureNum(url)  # 总图片数
    pageNum = int(PicNum / 24 + 1)  # 求出总页面数
    print("We found:{} images.".format(PicNum))

    # j = 1
    Arr = input("请输入你想要爬的图片数，不能超过已找到的图片数:【若要设定其实页码用|分割，如：50|10(即从第10页开始，取50个)】").split('|')
    Num = int(Arr[0])
    pageStart = 0

    if (len(Arr) == 2):
        pageStart = int(Arr[1])
    detail_url_queue = Queue(maxsize=1000)  # 用Queue构造一个大小为1000的线程安全的先进先出队列
    # 先创造四个线程
    thread = threading.Thread(target=urlQueue, args=(pageStart,pageNum,url,detail_url_queue,))  # A线程负责抓取列表url
    html_thread = []
    for i in range(int(theadnumber)):
        thread2 = threading.Thread(target=getdetail, args=(filepath,keyword,Num,detail_url_queue, headers,i))
        html_thread.append(thread2)  # B C D 线程抓取文章详情
    # 启动四个线程
    thread.start()
    for i in range(int(theadnumber)):
        html_thread[i].start()
    # 等待所有线程结束，thread.join()函数代表子线程完成之前，其父进程一直处于阻塞状态。
    thread.join()
    for i in range(int(theadnumber)):
        html_thread[i].join()


    # for i in range(pageStart, pageNum):
    #     PicUrl = GetLinks(url, i + 1)
    #     for item in PicUrl:
    #         # print(item)
    #         Download(filepath, keyword, item, j, headers)
    #         j += 1
    #         if (j > Num):  # 如果你下载的图片够用了，那就直接退出循环，结束程序。
    #             return


if __name__ == '__main__':
    main()

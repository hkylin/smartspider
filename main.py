# -*- coding:utf-8 -*-

import urllib2
import re
import time
import mysql
import sys
import os
from bs4 import BeautifulSoup

class Spider:
    
    #初始化
    def __init__(self):
        self.total_num = None
        self.path = os.getcwd()
        self.mysql = mysql.Mysql()
        
    #获取当前时间
    def getCurrentTime(self):
        return time.strftime('[%Y-%m-%d %H:%M:%S]',time.localtime(time.time()))
    
    #获取当前时间
    def getCurrentDate(self):
        return time.strftime('%Y-%m-%d',time.localtime(time.time()))
    
    #通过网页的页码数来构建网页的URL
    def getPageURLByNum(self, page_num):
        page_url = "http://www.smartshanghai.com/listings/all/?page=" + str(page_num)
        return page_url
    
    
    #通过传入网页页码来获取该页面的HTML
    def getPageByNum(self, page_num):
        header = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'}
        timeout = 20
        request = urllib2.Request(self.getPageURLByNum(page_num),None,header)
        try:
            response = urllib2.urlopen(request,None,timeout)
        except urllib2.URLError, e:
            if hasattr(e, "code"):
                print self.getCurrentTime(),"获取list页面失败,错误代号", e.code
                return None
            if hasattr(e, "reason"):
                print self.getCurrentTime(),"获取list页面失败,原因", e.reason
                return None
        else:
            page =  response.read().decode("utf-8")
            return page
    
    #获取所有的页码数
    def getTotalPageNum(self):
        print self.getCurrentTime(),"正在获取目录页面个数,请稍候"
        url = "http://www.smartshanghai.com/listings/all"
        header = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'}
        timeout = 20
        request = urllib2.Request(url,None,header)
        try:
            response = urllib2.urlopen(request,None,timeout)
        except urllib2.URLError, e:
            if hasattr(e, "code"):
                print self.getCurrentTime(),"获取目录页面个数失败,错误代号", e.code
                return None
            if hasattr(e, "reason"):
                print self.getCurrentTime(),"获取目录页面个数失败,原因", e.reason
                return None
        else:
            content = response.read().decode("utf-8")
            soup = BeautifulSoup(content)
            total_num = soup.find(class_="pagination").find_all("li")[4].a["href"].split("=")[1]
            print "获取成功，页面个数为：%s" % total_num
            return total_num
    
    #获取当前页面venue的url,返回venue的URL列表
    def getCurrentPageURL(self,page_num):
        #获取当前页面的HTML
        page = self.getPageByNum(page_num)
        soup = BeautifulSoup(page)
        #分析该页面
        venues = soup.find(class_="venues listings").find_all("li",recursive=False)
        return [venue.a["href"] for venue in venues]

    #获取venue的网页的HTML
    def getVenuePageByURL(self,venue_url):
        header = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'}
        timeout = 20
        request = urllib2.Request(venue_url,None,header)
        try:
            response = urllib2.urlopen(request,None,timeout)
        except urllib2.URLError, e:
            if hasattr(e, "code"):
                print self.getCurrentTime(),"获取venue页面信息失败,错误代号", e.code
                return None
            if hasattr(e, "reason"):
                print self.getCurrentTime(),"获取venue页面信息失败,原因", e.reason
                return None
        else:
            venue_page = response.read().decode("utf-8")
            return venue_page                 

    #获取venue信息，返回文字信息列表
    def getVenueInfo(self, venue_page):
        soup = BeautifulSoup(venue_page)
        venue_name = soup.find(class_="dabiaoti").string.strip()#得到venue的名称
        
        #匹配百度地图位置
        latitude = ""
        longitude = ""
        scripts = soup.find_all("script")
        for script in scripts:
            result = re.match("(.*)(latitude = )(\d+.\d+)", script.get_text(), re.DOTALL)
            if result != None:
                latitude = result.group(3)
                longitude = re.match("(.*)(longitude = )(\d+.\d+)", script.get_text(), re.DOTALL).group(3)
        tags = []
        tags_a = soup.find(class_="lianjie").find_all("a")
        if tags_a != None:
            tags = [tag.string for tag in tags_a]
        img_links = []
        img_divs = soup.find(class_="photos")
        if img_divs != None:
            img_divs = img_divs.find_all("li")
            if img_divs != None and len(img_divs) != 0:
                #获取Img下载链接
                img_links = [img_div.a.img.get('src') for img_div in img_divs]
                #url去重
                img_links = list(set(img_links))
        xinxi = soup.find(class_="xinxi").find_all("li")
        #存储到数据库的所有字段

        address = ""
        phone = ""
        area = ""
        metro = ""
        hours = ""
        cards = ""
        price = ""
        web = "" 
        happy_hour = "" 
        description = ""
              
        for shuxin in xinxi:
            #区分shuxin和jianjie
            key = ""
            value = ""
            if shuxin.div["class"][0] == "shuxin":
                key = shuxin.div.string
                value = shuxin.find(class_="wenzi").get_text().strip()
            else :
                key = shuxin.find(class_="biaoti").string
                if shuxin.div.span != None:
                    value = shuxin.div.span.get_text().strip()

            #判断字段名称，并根据字段名称获取相关字段内容，对内容要进行格式处理
            if key == " ADDRESS: ":
                address = ''.join(tuple([old_value.strip() for old_value in value.split('\n')]))
            elif key == " PHONE: ":
                phone = '-'.join(value.split(' '))
            elif key == " AREA: ":
                area = value
            elif key == " METRO: ":
                metro = value
            elif key == " HOURS: ":
                hours = value
            elif key == " CARDS: ":
                cards = value
            elif key == " WEB: ":
                web = value
            elif key == "SmartShanghai.com Editor's Description":
                description = value
            elif key == " HAPPY HOUR: ":
                happy_hour = value
            elif key==" PRICE: ":
                price = value
            else:
                break
        return [venue_name, address, phone, area, metro, hours, cards, web, happy_hour, price, description, tags, img_links, latitude, longitude]
        
    #得到所有的venue信息
    def getVenues(self, page_num):
        venue_urls = self.getCurrentPageURL(page_num)
        for venue_num in range(len(venue_urls)):
            print self.getCurrentTime(),"正在抓取第", str(venue_num+1), "个venue"
            venue_page = self.getVenuePageByURL(venue_urls[venue_num])
            venue_info = self.getVenueInfo(venue_page)
            #构建venue文字信息字典
            venue_dict = {
                "venue_name": venue_info[0],
                "address": venue_info[1],
                "phone": venue_info[2],
                "area": venue_info[3],
                "metro": venue_info[4],
                "hours": venue_info[5],
                "cards": venue_info[6],
                "web": venue_info[7],
                "happy_hour": venue_info[8],
                "price": venue_info[9],
                "description": re.sub('["()]', '_', venue_info[10]),
                "latitude": venue_info[13],
                "longitude": venue_info[14]
            }
            #获得插入venue的自增ID
            vinsert_id = self.mysql.insertData("venue", venue_dict)
            print self.getCurrentTime(), "保存到数据库，此venue的ID为", vinsert_id
            
            if venue_info[11] != None and len(venue_info[11]) > 0:
                for i in range(len(venue_info[11])):
                    venue_tag_dict = {
                        "venue_name": venue_info[0],
                        "tag_name": venue_info[11][i]
                    }
                    vtinsert_id = self.mysql.insertData("venue_tag", venue_tag_dict)
                    print self.getCurrentTime(), "保存到数据库，此venue_tag的ID为", vtinsert_id
                
                for j in range(len(venue_info[11])):
                    tag_dict = {
                        "tag_name": venue_info[11][j]
                    }
                    #获得插入tag的id
                    tinsert_id = self.mysql.insertData("tags", tag_dict)
                    print self.getCurrentTime(), "保存到数据库，此tag的ID为", tinsert_id    
            img_links = venue_info[12]
            if img_links != None and len(img_links) != 0 :
                img_path = os.path.join(self.path, u'smartshanghai\\' + re.sub('/', '_', venue_info[0]))
                os.mkdir(img_path)
                for link in img_links:
                    try:
                        img_content = urllib2.urlopen(link).read()
                    except urllib2.URLError, e:
                        if hasattr(e, "code"):
                            print self.getCurrentTime(),"获取图片信息失败,错误代号", e.code
                        if hasattr(e, "reason"):
                            print self.getCurrentTime(),"获取图片信息失败,原因", e.reason
                        continue
                    else:
                        try:
                            with open(img_path + '\\' + link.split('/')[-1], 'wb') as code:
                                code.write(img_content)      
                        except IOError, e:
                            if hasattr(e, "code"):
                                print self.getCurrentTime(),"获取图片信息失败,错误代号", e.code
                            if hasattr(e, "reason"):
                                print self.getCurrentTime(),"获取图片信息失败,原因", e.reason
                            continue
        
    #主函数
    def main(self):
        # 创建文件夹
        new_path = os.path.join(self.path,u'smartshanghai')  
        if not os.path.isdir(new_path):  
            os.mkdir(new_path)  
        f_handler=open('out.log', 'w') 
        sys.stdout=f_handler
        if not os.path.exists('page.txt'):
            f = open('page.txt', 'w')
            f.write('1')
            f.close()
        page = open('page.txt', 'r')
        content = page.readline()
        print page, content
        start_page = int(content.strip())
        page.close()     
        print self.getCurrentTime(),"开始页码",start_page
        print self.getCurrentTime(),"爬虫正在启动,开始爬取smartshanghai"
        self.total_num = self.getTotalPageNum()
        print self.getCurrentTime(),"获取到目录页面个数",self.total_num,"个"

        for x in range(start_page, int(self.total_num)):
            print self.getCurrentTime(),"正在抓取第",x,"个页面"
            try:
                self.getVenues(x)
            except urllib2.URLError, e:
                if hasattr(e, "reason"):
                    print self.getCurrentTime(),"某总页面内抓取或提取失败,错误原因", e.reason
            except Exception,e:  
                print self.getCurrentTime(),"某总页面内抓取或提取失败,错误原因:",e
            if x < self.total_num:
                f=open('page.txt','w')
                f.write(str(x))
                print self.getCurrentTime(),"写入新页码",x
                f.close()
            else:
                return 0
spider = Spider()
spider.main()       
#! /usr/bin/env python
# -*-coding:utf-8 -*-
import random
import requests.utils
import json
import jsonpath
from lxml import etree
import datetime
from dateutil.relativedelta import relativedelta
from urllib.parse import quote


class SD:
    """
    pc网页版山东电信
    """
    captcha_url = "http://login.189.cn/web/captcha"
    login_url = "http://login.189.cn/web/login"
    data_url = 'http://ln.189.cn/getSessionInfo.action'

    def __init__(self, account, password):

        self.session = requests.session()
        self.account = account
        self.password = password
        self.data = {}
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36"
        }

    def get_data(self):
        """
        获取验证码，并登陆
        :return:
        """

        captcha_params = {
            "undefined": "",
            "source": "login",
            "width": "100",
            "height": "37",
            str(random.random()): "",
        }

        response_1 = self.session.get(self.captcha_url, params=captcha_params)

        with open("captcha.jpg", "wb") as f:
            f.write(response_1.content)

        captcha = input("请输入登录的图片验证码: ")
        login_url = "http://login.189.cn/web/login"

        login_data = {
            "Account": phone_number,
            "UType": "201",
            "ProvinceID": "16",
            "AreaCode": "",
            "CityNo": "",
            "RandomFlag": "0",
            "Password": service_password,
            "Captcha": captcha,
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36"
        }

        response = self.session.post(login_url, headers=headers, data=login_data)

        text = etree.HTML(response.text)
        try:
            province = text.xpath(".//div[@class='cityChoose w81 h ov mt30']/div/div/a/text()")[0]
        except:
            print('登录失败')
            return self.get_data()  # 登录失败，重新登录
        else:
            if response.status_code == 200 and province:
                return True

    def get_cookie(self):

        cookies = requests.utils.dict_from_cookiejar(self.session.cookies)

        url = 'http://www.189.cn/dqmh/ssoLink.do?method=linkTo&platNo=10016&toStUrl=http://' \
              'sd.189.cn/selfservice/account/returnAuth?columnId=1121&fastcode=10000493&cityCode=sd'
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Host": "www.189.cn",
            "Referer": "http://www.189.cn/dqmh/my189/initMy189home.do",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36"
        }
        response = self.session.get(url, headers=headers, cookies=cookies)

        if response.status_code == 200:  # 增加cookie值

            url = 'http://sd.189.cn/resource/v4/js/jquery.cookies.js'
            r = self.session.get(url=url, headers=headers)

            return True

    def check_is_login(self):
        """
        获取用户手机号码区域编号，套餐类型
        :return:
        """
        cookies = requests.utils.dict_from_cookiejar(self.session.cookies)
        url1 = 'http://sd.189.cn/selfservice/cust/checkIsLogin'
        try:
            r = self.session.post(url1, headers=self.headers, json={}, cookies=cookies)
            j = r.json()
        except Exception as e:
            print(e)

        else:
            self.phoneNumber = jsonpath.jsonpath(j, "$..accNbr")[0]  # 手机号码

            self.areaCode = jsonpath.jsonpath(j, "$..areaCode")[0]  # 所属区编号
            self.userLoginType = jsonpath.jsonpath(j, "$..userLoginType")[0]  # 用户套餐类型

            data = {'accNbr': self.phoneNumber, 'areaCode': self.areaCode, 'accNbrType': self.userLoginType}

            return data

    def get_valicode(self):
        """
        刷新验证码
        :return:
        """
        cookies = requests.utils.dict_from_cookiejar(self.session.cookies)

        validatecode_url = 'http://sd.189.cn/selfservice/validatecode/codeimg.jpg?'

        # 验证码
        valicode_res = self.session.get(headers=self.headers, url=validatecode_url, cookies=cookies)

        with open("valicode.jpg", "wb") as f:
            f.write(valicode_res.content)
        valicode = input("请输入图片验证码：")

        if valicode:
            return valicode

    def first_selfservice(self):
        """
        查询个人基本资料，进行短信认证
        :return:
        """

        url = 'http://sd.189.cn/selfservice/service/sendSms'
        valicode = self.get_valicode()

        data = {"orgInfo": "13371372035", "valicode": valicode, "smsFlag": "real_2busi_validate"}

        r1 = self.session.post(url, headers=self.headers, data=json.dumps(data), cookies=self.cookies)

        if r1.text == '0':  # 发送验证码成功

            postsms = input('请输入二次验证短信:')

            self.first_busiVa(valicode, postsms)

        else:
            return self.first_selfservice()

    def first_busiVa(self, valicode, postsms):
        """
        短信验证
        :param valicode: 图片验证码
        :param postsms: 短信验证码
        :return:
        """

        busiva_url = 'http://sd.189.cn/selfservice/service/busiVa'

        busiva_data = {"username_2busi": "undefined", "credentials_no_2busi": "undefined", "validatecode_2busi":
            valicode, "randomcode_2busi": postsms, "randomcode_flag": "0"}

        response = self.session.post(busiva_url, headers=self.headers, data=json.dumps(busiva_data),
                                     cookies=self.cookies)

        res = response.json()

        if res['retnCode'] == 0:  # 认证成功

            self.cust_info()

    def cust_info(self):
        """
        需要请求两次，第一次请求此函数，系统返回需要二次验证。验证完之后，获取用户信息
        :return:
        """
        self.cookies = requests.utils.dict_from_cookiejar(self.session.cookies)

        headers = {
            "Host": "sd.189.cn",
            "Accept": "application/json",
            "Origin": "http://sd.189.cn",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36",
            "Content-Type": "application/json",
            "Referer": "http://sd.189.cn/selfservice/cust/manage",
        }
        url = 'http://sd.189.cn/selfservice/cust/querymanage?100'
        data = {}

        r = self.session.post(url=url, headers=headers, json=data, cookies=self.cookies)

        j = r.json()

        if j.get('ruleId') == '6':  # 二次业务实名制规则6校验未通过
            pass

        else:
            try:
                authorizeId = jsonpath.jsonpath(j, "$..id")[0]  # 认证ID
                mobileOperator = 'CHINA_TELECOM'

                self.iDCard = jsonpath.jsonpath(j, "$..indentNbr")[0]  # 身份证号码
                contactNum = jsonpath.jsonpath(j, "$..linkNbr")[0]  # 联系人号码
                phoneAttribution = jsonpath.jsonpath(j, "$..areaName")[0]  # 手机号归属地
                levelInfo = jsonpath.jsonpath(j, "$..custLevel")[0]  # 客户等级
            except Exception as e:
                print(e)

            else:
                self.query_balance()

    def query_balance(self):
        """
        余额查询
        :return:
        """
        queryBalance_url = 'http://sd.189.cn/selfservice/bill/queryBalance'
        data = self.check_is_login()
        try:
            res = self.session.post(url=queryBalance_url, headers=self.headers, json=data, cookies=self.cookies)
            j = res.json()
        except Exception as e:
            print(e)

        else:
            curFee = j.get('balance')  # 当前实际余额
            curFeeTotal = j.get('cfyBalance')  # 专有账户余额，储蓄余额
            print(curFee)
            print(curFeeTotal)

            self.get_zhangdan()

    def get_zhangdan(self):
        """
        获取月账单
        :return:
        """
        last = datetime.date.today() - relativedelta(months=+1)
        month = last.strftime("%Y%m")  # 上一月份
        getCustBill_url = 'http://sd.189.cn/selfservice/bill/getCustBill'

        getCustBill_data = {"accNbr": self.phoneNumber, "areaCode": self.areaCode, "ptype": self.userLoginType,
                            "billCycle": month}

        response = self.session.post(url=getCustBill_url, json=getCustBill_data, headers=self.headers,
                                     cookies=self.cookies)

        if response.status_code == 200:
            try:
                j = response.json()
            except Exception as e:
                print(e)
            else:
                topHtml = j.get('topHtml')
                topHtml_text = etree.HTML(topHtml)
                contactAddress = topHtml_text.xpath(".//tr/td[1]/text()")[0][3:]  # 通讯地址
                self.customerName = topHtml_text.xpath(".//tr[2]/td[1]/text()")[0][3:]  # 姓名

                jf = j.get("jf")
                jf_text = etree.HTML(jf)
                pointValue = jf_text.xpath(".//tr[3]/td[1]/text()")[0]  # 积分
                print(pointValue)

                month_list = jsonpath.jsonpath(j, "$...recentSixList")[0]  # 半年月账单列表
                print(month_list)
                print(contactAddress)
                print(self.customerName)

                for index, value in enumerate(reversed(month_list)):  # 倒序遍历列表的索引和值
                    last = datetime.date.today() - relativedelta(months=+(index + 1))
                    month = last.strftime("%Y%m")
                    print(month)  # 月份
                    print(value[1])  # 本月消费

                self.product_info()
        else:
            print('获取月账单失败,重新获取')
            return self.get_zhangdan()

    def product_info(self):
        """
        用户入网时间，注册地址
        :return:
        """
        loadMyProductInfo_url = "http://sd.189.cn/selfservice/cust/loadMyProductInfo"
        headers = {
            "Accept": "application/json, text/javascript, */*",
            "Content-Type": "application/json",
            "Host": "sd.189.cn",
            "Origin": "http://sd.189.cn",
            "Referer": "http://sd.189.cn/selfservice/IframeBill/manage",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36"
        }

        loadMyProductInfo_data = {"accNbr": self.phoneNumber, "areaCode": self.areaCode,
                                  "accNbrType": self.userLoginType, "queryType": "2",
                                  "queryMode": "1"}

        loadMyProductInfo_res = self.session.post(loadMyProductInfo_url, headers=headers, json=loadMyProductInfo_data,
                                                  cookies=self.cookies)
        if loadMyProductInfo_res.status_code == 200:
            try:
                loadMyProductInfo_j = loadMyProductInfo_res.json()
                retString = loadMyProductInfo_j.get('retString')
                retString = eval(retString)

                realNameInfo = jsonpath.jsonpath(retString, "$...prodItem")[0][0].get('name')  # 是否实名认证
                print(realNameInfo)

                # regAddress = jsonpath.jsonpath(retString, "$...address")[0]  # 注册地址
                # print(regAddress)
                phoneStatus = jsonpath.jsonpath(retString, "$...productStatusName")[0]  # 手机状态
                print(phoneStatus)

                netAge = jsonpath.jsonpath(retString, "$...servCreateDate")[0]  # 网龄
                print("入网时间{}".format(netAge))

            except Exception as e:
                print(e)

            else:
                self.check_bill_sms()
                # self.get_year_month()  # 开始查询通讯详单

    def check_bill_sms(self):
        """
        通讯详单查询 需要短信验证码
        :return:
        """
        sendBillSms_url = 'http://sd.189.cn/selfservice/bill/sendBillSmsRandom'
        headers = {
            "Accept": "application/json, text/javascript, */*",
            "Content-Type": "application/json",
            "Host": "sd.189.cn",
            "Origin": "http://sd.189.cn",
            "Referer": "http://sd.189.cn/selfservice/IframeBill/iframeSimple?tag=monthlyDetail",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36",
        }
        sendBillSms_data = {"orgInfo": self.phoneNumber, "nbrType": "4"}

        sendBillSms_res = self.session.post(sendBillSms_url, headers=headers, json=sendBillSms_data,
                                            cookies=self.cookies)

        checkBillSms_j = sendBillSms_res.json()

        if checkBillSms_j.get("flag") == '0':

            code = input('请输入查询通话详单的短信验证码:')
            checkBillSms_url = "http://sd.189.cn/selfservice/bill/checkBillSmsRandom"

            checkBillSms_data = {"code": code, "accNbrorg": self.phoneNumber}

            checkBillSms_res = self.session.post(url=checkBillSms_url, headers=headers, json=checkBillSms_data,
                                                 cookies=self.cookies)

            checkBillSms_j = checkBillSms_res.json()

            if checkBillSms_j.get('flag') == '1':  # 电信系统需要记录

                serverQuery_url = "http://sd.189.cn/selfservice/bill/serverQuery"

                serverQuery_data = {"accNbr": self.phoneNumber, "areaCode": self.areaCode,
                                    "accNbrType": self.userLoginType}
                try:

                    serverQuery_res = self.session.post(serverQuery_url, headers=headers, json=serverQuery_data,
                                                        cookies=self.cookies)

                except Exception as e:
                    print(e)
                    serverQuery_res = self.session.post(serverQuery_url, headers=headers, json=serverQuery_data,
                                                        cookies=self.cookies)

                if serverQuery_res.json().get('resultCode'):
                    self.get_phone_records()

        else:  # 短信认证失败，重新认证
            self.check_bill_sms()

    def second_selfservice(self):
        """
        第三次认证获取验证码
        :return:
        """
        url = 'http://sd.189.cn/selfservice/service/sendSms'
        valicode = self.get_valicode()

        if valicode:
            data = {"orgInfo": "13371372035", "valicode": valicode, "smsFlag": "real_2busi_validate"}

            r1 = self.session.post(url, headers=self.headers, data=json.dumps(data), cookies=self.cookies)

            if r1.text == '0':  # 发送验证码成功

                postsms = input('请输入三次验证短信:')

                self.second_busi_va(valicode, postsms)

            else:
                return self.second_selfservice()

    def second_busi_va(self, valicode, postsms):
        """
        第三次提交认证数据
        :param valicode:
        :param postsms:
        :return:
        """

        busiva_url = 'http://sd.189.cn/selfservice/service/busiVa'
        username_2busi = quote(self.customerName)

        busiva_data = {"username_2busi": username_2busi, "credentials_type_2busi": "1",
                       "credentials_no_2busi": self.iDCard, "validatecode_2busi": valicode,
                       "randomcode_2busi": postsms, "randomcode_flag": "0"}

        response = self.session.post(busiva_url, headers=self.headers, data=json.dumps(busiva_data),
                                     cookies=self.cookies)

        res = response.json()
        print(res)
        if res.get('retnCode') == 0:

            self.get_phone_records()

        else:
            print('第三次认证失败')
            self.second_busi_va(valicode, postsms)

    def get_phone_records(self):
        """
        获取通话记录
        :param postsms:
        :return:
        """
        for _ in range(0, 7):  # 最近半年, 可以查询7个月记录

            last = datetime.date.today() - relativedelta(months=+_)
            month = last.strftime("%Y%m")

            queryBillDetailNum_url = 'http://sd.189.cn/selfservice/bill/queryBillDetailNum?tag=iframe_rnval'
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Host": "sd.189.cn",
                "Origin": "http://sd.189.cn",
                "Referer": "http://sd.189.cn/selfservice/IframeBill/iframeSimple?tag=monthlyDetail",
                "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36"
            }
            queryBillDetailNum_data = {"accNbr": self.phoneNumber, "billingCycle": month, "ticketType": "0"}
            queryBillDetailNum_res = self.session.post(url=queryBillDetailNum_url, headers=headers,
                                                       json=queryBillDetailNum_data, cookies=self.cookies)

            queryBillDetailNum_j = queryBillDetailNum_res.json()

            if queryBillDetailNum_j.get('resultMsg') == '成功':

                records = int(queryBillDetailNum_j.get('records'))  # 通话记录条数，每页为20条记录

                if records == 0:
                    print('{}无通话记录'.format(month))
                    continue

                else:
                    pages = records // 20 if records % 20 == 0 else records // 20 + 1

                    try:
                        for pageNo in range(pages):

                            queryBillDetail_url = 'http://sd.189.cn/selfservice/bill/queryBillDetail'
                            queryBillDetail_data = {"accNbr": self.phoneNumber, "billingCycle": month,
                                                    "pageRecords": "20", "pageNo": str(pageNo + 1),
                                                    "qtype": "0", "totalPage": "1", "queryType": "6"}

                            queryBillDetail_res = self.session.post(url=queryBillDetail_url, headers=headers,
                                                                    json=queryBillDetail_data, cookies=self.cookies)

                            queryBillDetail_j = queryBillDetail_res.json()

                            if queryBillDetail_j.get("ruleId") == '1':  # 身份认证未通过的情况，重新认证
                                self.second_selfservice()

                            elif queryBillDetail_j.get("resultMsg") == "服务忙，请稍后再试":
                                self.get_phone_records()

                            elif queryBillDetail_j.get("resultMsg") == "成功":

                                callDetailRecord = []
                                # print(queryBillDetail_j)
                                items = jsonpath.jsonpath(queryBillDetail_j, "$..items")[0]
                                for _ in items:
                                    txxiangDanModel = dict()
                                    txxiangDanModel['startTime'] = _.get('startTime')  # 本次通话发生时间
                                    txxiangDanModel['commPlac'] = _.get('position')  # 本次通话发生地点
                                    txxiangDanModel['commMode'] = _.get('callType')  # 本次通话方式，主叫/被叫
                                    txxiangDanModel['anotherNm'] = _.get('calledNbr')  # 本次通话对方号码
                                    txxiangDanModel['commTime'] = _.get('duration')  # 本次通话时长(秒)
                                    txxiangDanModel['commType'] = _.get('eventType')  # 本次通话类型 ,无通讯费用
                                    txxiangDanModel['commFee'] = _.get('charge')  # 本次通话通信费(元)
                                    callDetailRecord.append(txxiangDanModel)
                                print(callDetailRecord)

                    except Exception as e:
                        print(e)
                        return self.second_selfservice()
            else:
                return self.get_phone_records()


def main():
    phone_number = ""
    service_password = ""
    sd = SD(phone_number, service_password)
    if sd.get_data():
        if sd.get_cookie():
            sd.cust_info()
            sd.first_selfservice()


if __name__ == "__main__":
    main()

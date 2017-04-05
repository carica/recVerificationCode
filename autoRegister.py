#/usr/bin/python3
# -*- coding : utf-8 -*-
from bs4 import BeautifulSoup
from io import BytesIO
from PIL import Image
from tesserocr import PyTessBaseAPI, PSM
import sys
import requests
import time
import chardet

class RegPHPWind(object):
    def __init__(self, siteURL, username, password):
        self.__siteURL = siteURL
        self.__username = username
        self.__password = password
        self.__UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.152 Safari/537.36"
        self.__login = '/login.php'
        self.__homepage = '/index.php'
        self.__mission = '/jobcenter.php'
        self.__center = '/u.php'
        self.__headers = {
        "User-Agent" : self.__UA,
        "Host" : self.__siteURL,
        "Referer" : self.__siteURL + self.__homepage,
        "Origin" : self.__siteURL + self.__homepage
        }
        self.__session = requests.Session()

    def getVerificationCode(self, image):
        im = Image.open(image)
        im = im.convert('L')
        with PyTessBaseAPI(psm=PSM.SINGLE_LINE) as api:
            api.SetImage(im)
            api.SetVariable('tessedit_char_whitelist', '0123456789-+')
            rawResult = api.GetUTF8Text()
            rawResult = rawResult[:rawResult.find(' ')]
            plusPos = rawResult.find('+')
            print(rawResult)
            if plusPos == -1:
                sevenPos = rawResult.find('7', 1) #first 7 is meant for real number
                while sevenPos != -1:
                    first = int(rawResult[:(sevenPos)])
                    second = int(rawResult[(sevenPos+1):])
                    if first - second < 0:
                        sevenPos = rawResult.find('7', sevenPos+1)
                    else:
                        break
                result = first - second
            else:
                first = int(rawResult[:(plusPos)])
                second = int(rawResult[(plusPos+1):])
                result = first + second
        return result

    def Run(self):
        page = self.__session.get(self.__siteURL + self.__login).text
        soup = BeautifulSoup(page, 'html.parser')
        imageURL = soup.find(attrs = {'id':'ckquestion'})['src']
        verifyImage = self.__session.get(self.__siteURL + '/%s'%imageURL).content
        # with open('a.png', 'wb') as img:
        #     img.write(verifyImage)
        result = self.getVerificationCode(BytesIO(verifyImage))
        print(result)

        verify_value = soup.find(attrs = {'name':'verify'})['value']

        post_info = {
            'pwuser': self.__username,
            'pwpwd': self.__password,
            'verify': verify_value,
            'step': '2',
            'qkey': '-1',
            'qanswer': result,
            'jumpurl': self.__siteURL,
        }

        resp = self.__session.post(self.__siteURL + self.__login, data=post_info)
        # print(resp.text)

        page = self.__session.get(self.__siteURL + self.__center).text
        soup = BeautifulSoup(page, 'html.parser')
        verify_script = soup.find_all('script')[3].text
        print(verify_script)
        verify_hash = verify_script.splitlines()[2].split('\'')[1]
        print(verify_hash)
        punch = soup.find(id='punch')['onclick']
        print(punch)

        post_info = {
        'action': 'punch',
        'verify': verify_hash,
        'step': '2'
        }
        res = self.__session.post(mission_url, data=post_info, headers=headers, verify=True).text
        print(res)


if __name__ == '__main__':
    with open('site.info', 'rt') as info:
        lines = [line.rstrip('\n') for line in info]
    test = RegPHPWind(*lines)
    test.Run()

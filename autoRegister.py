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
import pickle
import os

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
        self.__cookie_filename = "./cookie.pickle"

        self.__cookie = None
        if os.path.exists(self.__cookie_filename):
            with open(self.__cookie_filename, "rb") as f:
                self.__cookie = pickle.load(f)


    """compute verification code according to equation given by the image
    
    The ckquestion plugin for phpWind 7.5 turns an equation of add or substraction operation to an image.
    Its result must be between [0,99].
    Tesseract-ocr recognizes the plus operator correctly. The minus operator, however, is recognized as '7'.
    Therefore, we shall look for '7' in the string and try to replace it with '-' and see if the result is positive.
    It is possible that there are multiple '7's in the equation and the 2nd one is'nt '-'.
    In such case, the result is not correct.
    """
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
        if self.__cookie is not None:
            self.__session.cookies = self.__cookie
            print('cookies loaded.')
        else:
            page = self.__session.get(self.__siteURL + self.__login).text
            soup = BeautifulSoup(page, 'html.parser')
            ckquestion = soup.find(attrs = {'id':'ckquestion'})
            verify_value = soup.find(attrs = {'name':'verify'})['value']
            post_info = {
                'pwuser': self.__username,
                'pwpwd': self.__password,
                'verify': verify_value,
                'step': '2',
                'qkey': '-1',
                #'qanswer': result,
                'jumpurl': self.__siteURL,
            }
            # print(post_info)
            
            if ckquestion is not None:
                imageURL = ckquestion['src']
                verifyImage = self.__session.get(self.__siteURL + '/%s'%imageURL).content
                # with open('a.png', 'wb') as img:
                #     img.write(verifyImage)
                result = self.getVerificationCode(BytesIO(verifyImage))
                post_info['qanswer'] = result
                print(result)

            resp = self.__session.post(self.__siteURL + self.__login, data=post_info)
            # print(resp.text)

        page = self.__session.get(self.__siteURL + self.__center).text
        soup = BeautifulSoup(page, 'html.parser')
        verify_script = soup.find_all('script')[3].text
        # print(verify_script)
        if 'login' in verify_script:
            if self.__cookie is not None:
                os.remove(self.__cookie_filename)
            return None
        else:
            with open(self.__cookie_filename, "wb") as f:
                pickle.dump(self.__session.cookies, f)
        verify_hash = verify_script.splitlines()[2].split('\'')[1]
        print(verify_hash)
        punch = soup.find(id='punch')
        if punch is not None:
            print(punch['onclick'])

            post_info = {
                'action': 'punch',
                'verify': verify_hash,
                'step': '2'
            }
            res = self.__session.post(self.__siteURL + self.__mission, data=post_info).text
        else:
            res = 'already registered!'
        return res


if __name__ == '__main__':
    with open('site.info', 'rt') as info:
        lines = [line.rstrip('\n') for line in info]
    test = RegPHPWind(*lines)
    rm93 = None
    i = 0
    trials = 3 #for some reason, login attempt will fail. let's try 3 times before call it.
    while rm93 is None and i < trials:
        rm93 = test.Run()
        i = i + 1
    if rm93 is None:
        #send message to bot
    #print(rm93)

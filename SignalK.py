#!/usr/bin/python3
# -*- coding: iso-8859-15 -*-
# Author Per Norrfors 2020-09-05
import subprocess
import sys
sys.path.append("/home/pi/Documents/RPI_Remote/Waveshare/")  # OK
import epd2in7b
from PIL import Image, ImageDraw, ImageFont
from gpiozero import Button
from time import ctime
import socket
import requests
import json
import pytemperature # sudo pip3 install pytemperature
from gpiozero import CPUTemperature


def get_interface(interface):  # Get my intf
    try:
        ii = (subprocess.check_output(['iwgetid', 'wlan0']))
        ii = ii.decode("utf-8")
        print(ii)
        iii = ii.split(':')

        print(str(iii[1]))
        intFace = str(iii[1].replace('"', '')).strip() # Remove trailing and leading newlines from string
        print(intFace)
    except Exception as err:
        print(err)
        intFace = 'No Internet' + str(err)
    finally:
        print(f'{intFace} ')
        return str(intFace)

ssid = get_interface('wlan0')

class Display:
    btn = Button(5)

    def __init__(self):
        print('Init Display...')
        self.epd = epd2in7b.EPD()
        Display.btn.when_pressed = Display.handleBtnPress
        self.epd.init()
        self.epd.Clear()

    def printToDisplay(self, r1, r2, r3, r4, r5, row3Red):
        print("printToDisplay...")

        HBlackImage = Image.new('1', (epd2in7b.EPD_HEIGHT, epd2in7b.EPD_WIDTH), 255)
        HRedImage = Image.new('1', (epd2in7b.EPD_HEIGHT, epd2in7b.EPD_WIDTH), 255)

        draw_black = ImageDraw.Draw(HBlackImage)   # Create draw object and pass in the image layer we want to work with (HBlackImage)
        draw_red = ImageDraw.Draw(HRedImage)       # Create draw object and pass in the image layer we want to work with (HBlackImage)
        fontL = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeSerif.ttf', 30)  # Create our font, passing in the font file and font size
        fontM = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeSerif.ttf', 22)  # Create our font, passing in the font file and font size
        fontS = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeSerif.ttf', 14)  # Create our font, passing in the font file and font size
        leftCol = 10
        rowOffset1 = 5
        rowOffset2 = 10
        rowHeight = 27
        draw_red.text((leftCol, rowOffset1 + 0 * rowHeight), r1, font=fontL, fill=0)
        draw_black.text((leftCol, rowOffset2 + 1 * rowHeight), r2, font=fontS, fill=0)
        if row3Red:
            draw_red.text((leftCol, rowOffset2 + 2 * rowHeight), r3, font=fontM, fill=0)
        else:
            draw_black.text((leftCol, rowOffset2 + 2 * rowHeight), r3, font=fontM, fill=0)
        draw_black.text((leftCol, rowOffset2 + 3 * rowHeight), r4, font=fontM, fill=0)
        draw_black.text((leftCol, rowOffset2 + 4 * rowHeight), r5, font=fontM, fill=0)
        draw_black.text((leftCol, rowOffset2 + 5 * rowHeight), ctime(), font=fontM, fill=0)

        self.epd.display(self.epd.getbuffer(HBlackImage), self.epd.getbuffer(HRedImage))

    def handleBtnPress(self):
        print("handleBtnPress enter...")

class SignalK:
    def __init__(self, URL):
        self.mmsi = ''
        self.code = 0
        self.res_txt = ''
        self.res_float = 0.0
        self.res_int = 0
        self.loaded_json = {}  # dict
        self.SignalK_URL = URL  # 'alumina.norrfors.se:3000'

    def Read_SignalK(self, URL, OKtxt, NOKtxt):
        print(self.SignalK_URL + URL)
#        resp = requests.get('http://alumina.norrfors.se:3000/signalk/v1/api/')

        resp = requests.get(self.SignalK_URL + URL)
        self.status_code = resp.status_code
        if self.status_code != 200:    # This means something went wrong.
            print(self.status_code)    # Debug
            self.res_txt = NOKtxt + ' : ' + str(resp.status_code)
            return False
        else:
            if isinstance(resp.json(), float):
                self.res_float = resp.json()
            else:
                if isinstance(resp.json(), int):
                    self.res_int = resp.json()
                else:
                    self.res_txt = OKtxt
                    for ii in resp.json():
                        self.res_txt += ii
                        print(ii)              # Debug
            json_str = json.dumps(resp.json())
            self.loaded_json = json.loads(json_str)
            return True

def get_CPUtemp():
    cpu = CPUTemperature()
    print(f'CPU Temp = {cpu.temperature:.1f}')
    return round(cpu.temperature, 1)

def get_IP():  # Get my IP
    try:
        hostname = socket.gethostname()
#        internal_address = socket.gethostbyname(hostname) funkar ej med Telia dongle?
        # get the internal IP address
        addresses = subprocess.check_output(["hostname", "-I"]).split()
        if len(addresses) > 0:
            internal_address = addresses[0].decode("utf-8")
            if len(addresses) > 1: # two connections?
                internal_address += ' ' + addresses[1].decode("utf-8")

# get the external IP address
            check_address = requests.get('http://checkip.dyndns.org/').text
            start = check_address.find(': ') + 2
            end = check_address.find('</body>')
            external_address = check_address[start:end]
            print(f'{hostname} {internal_address} {external_address}')
        else:
            internal_address = 'No IP connection!'
    except Exception as err:
        print(err)
        internal_address = 'Err conn.'
    finally:
        return internal_address  # + ' - ' + external_address

if __name__ == "__main__":
    print("Executed when invoked directly")
    print(ctime() + " Start...")
    cpu_temp_value = get_CPUtemp()
    cpu_temp = f'CPU {cpu_temp_value:.1f}C'  # in celsius
    myIP = get_IP()

    boat_name = 'SignalK No Respons'
    kyl_temp_value = -99
    kyl_temp = ''
    pos = 'Signal-K: No GPS!'
    temp = ''
    pressure = ''
#    mySK=SignalK('http://alumina.norrfors.se:3000')  # Instantiate SignalK over the Internet!
    mySK = SignalK('http://127.0.0.1:3000')  # Instantiate SignalK local
    if mySK.Read_SignalK('/signalk/v1/api/vessels/', '', "SignalK No Respons"):
        try:
            mySK.mmsi = mySK.res_txt
            boat_name = mySK.loaded_json[mySK.mmsi]['name'] + ' Signal-K'
        except Exception as err:
            print(err)
            boat_name = 'Ship name missing'
        print(boat_name)

        if mySK.Read_SignalK('/signalk/v1/api/vessels/' + mySK.mmsi + '/environment/inside/refrigerator/temperature/value',
                        '', "SignalK No Kyl Temp"):
            kyl_temp_value = pytemperature.k2c(mySK.res_float)   # Celsius
            kyl_temp = f'Kyl {kyl_temp_value:.1f}C'
        print(kyl_temp)

        if mySK.Read_SignalK('/signalk/v1/api/vessels/' + mySK.mmsi + '/environment/inside/refrigerator/pressure/value',
                        '', "SignalK No Pressure"):
            mmhg = mySK.res_int / 1000.0 * 7.50062
            pressure = f'Barometric {mmhg:.0f} mmHg' # f'Barometric {pytemperature.k2c(mySK.res_int)}Pa'
        print(pressure)
        '''
        if mySK.Read_SignalK('/signalk/v1/api/vessels/' + mySK.mmsi + '/environment/rpi/cpu/temperature/value',
                        '', "SignalK No CPU Temp"):
            cpu_temp = f'CPU {pytemperature.k2c(mySK.res_float):.1f}C'
        print(cpu_temp)
        '''
        if mySK.Read_SignalK('/signalk/v1/api/vessels/' + mySK.mmsi + '/navigation/position/value/',
                        '', "SignalK No GPS"):
            pos = f'GPS N {mySK.loaded_json["latitude"]:.4f} E {mySK.loaded_json["longitude"]:.4f}'
        print(pos)

    temp = kyl_temp + ' ' + cpu_temp

    if cpu_temp_value > 60 or cpu_temp_value < -20 or \
       kyl_temp_value > 8 or kyl_temp_value < 0:
        row3Red = True
    else:
        row3Red = False

    myDisp = Display()  # Instantiate Display
    myDisp.printToDisplay(boat_name, ssid + ' ' + myIP, temp, pos, pressure, row3Red)
    print("wait for keypress...")
    exit()  # Terminate script (will not wait for keypress any more)
else:
    print("Executed when imported")

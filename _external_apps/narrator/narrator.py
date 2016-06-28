#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import httplib
import threading
import time
import subprocess
from os import system, path
from PyQt4 import QtGui
from math import ceil
from ConfigParser import ConfigParser
from django.utils.encoding import smart_str, smart_unicode, force_unicode


class NarratorUI(QtGui.QWidget):

    def __init__(self):
        super(NarratorUI, self).__init__()
        self._reset_scene_info()
        self.initUI()


    def initUI(self):
        # Celebrity list
        self.lsCeleb= QtGui.QListWidget(self)
        self.slug_list= self.fill_celebrity(self.lsCeleb)
        self.lsCeleb.itemActivated.connect(self.onActivatedCelebrity)
        self.lsCeleb.setSizePolicy(
            QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        
        # Celebrity name label
        self.lbCeleb= QtGui.QLabel('', self)

        # Celebrity Languages list
        self.cbLang= QtGui.QComboBox(self)
        self.cbLang.activated[str].connect(self.onActivatedLang)

        # Script text
        self.stText= QtGui.QTextEdit()
        self.stText.setReadOnly(True)

        # Navigation buttons & current scene indicator
        self.btNext= QtGui.QPushButton(">>")
        self.btPrev= QtGui.QPushButton("<<")
        self.lbCurrScene= QtGui.QLabel()
        self.lbCurrScene.setText('<p style="font-size:30pt;">0</p>')
        self.lbSceneDur= QtGui.QLabel('0')
        self.lbSceneDur.setText('<p style="font-size:30pt;">0</p>')
        self.btNext.clicked.connect(self.next_scene)
        self.btPrev.clicked.connect(self.prev_scene)
        self.nextShortcut= QtGui.QShortcut( # [->]
            QtGui.QKeySequence.MoveToNextChar, self.btNext)
        self.nextShortcut.activated.connect(self.next_scene)
        self.prevShortcut= QtGui.QShortcut( # [<-]
            QtGui.QKeySequence.MoveToPreviousChar, self.btPrev)
        self.prevShortcut.activated.connect(self.prev_scene)

        # REC. section
        self.lbFileExist= QtGui.QLabel()
        self.lbFileExist.setText('<p style="font-size:80pt;color:#df0004">-</p>')
        self.btRec= QtGui.QPushButton("REC.")
        self.btRec.clicked.connect(self.record)
        self.btListen= QtGui.QPushButton(u"Прослушать")
        self.btListen.clicked.connect(self.listen)
        self.btCancel= QtGui.QPushButton(u"Отмена")
        self.recordShortcut= QtGui.QShortcut( # [Space]
            QtGui.QKeySequence("Space"), self.btRec)
        self.recordShortcut.activated.connect(self.record)
        self.listenShortcut= QtGui.QShortcut( # [Enter]
            QtGui.QKeySequence.InsertParagraphSeparator, self.btListen)
        self.listenShortcut.activated.connect(self.listen)

        # Timer label
        self.lbTimer= QtGui.QLabel('<p style="font-size:60pt;color:#000000">0</p>')
        # self.lcdTimer= QtGui.QLCDNumber(self)

        # Layout
        grid= QtGui.QGridLayout()
        grid.setSpacing(10)
        centerVLayout= QtGui.QVBoxLayout() # Central box
        rightVLayout= QtGui.QVBoxLayout() # Right box

        centerVLayout.addWidget(self.lbCeleb)
        centerVLayout.addWidget(QtGui.QLabel(u'Язык'))
        centerVLayout.addWidget(self.cbLang)
        centerVLayout.addWidget(self.stText)

        rightVLayout.addWidget(self.btNext)
        rightVLayout.addWidget(self.btPrev)
        rightVLayout.addWidget(self.lbCurrScene)
        rightVLayout.addWidget(self.lbSceneDur)
        rightVLayout.addWidget(self.lbTimer)
        # rightVLayout.addWidget(self.lcdTimer)
        rightVLayout.addWidget(self.lbFileExist)
        rightVLayout.addWidget(self.btRec)
        rightVLayout.addWidget(self.btListen)
        rightVLayout.addWidget(self.btCancel)

        grid.addWidget(self.lsCeleb, 0, 0)
        grid.addLayout(centerVLayout, 0, 1, 1, 1)
        grid.addLayout(rightVLayout, 0, 2, 1, 1)

        self.setLayout(grid)
        # self.setLayout(mainHLayout)
        
        self.setGeometry(QtGui.QDesktopWidget().screenGeometry())
        self.setWindowTitle(u'Большие люди: Диктор')
        self.show()

    def _reset_scene_info(self):
        """scene_info is a class dict for current scene data.
        Used to name files
        """
        self.scene_info= {'slug': '', 'lang': '', 'scene': None}

    def _get_next_scene_index(self, curr_scene_index, inc):
        is_script= True
        try:
            last_scene_index= len(self.script)-1
        except AttributeError:
            is_script= False
        if is_script:
            next_scene_index= curr_scene_index + inc
            if next_scene_index > last_scene_index:
                if conf.SCROLL:
                    next_scene_index= 0
                else:
                    next_scene_index= last_scene_index
            if next_scene_index < 0:
                if conf.SCROLL:
                    next_scene_index= last_scene_index
                else:
                    next_scene_index= 0
        else:
            next_scene_index= -1
        return next_scene_index


    def print_dur_pretty(self, ms):
        minutes, milliseconds= divmod(ms, 60000)
        seconds= float(milliseconds) / 1000
        split_sec= divmod(seconds, 1)
        return "%i:%02d.%03d" % (minutes, split_sec[0],
            int(str(split_sec[1]).split('.')[1]))


    def show_text_and_dur(self, inc, initial=False):
        if initial:
            nxt= self._get_next_scene_index(-1, inc)
        else:
            nxt= self._get_next_scene_index(int(self.scene_info['scene']), inc)
        if nxt >= 0:
            self.lbCurrScene.setText('<p style="font-size:30pt;">%s</p>' % str(nxt+1))

            scene_text= force_unicode(smart_str(self.script[nxt]['text']), encoding='utf-8')
            self.stText.setText('<p style="font-size:46pt;">%s</p>' % scene_text)
            self.lbSceneDur.setText(
                '<p style="font-size:30pt;">%s</p>' %
                self.print_dur_pretty(self.script[nxt]['dur']))
            self.scene_info['scene']= nxt

            try: # Indicator that file exists or not.
                filename= "%s%s_%s_%s.%s" % (conf.AUDIO_PATH,
                    self.scene_info['slug'], self.scene_info['lang'],
                    str(self.scene_info['scene']), conf.AUDIO_FORMAT)
            except:
                filename= None
                self.lbFileExist.setText(
                    '<p style="font-size:80pt;color:#df0004">-</p>')
            if filename:
                if path.exists(filename):
                    self.lbFileExist.setText(
                        '<p style="font-size:80pt;color:#00208a">+</p>')
                else:
                    self.lbFileExist.setText(
                        '<p style="font-size:80pt;color:#df0004">-</p>')


    def next_scene(self):
        """Next script scene
        """
        self.show_text_and_dur(1)


    def prev_scene(self):
        """Previous script scene
        """
        self.show_text_and_dur(-1)


    def record(self):
        """ Record from input.
        """
        source= self.sender()
        try:
            ind= self.scene_info['scene']
            duration= self.script[ind]['dur']
        except Exception as e:
            duration= None
        if duration:
            duration= int(ceil(float(duration) / 1000)) # Duration should be in seconds.
            filename= "%s%s_%s_%s" % (conf.AUDIO_PATH, self.scene_info['slug'],
                self.scene_info['lang'], str(self.scene_info['scene']))
            if path.exists(filename+'.'+conf.AUDIO_FORMAT):
                reply= QtGui.QMessageBox.question(self,
                    u"Файл существует!", u"Файл %s.%s существует!\nПереписать?" % (filename, conf.AUDIO_FORMAT),
                    QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
                if reply == QtGui.QMessageBox.Yes:
                    self.record_to_file(filename+".wav", duration)
            else:
                self.record_to_file(filename+".wav", duration)
        

    def onActivatedCelebrity(self):
        """Celebrity has been changed
        """
        self.lbCeleb.setText(
            '<p style="font-size:20pt; font-weight: bold;">%s</p>'
            % self.lsCeleb.currentItem().text())
        self.lbCeleb.adjustSize()
        slug= self.slug_list[self.lsCeleb.indexFromItem(self.lsCeleb.currentItem()).row()]
        self._reset_scene_info()
        self.scene_info['slug']= slug
        self.lang_list= self.fill_celebrity_lang(self.cbLang, slug)
        # WARNING! add here change of the text, sthn like self.cbLang.activate
        

    def onActivatedLang(self, text):
        """Language has been changed
        """
        slug= self.slug_list[self.lsCeleb.indexFromItem(self.lsCeleb.currentItem()).row()]
        lang= self.lang_list[self.cbLang.currentIndex()]
        self.scene_info['lang']= lang.lower()
        self.scene_info['scene']= 0
        self.script= self.fill_celebrity_lang_text(self.stText, slug, lang)
        self.show_text_and_dur(1, initial=True) # Update text and duration.


    def fill_celebrity(self, widget):
        """Fill list of celebrities for choose
        """
        data= self._get_data_from_http_response('GET', '/api/celebrity/')
        # data= celeb_data()
        out= []
        widget.clear()
        if data:
            for celebrity in data['celebrity']:
                celebrity_name= force_unicode(smart_str(celebrity['name']), encoding='utf-8')
                widget.addItem(celebrity_name)
                out.append(celebrity['slug'])
        return out


    def fill_celebrity_lang(self, widget, slug):
        data= self._get_data_from_http_response('GET', '/api/celebrity/%s/' % slug)
        out= []
        widget.clear()
        for lang in data['celebrity']['language']:
            lang_title= force_unicode(smart_str(lang['title_orig']), encoding='utf-8')
            widget.addItem(lang_title)
            out.append(lang['title'])
        return out


    def fill_celebrity_lang_text(self, widget, slug, lang):
        data= self._get_data_from_http_response('GET', '/api/celebrity/%s/%s/' % (slug, lang))
        out= data['celebrity'][lang]['script']
        widget.clear()
        return out


    def _get_data_from_http_response(self, method, uri):
        """Get data from the server via API
        Returns dict
        """
        conn= httplib.HTTPConnection(conf.HOST)
        try:
            conn.request(method, uri)
        except:
            return None
        response= conn.getresponse()
        data= response.read()
        data= force_unicode(smart_str(data), encoding='utf-8')
        data_dict= eval(data)
        conn.close()
        return data_dict


    def clock(self, interval):
        i= interval
        warning= int(interval * 0.3)
        ending= int(interval * 0.1)
        reportstr= '<p style="font-size:60pt;color:#df0004">!'
        exec('self.lbTimer.setText(reportstr)')
        time.sleep(1) # signal!

        while i >= 0:
            if i > warning:
                reportstr= '<p style="font-size:60pt;color:#000000">' + str(i)
            elif i <= warning and i > ending:
                reportstr= '<p style="font-size:60pt;color:#f6bc12">' + str(i)
            elif i <= ending:
                reportstr= '<p style="font-size:60pt;color:#df0004">' + str(i)
            exec('self.lbTimer.setText(reportstr)')
            time.sleep(1)
            i -= 1
        reportstr= '<p style="font-size:60pt;color:#000000">' + str(i+1) # last sec value
        exec('self.lbTimer.setText(reportstr)')


    def _do_listen(self, filename):
        if path.exists(filename):
            p= subprocess.Popen(['play', filename])
        else:
            reply= QtGui.QMessageBox.question(self,
                u"Файл не найден!", u"Файл %s не существует!" % filename,
                QtGui.QMessageBox.Ok)
        

    def listen(self):
        """Listen to the recorded file
        """
        filename= "%s%s_%s_%s.%s" % (conf.AUDIO_PATH, self.scene_info['slug'],
            self.scene_info['lang'], str(self.scene_info['scene']), conf.AUDIO_FORMAT)
        self._do_listen(filename)


    def is_file_open(self, filename, timeout):
        """Check if processed file is open
        """
        file_open= True
        while file_open and timeout > 0:
            time.sleep(0.1)
            timeout= float(timeout) - 0.1
            try:
                myfile= open(filename, "r+")
                myfile.close()
                file_open= False
            except:
                file_open= True
        return file_open


    def _do_record(self, path, dur):
        self._do_listen(conf.AUDIO_SIGNAL) # Signal!
        time.sleep(1)
        
        p= subprocess.Popen(['rec', '-c', '2', path, 'trim', '0', '00:%02d' % dur])
        while p.poll() != 0:
            time.sleep(0.1)

        if self.is_file_open(path, 10): # 10 sec for saving the file.
            QtGui.QMessageBox.question(self,
                u"Файл занят другим приложением!",
                u"Достигнут таймаут при попытке записать файл \n%s" % path,
                QtGui.QMessageBox.Ok)
        else:
            p= subprocess.Popen(['sox', path,
                path.replace('.wav', '.'+conf.AUDIO_FORMAT)])

        if self.is_file_open(path.replace('.wav', '.'+conf.AUDIO_FORMAT), 10): # 10 sec for converting.
            QtGui.QMessageBox.question(self,
                u"Файл занят другим приложением!",
                u"При попытке получить доступ достигнут таймаут \n%s" % path.replace('.wav', '.'+conf.AUDIO_FORMAT),
                QtGui.QMessageBox.Ok)
        else:
            self._do_listen(conf.AUDIO_SIGNAL) # Signal after recording.
            p= subprocess.Popen(['rm', path]) # Remove original wave.

            if conf.AUTOLISTEN: # Listen to the file just recorded.
                self.listen()

            self.lbFileExist.setText( # Change
                '<p style="font-size:80pt;color:#00208a">+</p>')
        


    def record_to_file(self, path, dur):
        """Records from the microphone and
        outputs the resulting data to 'path'
        """
        t_clock= threading.Thread(target=self.clock, args=(dur,))
        t_clock.start()
        t_rec= threading.Thread(target=self._do_record, args=(path, dur,))
        t_rec.start()


class Conf():
    def __init__(self, path):
        cfg= ConfigParser({'basedir': path})
        cfg.read(path)
        self.fill_conf_values(cfg)

    def fill_conf_values(self, cfg):
        # Connection
        self.HOST= cfg.get('connect', 'host')
        # Audio settings
        self.AUDIO_PATH= cfg.get('audio', 'path')
        self.AUDIO_FORMAT= cfg.get('audio', 'format')
        self.AUDIO_SIGNAL= cfg.get('audio', 'signal')
        self.AUTOLISTEN= cfg.get('audio', 'autolisten')
        if self.AUTOLISTEN == 'true':
            self.AUTOLISTEN= True
        else:
            self.AUTOLISTEN= False
            # Interface settings
        self.SCROLL= cfg.get('interface', 'scroll')
        if self.SCROLL == 'true':
            self.SCROLL= True
        else:
            self.SCROLL= False
        
    

def main():
    app= QtGui.QApplication(sys.argv)
    ex= NarratorUI()
    sys.exit(app.exec_())


if __name__ == '__main__':
    conf_filename= path.join(path.dirname(__file__),
        __file__.split('.')[0]+'.conf')
    conf= Conf(conf_filename)
    main()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# Copyright 2021 Kevin B. Hendricks, Stratford Ontario Canada
# Copyright 2021 Doug Massay

# This plugin's source code is available under the GNU LGPL Version 2.1 or GNU LGPL Version 3 License.
# See https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html or
# https://www.gnu.org/licenses/lgpl.html for the complete text of the license.

import sys
import os
import argparse
import tempfile, shutil
import inspect

try:
    from PySide2.QtCore import *
    from PySide2.QtWidgets import *
    from PySide2.QtGui import *
    from PySide2.QtWebEngineWidgets import QWebEnginePage, QWebEngineProfile, QWebEngineScript
    from PySide2.QtWebEngineWidgets import QWebEngineSettings, QWebEngineView
    print('Pyside2')
except:
    from PyQt5.QtCore import *
    from PyQt5.QtWidgets import *
    from PyQt5.QtGui import *
    from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineProfile, QWebEngineScript
    from PyQt5.QtWebEngineWidgets import QWebEngineSettings, QWebEngineView
    print('PyQt5')


SCRIPT_DIR = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

_plat = sys.platform.lower()
iswindows = 'win32' in _plat or 'win64' in _plat
ismacos = isosx = 'darwin' in _plat

def setup_highdpi(highdpi):
    has_env_setting = False
    env_vars = ('QT_AUTO_SCREEN_SCALE_FACTOR', 'QT_SCALE_FACTOR', 'QT_SCREEN_SCALE_FACTORS', 'QT_DEVICE_PIXEL_RATIO')
    for v in env_vars:
        if os.environ.get(v):
            has_env_setting = True
            break
    if highdpi == 'on' or (highdpi == 'detect' and not has_env_setting):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    elif highdpi == 'off':
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, False)
        for p in env_vars:
            os.environ.pop(p, None)


class WebPage(QWebEnginePage):

    def __init__(self, parent=None):
       QWebEnginePage.__init__(self, parent)

    def javaScriptConsoleMessage(self, level, msg, linenumber, source_id):
        prefix = {
            QWebEnginePage.JavaScriptConsoleMessageLevel.InfoMessageLevel: 'INFO',
            QWebEnginePage.JavaScriptConsoleMessageLevel.WarningMessageLevel: 'WARNING'
        }.get(level, 'ERROR')
        if prefix in ('ERROR') and not 'ResizeObserver loop limit exceeded' in msg:
            try:
                print('%s: %s:%s: %s' % (prefix, source_id, linenumber, msg), file=sys.stderr)
                sys.stderr.flush()
            except EnvironmentError:
                pass
            
    def acceptNavigationRequest(self, url, req_type, is_main_frame):
        if req_type == QWebEnginePage.NavigationType.NavigationTypeReload:
            return True
        if req_type == QWebEnginePage.NavigationType.NavigationTypeBackForward:
            return True
        if url.scheme() in ('data', 'file', 'blob'):
            return True
        if url.scheme() in ('http', 'https') and req_type == QWebEnginePage.NavigationType.NavigationTypeLinkClicked:
            print('Blocking external navigation request to: ', url.toString())
            return False;
        print('Blocking navigation request to:', url.toString())
        return False


class WebView(QWebEngineView):

    def __init__(self, parent=None):
        QWebEngineView.__init__(self, parent)
        s = self.settings();
        s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.AllowWindowActivationFromJavaScript, True)
        w = QApplication.instance().desktop().availableGeometry(self).width()
        self._size_hint = QSize(int(w/3), int(w/2))
        self._page = WebPage(self)
        self.setPage(self._page)

    def sizeHint(self):
        return self._size_hint


    
class MainWindow(QMainWindow):

    # constructor
    def __init__(self, query, prefs, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        
        self.query = query
        self.prefs = prefs
        
        # creating a QWebEngineView
        self.browser = WebView()

        # adding action when loading is finished
        self.browser.loadFinished.connect(self.update_title)

        # creating QToolBar for navigation and add close button
        # navtb = QToolBar("Navigation")
        # self.addToolBar(navtb)
        # done_btn = QAction('Close', self)
        # done_btn.setStatusTip('Close Reader')
        # done_btn.triggered.connect(self.done)
        # navtb.addAction(done_btn)
        
        # build url to launch readium with
        readerpath = os.path.join(SCRIPT_DIR,'viewer','cloud-reader-lite','index.html')
        bookurl = QUrl.fromLocalFile(readerpath)
        bookurl.setQuery(self.query)
        self.browser.setUrl(bookurl)

        # set this browser as central widget or main window
        self.setCentralWidget(self.browser)

        self.readsettings()
        self.show()

    def readsettings(self):
        b64val = self.prefs.get('geometry', None)
        if b64val:
            self.restoreGeometry(QByteArray.fromBase64(QByteArray(b64val.encode('ascii'))))

    # method for updating the title of the window
    def update_title(self):
        if not self.browser or not self.browser.isVisible():
            return;
        height = self.browser.height()
        width =    self.browser.width()
        self.setWindowTitle('Screen Size:'  +  ' (%dx%d)' % (width, height))

    def done(self):
        self.close()

    def resizeEvent(self, ev):
        QMainWindow.resizeEvent(self, ev)
        self.update_title()

    def closeEvent(self, ev):
        b64val = str(self.saveGeometry().toBase64(), 'ascii')
        self.prefs['geometry'] = b64val
        QMainWindow.closeEvent(self, ev)


# the plugin entry point
def run(bk):

    if bk.launcher_version() < 20210430:
        print("\nThis plugin requires Sigil-1.6.0 or later to function.")
        return -1
    
    # get users preferences and set defaults for width of images in gui (in pixels)
    prefs = bk.getPrefs()

    # create your own current copy of all ebook contents in destination directory
    # it must be relative and under the index.html directory inside an epub_content directory
    viewer_home = os.path.join(SCRIPT_DIR, 'viewer', 'cloud-reader-lite')
    epub_home = os.path.join(viewer_home, 'epub_content')
    os.makedirs(epub_home, exist_ok = True)

    bookdir = tempfile.mkdtemp(suffix=None, prefix=None, dir=epub_home)
    bookdir_name = os.path.split(bookdir)[-1]

    bk.copy_book_contents_to(bookdir)
    data = 'application/epub+zip'
    mpath = os.path.join(bookdir, 'mimetype')
    with open(mpath, 'wb') as f:
        f.write(data.encode('utf-8'))
        f.close()
        
    query = 'epub=epub_content/' +  bookdir_name + '/'

    if not ismacos:
        setup_highdpi(bk._w.highdpi)

    # creating a pyQt5 application
    app = QApplication(sys.argv)

    # setting name to the application
    app.setApplicationName("Readium Cloud Reader Lite Demo")

    # creating a main window object
    window = MainWindow(query, prefs)

    # loop
    app.exec_()
    
    # done with temp folder so clean up after yourself
    shutil.rmtree(bookdir)
    
    print("Readium Reader Session Complete")
    bk.savePrefs(prefs)

    # Prevent potential crash when exiting by specifying the order
    # of deletion. Apparently a known issue with PyQt5 < 5.14
    # https://stackoverflow.com/questions/59120337/59126660#59126660
    del window, app

    # Setting the proper Return value is important.
    # 0 - means success
    # anything else means failure
    return 0
 

def main():
    print("I reached main when I should not have\n")
    return -1
    
if __name__ == "__main__":
    sys.exit(main())


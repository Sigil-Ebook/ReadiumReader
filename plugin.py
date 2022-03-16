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

from plugin_utils import QtCore, QtWidgets
from plugin_utils import QtWebEngineWidgets
from plugin_utils import QWebEnginePage, QWebEngineProfile, QWebEngineScript, QWebEngineSettings
from plugin_utils import PluginApplication, iswindows, ismacos

SCRIPT_DIR = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))


class WebPage(QWebEnginePage):

    def __init__(self, profile, parent=None):
       QWebEnginePage.__init__(self, profile, parent)

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


class WebView(QtWebEngineWidgets.QWebEngineView):

    def __init__(self, parent=None):
        QtWebEngineWidgets.QWebEngineView.__init__(self, parent)
        app = PluginApplication.instance()
        # Plugin prefs folder
        pfolder = os.path.dirname(app.bk._w.plugin_dir) + '/plugins_prefs/' + app.bk._w.plugin_name
        localstorepath = pfolder + '/local-storage'
        if not os.path.exists(localstorepath):
            try:
                os.makedirs(localstorepath, 0o700)
            except FileExistsError:
                # directory already exists
                pass
        print(localstorepath)
        s = self.settings()
        s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.AllowWindowActivationFromJavaScript, True)
        w = app.primaryScreen().availableGeometry().width()
        self._size_hint = QtCore.QSize(int(w/3), int(w/2))
        # How to get bookid to add to QWebEngineProfile name?
        self._profile = QWebEngineProfile('ReadiumReaderSigilPluginSettings')
        self._page = WebPage(self._profile, self)
        self.setPage(self._page)
        # Save Readium prefs to plugin prefs
        self._page.profile().setCachePath(localstorepath)
        self._page.profile().setPersistentStoragePath(localstorepath)
        print(self._page.profile().isOffTheRecord())
        print(self._page.profile().cachePath())
        print(self._page.profile().persistentStoragePath())

    def sizeHint(self):
        return self._size_hint


    
class MainWindow(QtWidgets.QMainWindow):

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
        bookurl = QtCore.QUrl.fromLocalFile(readerpath)
        bookurl.setQuery(self.query)
        self.browser.setUrl(bookurl)

        # set this browser as central widget or main window
        self.setCentralWidget(self.browser)

        self.readsettings()
        self.show()

    def readsettings(self):
        b64val = self.prefs.get('geometry', None)
        if b64val:
            self.restoreGeometry(QtCore.QByteArray.fromBase64(QtCore.QByteArray(b64val.encode('ascii'))))

    # method for updating the title of the window
    def update_title(self):
        if not self.browser or not self.browser.isVisible():
            return
        height = self.browser.height()
        width =    self.browser.width()
        self.setWindowTitle('Screen Size:'  +  ' (%dx%d)' % (width, height))

    def done(self):
        self.close()

    def resizeEvent(self, ev):
        QtWidgets.QMainWindow.resizeEvent(self, ev)
        self.update_title()

    def closeEvent(self, ev):
        b64val = str(self.saveGeometry().toBase64(), 'ascii')
        self.prefs['geometry'] = b64val
        QtWidgets.QMainWindow.closeEvent(self, ev)


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

    '''
    if not ismacos:
        setup_highdpi(bk._w.highdpi)
    '''
    icon = os.path.join(bk._w.plugin_dir, bk._w.plugin_name, 'plugin.svg')
    # creating a python qt application
    app = PluginApplication(sys.argv, bk, app_icon=icon)

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


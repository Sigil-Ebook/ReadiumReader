# importing required libraries
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
import os
import sys
import argparse

_plat = sys.platform.lower()
iswindows = 'win32' in _plat or 'win64' in _plat
ismacos = isosx = 'darwin' in _plat


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


# creating main window class
class MainWindow(QMainWindow):

    # constructor
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        
        mydir = os.path.dirname(os.path.abspath(__file__))
        
        # creating a QWebEngineView
        self.browser = WebView()

        # adding action when loading is finished
        self.browser.loadFinished.connect(self.update_title)

        # creating QToolBar for navigation
        navtb = QToolBar("Navigation")

        self.addToolBar(navtb)
        done_btn = QAction('Close', self)
        done_btn.setStatusTip('Close Reader')
        done_btn.triggered.connect(self.done)
        navtb.addAction(done_btn)

        bookurl = QUrl.fromLocalFile(mydir + '/cloud-reader-lite/index.html')
        bookurl.setQuery('epub=epub_content/ebook/')
        self.browser.setUrl(bookurl)

        # set this browser as central widget or main window
        self.setCentralWidget(self.browser)

        self.readsettings()
        self.show()

    def readsettings(self):
        settings = QSettings('Sigil','ReaderPlugin')
        if settings.value('geometry', None):
            self.restoreGeometry(settings.value('geometry'))

    # method for updating the title of the window
    def update_title(self):
        if not self.browser or not self.browser.isVisible():
            return;
        height = self.browser.height()
        width =    self.browser.width()
        # title = self.browser.page().title()
        self.setWindowTitle('Screen Size:'  +  ' (%dx%d)' % (width, height))

    def done(self):
        self.close()

    def resizeEvent(self, ev):
        QMainWindow.resizeEvent(self, ev)
        self.update_title()

    def closeEvent(self, ev):
        settings = QSettings('Sigil','ReaderPlugin')
        settings.setValue('geometry', self.saveGeometry())
        QMainWindow.closeEvent(self, ev)


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


# This is simply: setup_highdpi(bk._w.highdpi) in a Sigil plugin
# without all the extra argparse stuff.
highdpi_choices = ['detect', 'on', 'off']
highdpi = 'detect'
parser = argparse.ArgumentParser()
parser.add_argument('-d', '--highdpi', default='detect')
args = parser.parse_args()
if args.highdpi and args.highdpi.lower() in highdpi_choices:
    highdpi = args.highdpi.lower()
    print(highdpi)
# end plugin simulation stuff
if not ismacos:
    # setup_highdpi(bk._w.highdpi)
    setup_highdpi(highdpi)

# creating a pyQt5 application
app = QApplication(sys.argv)

# setting name to the application
app.setApplicationName("Readium Cloud Reader Lite Demo")

# creating a main window object
window = MainWindow()

# loop
app.exec_()

**[Plugin] ReadiumReader - a version of Readium's Cloud-Reader-LITE for Sigil **

Updated: August 2, 2023

Current Version: "0.4.1"

This plugin implements an epub3 reader for the epub currently being edited in Sigil.
It uses PyQt5 and PyQtWebengine or PySide6 to create a browser like main window and then loads
Readium's cloud-reader-LITE from Readium's js-viewer project to implement the epub reader.

See https://github.com/readium/readium-js-viewer

License/Copying: The Readium code is covered by its own BSD 3-clause license:

Copyright (c) 2014 Readium Foundation and/or its licensees. All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
3. Neither the name of the organization nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


License/Copying: The actual python code used to create this plugin is covered under the GNU LGPL Version 2 or Version 3, your choice.  Any other license terms are only available directly from the authors of Sigil in writing.

Minimum Sigil Version: support for this plugin is provided for Sigil 1.6.0 and later using the Python 3.6 or later Python interpreter.


See the Sigil Plugin Index on MobileRead to find out more about this plugin and other plugins available for Sigil:
https://www.mobileread.com/forums/showthread.php?t=247431

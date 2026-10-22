# -*- coding: utf-8 -*-
"""Get the real page of every table-of-contents bookmark using Word COM."""
import win32com.client as win32
import pythoncom

from common import DOCX, write_json

pythoncom.CoInitialize()
word = win32.DispatchEx('Word.Application')
word.Visible = False
word.DisplayAlerts = 0
try:
    doc = word.Documents.Open(str(DOCX), ReadOnly=True)
    # actual page for each _Toc bookmark
    actual = {}
    for i in range(1, doc.Bookmarks.Count + 1):
        bm = doc.Bookmarks.Item(i)
        name = bm.Name
        if name.startswith('_Toc'):
            rng = bm.Range
            page = rng.Information(3)  # wdActiveEndPageNumber
            actual[name] = int(page)
    print('bookmarks found:', len(actual))
    write_json("actual_pages.json", actual)
    doc.Close(False)
finally:
    word.Quit()
print(f"saved actual pages to {DOCX.parent.parent / 'results' / 'word_qa'}")

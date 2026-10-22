# -*- coding: utf-8 -*-
"""Get the real page number of every heading in the Word document."""
import win32com.client as win32
import pythoncom

from common import DOCX, write_json

pythoncom.CoInitialize()
word = win32.DispatchEx('Word.Application')
word.Visible = False
word.DisplayAlerts = 0
rows = []
try:
    doc = word.Documents.Open(str(DOCX), ReadOnly=True)
    total = doc.ComputeStatistics(2)  # wdStatisticPages
    print('total pages:', total)
    for i in range(1, doc.Paragraphs.Count + 1):
        p = doc.Paragraphs.Item(i)
        style = p.Style.NameLocal
        if not style.startswith(('Heading', '标题')):
            continue
        text = p.Range.Text.replace('\r', '').replace('\x07', '').strip()
        if not text:
            continue
        page = int(p.Range.Information(3))  # wdActiveEndPageNumber
        rows.append({'style': style, 'text': text, 'page': page})
    doc.Close(False)
finally:
    word.Quit()

print('headings:', len(rows))
write_json("heading_pages.json", rows)
for r in rows[:8]:
    print('  p%-3d %-10s %s' % (r['page'], r['style'], r['text'][:50]))

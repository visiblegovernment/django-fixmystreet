import csv


class UnicodeWriter:
    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        self.writer = csv.writer(f, dialect=dialect, **kwds)
        self.encoding = encoding

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

import sys
import tkinter
from gorushi.browser import Browser
from gorushi.url import URL


if __name__ == "__main__":
    browser = Browser()
    browser.load(URL(sys.argv[1]))
    tkinter.mainloop()

import tkinter
import sys 
import argparse

from gorushi.browser import Browser
from gorushi.url import URL

# recursion limit increase for deep HTML trees
sys.setrecursionlimit(5000)

argparser = argparse.ArgumentParser(
    description="A simple GUI web browser."
)
argparser.add_argument("url")
argparser.add_argument("--width")
argparser.add_argument("--height")
argparser.add_argument("--ltr")
argparser.add_argument("--center")
args = argparser.parse_args()


if __name__ == "__main__":
    browser = Browser(
        width=args.width or 800,
        height=args.height or 600,
        is_ltr=args.ltr != "false",
        center_align=args.center == "true"
    )
    browser.load(URL.parse(args.url))
    tkinter.mainloop()

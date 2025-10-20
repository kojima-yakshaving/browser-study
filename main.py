import sys
from renderer import Renderer
from url import URL


def show(body):
    Renderer(body).render()

def load(url):
    body = url.request()
    show(body)


if __name__ == "__main__":
    load(URL(sys.argv[1]))

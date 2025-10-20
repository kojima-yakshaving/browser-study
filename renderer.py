
class Renderer:
    """
    renders contents of websites which is passed as a string
    """
    content: str

    def __init__(self, content: str):
        self.content = content 

    def render(self):
        in_tag = False
        for c in self.content:
            if c == "<":
                in_tag = True
            elif c == ">":
                in_tag = False
            elif not in_tag:
                print(c, end="")

        

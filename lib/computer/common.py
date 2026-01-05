from discopy import closed

class TitiBox(closed.Box):
    def __init__(self, name, dom, cod, data=None, draw_as_spider=False):
        super().__init__(name, dom, cod, data=data)
        self.draw_as_spider = draw_as_spider

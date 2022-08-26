from services.svg import SVG


class SalesFunnel:

    def __init__(self, path):
        """
        Class for build factor analysis for 
        forecaster site
        Arg:
            path: str - path to final SVG file
        """
        self.path = path
        self.s = SVG()
        self.s.create(400, 400)

    def buildTringle(self):
        self.s.line('#000000', 4, 0, 400, 400, 400)
        self.s.line('#000000', 4, 200, 0, 400, 400)
        self.s.line('#000000', 4, 0, 400, 200, 0)

    def save(self):
        self.s.finalize()
        try:
            self.s.save(self.path)
        except IOError as ioe:
            print(ioe)

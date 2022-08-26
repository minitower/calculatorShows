from svg import SVG
from pathlib import Path
import warnings
import os
from dotenv import load_dotenv

load_dotenv()

class SalesFunnel:

    def __init__(self, shows, clicks, postbacks, 
                 confirmed_postbacks, campaign, path=None):
        """
        Class for build factor analysis for forecaster site. 
        Args shows, clicks, postbacks, confirmed_postbacks depend to area of trapeze.
        
        About SALES_FUNNEL_PATH: firstly script watch for path var in function call. 
        If None whatch for 'SALES_FUNNEL_PATH' env variable. If this variable is None 
        (not in .env) then try default path (${PROJECT_PATH}/static/img/factorAnalysis)
        
        Arg:
            shows: int - shows of campaign
            clicks: int - clicks of campaign
            postbacks: int - postbacks of campaign
            confirmed_postbacks: int - confirmed postbacks of campaign
            campaign: str - name of the campaign (needed only for path)
            path: path-like - path to final SVG file
        """
        # Find and check filepath for SVG file
        if path is None:
            if os.environ.get('SALES_FUNNEL_PATH') is not None:
                self.path = os.environ.get('SALES_FUNNEL_PATH')
            else:
                self.path = Path(os.environ.get('PROJECT_PATH'))\
                    / Path('static/img/factorAnalysis')
        else:
            self.path = Path(path)
        if not os.path.exists(self.path):
            self.path = Path(os.environ.get('PROJECT_PATH'))\
                    / Path('static/img/factorAnalysis')
            if not os.path.exists(self.path):
                print(self.path)
                raise FileNotFoundError("Can't found default path and/or custom user path!")
            else:
                warnings.warn("Path for module 'services.salesFunnel'"
                                    f"is did not exist! Use default path: {self.path}")
        self.path = self.path / Path(f'salesFunnel_{campaign}.svg')
        # Binding main class variable
        self.s = SVG()
        self.shows = shows
        self.clicks = clicks
        self.postbacks = postbacks
        self.confirmed_postbacks = confirmed_postbacks
        # Binding colors of funnel
        self.colorArr = [os.environ.get('SALES_FUNNEL_FIRST_COLOR'),
                          os.environ.get('SALES_FUNNEL_SECOND_COLOR'),
                          os.environ.get('SALES_FUNNEL_THIRD_COLOR'),
                          os.environ.get('SALES_FUNNEL_FOURTH_COLOR')]
        self.baseColor = os.environ.get('SALES_FUNNEL_BASE_COLOR')
        print(self.baseColor)
        
        if self.baseColor is None:
            warnings.warn('Base color of funnel is not defined! Set to #000000 (black)')
            self.baseColor='#000000'
        
        for i in range(len(self.colorArr)):
            if self.colorArr[i] is None:
                self.colorArr[i] = self.baseColor
            
        # Get/calculate main values for creating SVG
        self.w = self.shows # max of lower line of trapeze
        self.h = os.environ.get('SALES_FUNNEL_HEIGTH_SECTOR')
        if self.h is None:
            self.h = 100
        else:
            try:
                self.h = int(self.h)
            except TypeError:
                warnings.warn("Can't apply SALES_FUNNEL_HEIGTH_SECTOR (not a number)! Set default value (100)")
                self.h = 100 # 100(default)
        if os.environ.get('SALES_FUNNEL_EQUILATERAL_TRIANGLE') is not None:
            self.eqLastSector=bool(os.environ.get('SALES_FUNNEL_EQUILATERAL_TRIANGLE'))
        else:
            self.eqLastSector=True
        
        self.lastSectorHeigth = os.environ.get('SALES_FUNNEL_UPPER_SECTOR_HEIGTH')
        try:
            self.lastSectorHeigth = int(self.lastSectorHeigth)
        except TypeError:
            warnings.warn("Can't apply SALES_FUNNEL_UPPER_SECTOR_HEIGTH (not a number)! Set default value (100)")
            self.lastSectorHeigth = 100
            
        # Scaling funnel
        while self.w >= 2000:
            self.shows = shows/2
            self.clicks = clicks/2 # divide all variable for stay CR, CTR and approve the same
            self.postbacks = postbacks/2 # divide all variable for stay CR, CTR and approve the same
            self.confirmed_postbacks = confirmed_postbacks/2 # divide all variable for stay CR, CTR and approve the same
            self.w = self.shows
        # Create SVG file in RAM
        self.s.create(self.w, self.h*3+self.lastSectorHeigth)
        
    def baseDotCalc(self):
        """
        Calc for (x0, y0) of each sector of funnel. Main rulex is:
            x0: previous x0 plus difference betwen lower line (bigger) and upper line
            y0: previous y0 plus heigth (determinating)
        """
        self.x0_clicks = 0+((self.shows-self.clicks)/2) # x0 plus difference betwen lower line(bigger) and upper line
        self.y0_clicks = 0+self.h # always equale to y0 plus heigth(determinating)
        self.x0_post = self.x0_clicks+((self.clicks-self.postbacks)/2)
        self.y0_post = self.y0_clicks+self.h
        self.x0_postConf = self.x0_post+((self.postbacks-self.confirmed_postbacks)/2)
        self.y0_postConf = self.y0_post+self.h
        
    def buildFunnel(self):
        """
        Function for build 4 sector of sales funnel
        """
        self.baseDotCalc() # Calculate value for (x0, y0) of sectors
        self.s.trapeze(self.colorArr[0], 4, 0, 0, self.h, self.shows, self.clicks)
        self.s.trapeze(self.colorArr[1], 4, self.x0_clicks, self.y0_clicks, self.h, 
                                self.clicks, self.postbacks)
        self.s.trapeze(self.colorArr[2], 4, self.x0_post, self.y0_post, self.h, 
                                self.postbacks, self.confirmed_postbacks)
        if self.eqLastSector:
            self.s.eqTriangle(self.colorArr[3], 4, 
                              self.x0_postConf, 
                              self.y0_postConf, 
                              base=self.confirmed_postbacks) # side of triangle equal to number of confirmed postbacks 
        else:
            self.s.isoTriangle(self.colorArr[3], 4, 
                               self.x0_postConf, 
                               self.y0_postConf,
                               base=self.confirmed_postbacks,
                               h=self.lastSectorHeigth)

    def save(self):
        self.s.finalize()
        try:
            self.s.save(self.path)
        except IOError as ioe:
            print(ioe)

if __name__ == "__main__":
    os.environ.setdefault('PROJECT_PATH',
                          str(os.path.dirname(os.path.abspath(__file__)) / 
                          Path('./../')))
    sf = SalesFunnel(shows=100, clicks=50, postbacks=35, 
                     confirmed_postbacks=20, campaign='RU_test')
    sf.buildFunnel()
    sf.save()
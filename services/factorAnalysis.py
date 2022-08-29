from salesFunnel import *
from dotenv import load_dotenv
import os

class FactorAnalysis:
    def __init__(self, campaign, shows_current, clicks_current, postbacks_current,
                 conf_postbacks_current, shows_forecast, clicks_forecast, 
                 postbacks_forecast, conf_postbacks_forecast):
        """
        Class for build factor analysis HTML page with all nercesury 
        SVG files.
        
        Args:
            shows_current: int - median value of daily shows in current 
                campaign
            clicks_current: int - median value of daily clicks in current 
                campaign
            postbacks_current: int - median value of daily postbacks in current 
                campaign
            conf_postbacks_current - median value of daily confirmed postbacks 
                in current campaign
            shows_forecast: int - median value of daily shows in forecast 
                model prediction
            clicks_forecast: int - median value of daily clicks in forecast 
                model prediction
            postbacks_forecast: int - median value of daily postbacks in forecast 
                model prediction
            conf_postbacks_forecast: int - median value of daily confirmed postbacks  
                in forecast model prediction
        """
        self.campaign = campaign
        self.shows_current = shows_current
        self.clicks_current = clicks_current
        self.postbacks_current = postbacks_current
        self.conf_postbacks_current = conf_postbacks_current
        self.shows_forecast = shows_forecast
        self.clicks_forecast = clicks_forecast
        self.postbacks_forecast = postbacks_forecast
        self.conf_postbacks_forecast = conf_postbacks_forecast
        self.diff_shows = self.shows_forecast - self.shows_current
        self.diff_clicks = self.clicks_forecast - self.clicks_current
        self.diff_postbacks = self.postbacks_forecast - self.postbacks_current
        self.diff_conf_postbacks = self.conf_postbacks_forecast - self.conf_postbacks_current
        self.current_filename = f'currentSalesFunnel_{self.campaign}.svg'
        self.forecast_filename = f'forecastSalesFunnel_{self.campaign}.svg'
        
    def buildCurrentFunnel(self):
        """
        Function for build current sales funnel in 
        SVG file. 
        """
        sf = SalesFunnel(shows=self.shows_current, clicks=self.clicks_current, 
                         postbacks=self.postbacks_current, confirmed_postbacks=self.conf_postbacks_current, 
                         campaign=self.campaign, filename=self.current_filename)
        sf.buildFunnel()
        sf.addInfo()
        sf.save()
        
    def buildForecastFunnel(self):
        """
        Function for build forecast sales funnel in
        SVG file.
        """
        sf = SalesFunnel(shows=self.shows_forecast, clicks=self.clicks_forecast, 
                         postbacks=self.postbacks_forecast, confirmed_postbacks=self.conf_postbacks_forecast, 
                         campaign=self.campaign, filename=self.forecast_filename)
        sf.buildFunnel()
        sf.addInfo()
        sf.save()
        
if __name__ == "__main__":
    load_dotenv()
    os.environ.get('PROJECT_PATH')
    fa = FactorAnalysis('RU_test', shows_current=100, clicks_current=50, 
                        postbacks_current=25, conf_postbacks_current=15,
                        shows_forecast=1000, clicks_forecast=500, 
                        postbacks_forecast=250, conf_postbacks_forecast=150)
    fa.buildCurrentFunnel()
    fa.buildForecastFunnel()
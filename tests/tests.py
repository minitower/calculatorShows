import requests
import socket
from pathlib import Path
import os
import json
from dotenv import load_dotenv

load_dotenv()

class Test_model_answers:
    
    def __init__ (self, resultPath=None, test_arr=None):
        """
        Class for automatic (almost) test of model answer.
        Check some random campaign and change parameters. Sort result
        by category:
            1. tests/results/down - if forecast of shows goes down
            2. tests/results/up - if forecast of shows goes up
        For every test make dir with plot of shows, Data Frames with data and 
        result table
        
        Args:
            resultPath: path-like - path to storage with analysis result
            test_arr: arr with tuples - list with calculation parameters like
                    (campaign,cpa,approve)
        """
        os.environ.setdefault('PROJECT_PATH', os.path.dirname(os.path.abspath(__file__)))
        self.resultPath=Path(os.environ.get("PROJECT_PATH")) \
                            /Path(os.environ.get('RESULT_PATH'))
        self.testPath=os.path.dirname(os.path.abspath(__file__))
        self.test_arr=test_arr
        self.local=bool(os.environ.get('LOCAL'))
        self.production=bool(os.environ.get('PRODUCTION'))
        self.port=os.environ.get('PORT')
    
    def getLocalIP(self):
        """
        Service function for find local IP by DNS socket connect.
        Needed to find address of tested machine
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        addr = s.getsockname()[0]
        s.close()
        return addr
      
    def requestToServer(self, campaign: str | int, 
                                cpa: int, approve: float,
                                pred_n: int, accurancy: float):
        """
        Function for build POST query to http://host:port
        
        Args:
            campaign: str | int - campaign name
            cpa: int - user custom bid
            cpa: int - user custom approve
        """        
        if self.local and os.environ.get('LOCAL') is not None:
            domain='http://127.0.0.1'
            port='5000'
        elif self.production and os.environ.get('PRODUCTION') is not None:
            domain=f'http://{self.getLocalIP()}'
            port='8080'
        url=f'{domain}:{port}?campaignId={str(campaign)}&approve={str(approve)}&cpa='\
                    f'{str(cpa)}&accurancy={str(accurancy)}&pred_n={str(pred_n)}'
        self.response = requests.post(url=url, data=None)
        return self.response
        
    def parseResult(self, res):
        """
        Export result from JSON response to local or 
        class variable and preprocessed it (if this is nercessury)
        """
        j=json.loads(res.content)
        # Bind main class variable
        self.userApprove=j['input_data']['userApprove']
        self.userCPA=j['input_data']['userBid']
        self.accurancy=j['model_data']['accurancy']
        self.forecastPostbacks=j['approve_check']['postbacks_forecast']
        self.forecastConfirmedPostbacks=j['approve_check']['conf_postbacks_forecast']
        #Binding pathes to main file
        self.factorAnalysis=j['pathes']['factorAnalysis'] # TODO Change encoding of variables
        self.plotNameShows=j['pathes']['plotNameShows']
        self.tableName=j['pathes']['tableName']
        # Binding local variable
        trendShows=j['trend']['shows']
        campaign=j['input_data']['campaign']
        
        
        if trendShows<=0:
            n=0
            while os.path.exists(Path(os.environ.get('PROJECT_PATH')) / Path(f'tests/results/down/{campaign}_{n}')):
                n+=1
            dirPath = Path(os.environ.get('PROJECT_PATH')) / Path(f'tests/results/down/{campaign}_{n}')
            os.mkdir(dirPath)
            # Copy main files to the result dir
            with open(self.factorAnalysis, 'r+') as f:
                tmp=f.read()
                f.close()
                
            with open(dirPath/Path('funnel.svg'), 'w+') as f:
                f.write(tmp)
                f.close()
                
            with open(self.plotNameShows, 'r+') as f: # TODO fill result with plot and table
                tmp=f.read()
                f.close()
        else: 
            pass # TODO add result of analysis for upper trend

        

        
        
if __name__ == "__main__":
    Test_model_answers()
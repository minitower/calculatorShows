from email import message
import os
from sqlite3 import Timestamp
import flask
from datetime import datetime
import uuid

class Loger:
    
    def __init__(self, full_model=None, full_server=None,
                        full_services=None, short=None,
                        reqPath=None, dataPath=None):
        """
        Class for init loger with pathes to main log file
        in server. Each path have default value and can be
        undefined.
        """
        if not full_model:
            self.full_model='logs/full_logs/model_log.log'
        else:
            self.full_model = full_model
            
        if not full_server:
            self.full_server='logs/full_logs/server_log.log'
        else:
            self.full_server = full_server
            
        if not full_services:
            self.full_services='logs/full_logs/services_log.log'
        else:
            self.full_services = full_services
            
        if not short:
            self.short='logs/short.log'
        else:
            self.short = short
            
        if not dataPath:
            self.dataPath='logs/res/'
        else:
            self.dataPath=dataPath
            
        if not reqPath:
            self.reqPath='logs/req.log'
        else:
            self.reqPath=reqPath
            
        
    def writeInFile(self, message: str, path: str):
        """
        Main func for write some log message in some 
        level of log:

        Args:
            message: str - message to log file
            mode: str - one of ['model', 'server', 'services', 'short']
        """
        if not os.path.exists(path):
            with open(path, 'w+') as f:
                f.close()
        else:
            with open(path, 'a+') as f:
                f.write(message)
                f.close()
                
    def requestMessage(self, req: flask.Request):
        """
        Build message with main headers of the request and
        write it in full_log/server_log.log and short_log
        
        Args
            req: request - request from client
        """
        path=req.__str__().split("'")[1]
        method=req.__str__().split("[")[1].replace(']', '')\
                            .replace('>', '')
        sendArguments=req.args.__str__()
        endpoint=req.args.__str__()
        userAgent=req.user_agent.__str__()
        reqUUID=uuid.uuid4().__str__()
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')
        reqTemplate=f"""
            {timestamp}: {method} method in request {reqUUID} to path {path}:\n
                1. args in request: {sendArguments};\n
                2. Python func in server.py (endpoint): {endpoint};\n
                3. User agent: {userAgent};\n
        _________________________________________________________________________________________\n\n\n
        """
        self.writeInFile(reqTemplate, self.full_server)
        
        req2=f"""
            {timestamp}: {req.__str__()}
        """
        self.writeInFile(req2, self.full_server)
    
    def shortRequestMessage(self, req: flask.Request):
        """
        Build message with main headers of the request and
        write it in full_log/server_log.log and short_log
        
        Args
            req: request - request from client
        """
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')
        self.writeInFile(timestamp+': '+req.__str__()+'\n', self.short)
    
    def responseMessage(self, res: flask.Response):
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')
        htmlUUID = uuid.uuid4()
        dataPath=self.dataPath+htmlUUID.__str__()+'.html'
        with open(dataPath, 'wb') as f:
            f.write(res.get_data())
        resTemplate=f"""
            {timestamp}: response with status {res.status} ({res.status_code}):\n
                1. Headers: {res.headers};\n
                2. HTML data path: {dataPath};\n
        _________________________________________________________________________________________\n\n\n
        """
        self.writeInFile(resTemplate, self.full_server)
        
    def shortResponseMessage(self, res: flask.Response):
        """
        Build message with main headers of the request and
        write it in full_log/server_log.log and short_log
        
        Args
            req: request - request from client
        """
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')
        self.writeInFile(timestamp+': '+res.__str__()+'\n', self.short)
        
    def calcStart(self):
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')
        message = f"""
            {timestamp}: model calc start
        """
        self.writeInFile(message, self.full_model)
        
    def mainStart(self):
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')
        message = f"""
            {timestamp}: main.py script started
        """
        self.writeInFile(message, self.full_model)
    
    def tableLoad(self):
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')
        message = f"""
            {timestamp}: table download
        """
        self.writeInFile(message, self.full_model)
        
    def campaignIdFound(self, campaignName):
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')
        message = f"""
            {timestamp}: model find campaign name {campaignName}
        """
        self.writeInFile(message, self.full_model)
        
    def statLoad(self, dictStat):
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')
        stats=''
        for i in dictStat.keys():
            tmp = f"{i}: {dictStat[i]}\n"
            stats.join(tmp)
        message = f"""
            {timestamp}: model export stat from ClickHouse:\n{stats}
        """
        self.writeInFile(message, self.full_model)
    
    def mainStatCalc(self, dictStat):
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')
        stats=''
        for i in dictStat.keys():
            tmp = f"{i}: {dictStat[i]}\n"
            stats.join(tmp)
        message = f"""
            {timestamp}: model calculate stat for campaign:\n{stats}
        """
        self.writeInFile(message, self.full_model)
        
    def optFind(self, opt):
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')
        stats=''
        dictOpt = {'alpha': opt[0],
                   'beta': opt[1], 
                   'gamma': opt[2]}
        for i in dictOpt.keys():
            tmp = f"{i}: {dictOpt[i]}\n"
            stats.join(tmp)
        message = f"""
            {timestamp}: model find optimal vector:\n{stats}
        """
        self.writeInFile(message, self.full_model)
        
    def mainEnd(self):
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')
        message = f"""
            {timestamp}: main.py finish
        """
        self.writeInFile(message, self.full_model)
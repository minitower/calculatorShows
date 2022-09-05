from asyncio import streams
from http import server
import os
import flask
from datetime import datetime
import uuid

class Loger:
    
    def __init__(self, full_model=None, full_server=None,
                        full_services=None, short=None,
                        streamPath=None):
        """
        Class for init loger with pathes to main log file
        in server. Each path have default value and can be
        undefined.
        """
        if not full_model:
            self.full_model='../logs/full_logs/model_log.log'
        else:
            self.full_model = full_model
            
        if not full_server:
            self.full_server='../logs/full_logs/model_log.log'
        else:
            self.full_server = full_server
            
        if not full_services:
            self.full_services='../logs/full_logs/model_log.log'
        else:
            self.full_services = full_services
            
        if not short:
            self.short='../logs/full_logs/model_log.log'
        else:
            self.short = short
        
        if not streamPath:
            self.streamPath='../logs/streams/'
        else:
            self.streamPath=streamPath
        self.mode_translate = {'model': self.full_model,
                               'server': self.full_server,
                               'services':self.full_services,
                               'short': self.short,
                               'streamPath': self.streamPath}
            
        
    def writeInFile(self, message: str, mode: str):
        """
        Main func for write some log message in some 
        level of log:

        Args:
            message: str - message to log file
            mode: str - one of ['model', 'server', 'services', 'short']
        """
        if not os.path.exists(self.mode_translate[mode]):
            with open(self.mode_translate[mode], 'w+') as f:
                f.close()
        else:
            with open(self.mode_translate[mode], 'a+') as f:
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
        stream=req.stream
        reqUUID=uuid.uuid4().__str__()
        streamUUID=uuid.uuid4().__str__()
        streamFilename = self.streamPath+streamUUID.__str__()+'.stream'
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')
        with open(streamFilename, 'wb') as f:
            f.write(stream)
        reqTemplate=f"""
            {timestamp}: {method} method in request {reqUUID} to path {path}:\n
                1. args in request: {sendArguments};\n
                2. Python func in server.py (endpoint): {endpoint};\n
                3. User agent: {userAgent};\n
                4. Stream filename: {streamFilename};\n
                5. Stream UUID: {streamUUID};\n
        """
        self.writeInFile(reqTemplate, 'server')
    
    def responseMessage(self, res: flask.Response):
        return None
        
        
        
if __name__ == "__main__":
    loger = Loger()
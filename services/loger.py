import os
import flask

class Loger:
    
    def __init__(self, full_model=None, full_server=None,
                        full_services=None, short=None):
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
        self.mode_translate = {'model': self.full_model,
                               'server': self.full_server,
                               'services':self.full_services,
                               'short': self.short}
            
        
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
        ip
        
if __name__ == "__main__":
    loger = Loger()
import pandas as pd
import clickhouse_driver as ch

class Checker:
    def __init__(self, campaignId=None, campaignName=None):
        self.campaignId = campaignId
        self.campaignName =- campaignName
        
    def checkId(self):
        with open('./queries/check/q_campaign_check.sql', 'r') as f:
            q = f.read()

        sqlCH = ch.Client(host="192.168.235.72",
                            user="valferov",
                            password="bUfMupl1kDgK1337")

        df = pd.DataFrame(sqlCH.execute(q))
        if df.loc[df[0]==self.campaignId].empty:
            return False
        else:
            return True
    
    def checkName(self):
        with open('./queries/check/q_name_check.sql', 'r') as f:
            q = f.read()

        sqlCH = ch.Client(host="192.168.235.72",
                            user="valferov",
                            password="bUfMupl1kDgK1337")

        df = pd.DataFrame(sqlCH.execute(q))
        if df.loc[df[0]==self.campaignName].empty:
            return False
        else:
            return True
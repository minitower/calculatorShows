import pandas as pd
import clickhouse_driver as ch
import os


class CPASimulator():

    def __init__(self, campaign_name, custom_bid):
        self.host = os.environ.get("HOST")
        self.user = os.environ.get("CLICKHOUSE_USERNAME")
        self.password = os.environ.get("PASSWORD")
        self.campaign_name = campaign_name
        if custom_bid != 0:
            self.custom_bid = custom_bid
        else:
            self.custom_bid = None

    def margin(self):
        with open('model/queries/simQueryCampaign.sql', 'r') as f:
            q = f.read()
        q = q.replace('${NAME}', self.campaign_name)
        sqlCH = ch.Client(host=self.host,
                          user=self.user,
                          password=self.password)
        df = sqlCH.execute(q)[0][0]
        return df

    def calcGrow(self, df):
        margin = self.margin()
        if self.custom_bid:
            incr = (self.custom_bid - df['cpa']) * margin
        else:
            incr = 0
        df['new_shows'] = df['shows'] + incr
        print(df)
        return df

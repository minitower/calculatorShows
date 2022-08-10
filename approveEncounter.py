import pandas as pd
import clickhouse_driver as ch
import os


def loadData(host, user, password, user_approve, interval=100):
    sql = ch.Client(host=host, user=user, password=password)
    with open('./queries/qForApproveEncount.sql', 'r') as f:
        q = f.read()
    q=q.replace('${APPROVE}', str(user_approve))
    q=q.replace('${INTERVAL}', str(interval))
    df=pd.DataFrame(sql.execute(q))
    if df.empty:
        loadData(host=host, user=user,
                 password=password, user_bid=user_approve, 
                 interval=interval+100)
    else:
        df.columns = ['campaign_name', 'shows']
        return df
    
def findRelevantCam(df, campaign):
    geo = campaign[0:2]
    if df.loc[df['campaign_name'].str.startswith(geo, na=False)].empty:
        return df
    else:
        return df.loc[df['campaign_name'].str.startswith(geo, na=False)]
    
    
def appEnc(campaign, user_approve):
    host=os.environ.get('HOST')
    user=os.environ.get('CLICKHOUSE_USERNAME')
    password=os.environ.get('PASSWORD')
    df = loadData(host=host, user=user,
             password=password, user_approve=user_approve)
    df = findRelevantCam(df, campaign=campaign)
    return df['shows'].mean()
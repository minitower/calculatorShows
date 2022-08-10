import pandas as pd
import clickhouse_driver as ch
import os



def loadData(host, user, password, user_bid, interval=100):
    sql = ch.Client(host=host, user=user, password=password)
    with open('./queries/qForCpaEncount.sql', 'r') as f:
        q = f.read()
    q=q.replace('${BID}', str(user_bid))
    q=q.replace('${INTERVAL}', str(interval))
    df=pd.DataFrame(sql.execute(q))
    if df.empty:
        loadData(host=host, user=user,
                 password=password, user_bid=user_bid, 
                 interval=interval+100)
    else:
        df.columns = ['campaign_name', 'shows']
        print(df)
        return df
    
def findRelevantCam(df, campaign):
    geo = campaign[0:2]
    if df.loc[df['campaign_name'].str.startswith(geo, na=False)].empty:
        return df
    else:
        return df.loc[df['campaign_name'].str.startswith(geo, na=False)]
    
    
def cpaEnc(campaign, user_bid):
    host=os.environ.get('HOST')
    user=os.environ.get('CLICKHOUSE_USERNAME')
    password=os.environ.get('PASSWORD')
    df = loadData(host=host, user=user,
             password=password, user_bid=user_bid)
    df = findRelevantCam(df, campaign=campaign)
    return df['shows'].mean()
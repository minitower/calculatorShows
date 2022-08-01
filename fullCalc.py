# Open libs
import pandas as pd
import clickhouse_driver as ch
from dotenv import load_dotenv
import os

# Project script
from main import *

def loadCheckData(host, user, password, 
                            bid, ecpm, step):
    campaignsPriority = ['RU', 'KZ', 'UA', 'BY']

    with open('./queries/q2.sql', 'r') as f:
        q = f.read()
    q=q.replace('${BID}', str(bid))

    sqlCH = ch.Client(host=host,
                        user=user,
                        password=password)

    df = pd.DataFrame(sqlCH.execute(q))
    df.columns = ['campaigns', 'adv_id', 'shows', 
                'postbacks', 'ecpm']
    df['diff'] = abs(df['ecpm']-ecpm)
    df['geo'] = df['campaigns'].apply(lambda x: x[:2])
    df_diff = df.loc[df['diff'] == df['diff'].min()]
    for i in campaignsPriority:
        check = df_diff.loc[df_diff['geo'] == i]
        if not check.empty:
            campaigns = check['campaigns'].values[0+step]
            break
    if campaigns is None:
        campaigns = df_diff.sort_values(by='shows', 
                                        ascending=False)['campaigns'].values[0+step]
    return campaigns

def resultParser(result):
    print(result[0])
    print(result[1])
    print(result[2])
    print(result[3])
    print(result[4])
    print(result[5])
    print(result[6])
    print(result[7])
    print(result[8])
    return dict(accurancy=result[0], mean=result[1], 
                std=result[2], median=result[3],
                pred_n=result[4], alpha=result[5], 
                beta=result[6], gamma=result[7], 
                sumShows=result[8])

def fullCalc(bid, approve, cr, ctr, 
                pred_n, minAccurancy, 
                ecpm, step=0):
    load_dotenv()
    host=os.environ.get("HOST")
    user=os.environ.get("CLICKHOUSE_USERNAME")
    password=os.environ.get("PASSWORD")
    campaign = loadCheckData(host=host, 
                                user=user, 
                                password=password, 
                                bid=bid, 
                                ecpm=ecpm,
                                step=step)
    result = main(campaign=campaign, 
                pred_n=pred_n, 
                minAccurancy=minAccurancy,
                full=True)
    
    if result[-1] == 'error 2':
        fullCalc(bid=bid, approve=approve, cr=cr, ctr=ctr,
                    pred_n=pred_n, minAccurancy=minAccurancy,
                    ecpm=ecpm, step=step+1)
    else:
        paramDict = resultParser(result=result)
        paramDict.update(dict(campaign=campaign, sumClicks=paramDict['sumShows']*ctr, 
                            sumPostbacksUnconf=paramDict['sumShows']*ctr*cr,
                            sumPostbacksConf=paramDict['sumShows']*ctr*cr*approve))
        print(paramDict)
        return paramDict

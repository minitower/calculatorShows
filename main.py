import pandas as pd
import clickhouse_driver as ch
from dotenv import load_dotenv
import os
from scipy.optimize import minimize
import plotly.graph_objects as go
from sklearn.metrics import accuracy_score

from hw import HoltWinters
from cross_val import CVScore


def loadData(host, user, password, campaign_name):
    
    if campaign_name:
        with open('./queries/q.sql', 'r') as f:
            q = f.read()
        q=q.replace('${NAME}', campaign_name)
    print(q)

    sqlCH = ch.Client(host=host,
                        user=user,
                        password=password)

    df = pd.DataFrame(sqlCH.execute(q))
    df.columns = ['datetime', 'campaings', 'shows']
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.sort_values('datetime')
    df = df.drop(df.loc[df['shows'] == 0].index)\
            .drop(df.index.values[-5:])\
            .reset_index().drop('index', axis=1)
    return df

def loadDataLocal(path, campaign_name):
    df = pd.read_csv(path).drop('Unnamed: 0', axis=1)
    df.columns = ['datetime', 'campaings', 'shows']
    df = df.loc[df['campaings'] == campaign_name]
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.sort_values('datetime')
    df = df.drop(df.loc[df['shows'] == 0].index)\
            .drop(df.index.values[-5:])\
            .reset_index().drop('index', axis=1)
    return df

def paramInit(df):
    x=[0,0,0]
    timeseriesCV = CVScore(df['shows'])
    opt = minimize(timeseriesCV.timeseriesCVscore, x0=x, method='TNC', 
                    bounds=((0, 1), (0, 1), (0, 1)), options={'maxiter': 10000})
    return opt

def HWPredict(df, opt, n_preds):
    hw = HoltWinters(df['shows'], slen=24, alpha=opt.x[0], 
                    beta=opt.x[1], gamma=opt.x[2], n_preds=n_preds,
                    scaling_factor=2.56)
    hw.triple_exponential_smoothing()
    return hw

def validation(df, hw):
    validation = pd.DataFrame(dict(shows= df['shows'], predict=hw.result))
    validation['SSR'] = (validation['shows'] - validation['predict'])**2
    validation['SST'] = (validation['shows'] - validation['shows'].mean())**2
    check = validation['SSR'].sum()/validation['SST'].sum()
    return check

def forecast(df, opt, n_preds):
    hw_forecast = HWPredict(df, opt, n_preds)

    forecast_arr = []
    for i in range(-n_preds):
        forecast_arr.append(df['datetime'].values[-1]+pd.Timedelta(hours=i))
    forecast = pd.DataFrame(forecast_arr, columns=['datetime'])
    forecast['forecast'] = hw_forecast.result[-n_preds:]
    return forecast

def plotBuilder(df, campaign, check, hw, n_preds, forecast, save=True):
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=df['datetime'].values, 
                            y=df['shows'].values,
                            name=f'Campaigns {campaign[0]}'))

    fig.add_trace(go.Scatter(x=df['datetime'].values,
                                y=hw.result, name='predict'))

    fig.add_trace(go.Scatter(x=forecast['datetime'].values, 
                            y=forecast['forecast'].values,
                            name=f'forecast for {n_preds} values'))
    fig.update_layout(
        font_family="Courier New",
        title_text=f'Forecast for campaign {campaign[0]} with accurancy {round(100-check, 10)}%'
    )
    fig.write_html(f'plots/plot_{campaign}.html')
    if save:
        fig.write_html(f'templates/plot_{campaign}.html')



def main(campaign):
    #WARN: for this script is nercessury: 
    #1. Data length must be more then 24 dots (1 dot==1 hour)
    # Load enviroment variables
    load_dotenv()
    # Load program constant
    host=os.environ.get("HOST")
    user=os.environ.get("CLICKHOUSE_USERNAME")
    password=os.environ.get("PASSWORD")
    print('Loading data...')
    print(campaign)
    # Load data from database
    df = loadDataLocal('./test.csv', campaign)
    #df = loadData(host=host, user=user, password=password,
    #                campaign_name=campaign)
    print(df)
    print('Load data is succsessful!')
    if df.empty:
        return ['error']
    mean=df['shows'].mean()
    std=df['shows'].mean()
    median=df['shows'].median()
    n_preds=10
    # Optimise Holt-Winters vector
    opt = paramInit(df)
    alpha=opt.x[0]
    beta=opt.x[1]
    gamma=opt.x[2]
    print('Find optimal parameters!')
    # Predict value for custom data
    hw = HWPredict(df, opt, 0)
    print('Predict is complete!')
    check = validation(df, hw)
    accurancy=round(1-check, n_preds)
    print(f'Validation is complete! R^2 is {1-check}')
    predict = forecast(df, opt, 24)
    df_save = pd.concat([df[['datetime', 'shows']], predict[['datetime', 'forecast']]])
    campaignSave=campaign.replace(' | ', '_')
    with open(f'./templates/table_{campaignSave}.html', 'w+') as f:
        f.write(df_save.to_html())
    #Build plot with HW result
    plotBuilder(df, campaignSave, check, hw, n_preds, predict)
    print(f'Plot saved on plots/plot_{campaignSave}.html')
    return [accurancy, mean, std, median,
        n_preds, alpha, beta, gamma]
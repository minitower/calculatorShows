import imp
from flask import *
import pickle
import os
from pathlib import Path
import warnings
from clickhouse_driver.errors import SocketTimeoutError
warnings.simplefilter(action='ignore', category=FutureWarning)

from main import *
from fullCalc import *
from checker import *
from cleaner import envCleaner

app = Flask(__name__)
load_dotenv()

if bool(os.environ.get('SERVER_INFO_CLEAN')) == True:
    print('clean')
    envCleaner('bin')

if bool(os.environ.get('SERVER_PLOT_CLEAN')) == True:
    envCleaner('plot')
    
if bool(os.environ.get('SERVER_TABLE_CLEAN')) == True:
    envCleaner('table')

host=os.environ.get("HOST")
user=os.environ.get("CLICKHOUSE_USERNAME")
password=os.environ.get("PASSWORD")

@app.route('/', methods=['GET', 'POST'])
def fullCalculator():
    if request.method == 'POST':
        custom=request.form.get('custom')
        if not custom:
            campaignId=request.form.get('campaignId')
            campaignName=None
            try:
                int(campaignId)
            except ValueError:
                campaignName=request.form.get('campaignId')
                campaignId=None
            cpa=request.form.get('cpa')
            customApprove=request.form.get('approve')
            if cpa!='':
                try:
                    int(cpa)
                    bid=cpa
                except ValueError:
                    return make_response(
                                    redirect(url_for("valNotFound", 
                                                          value="CPA")))
            else:
                bid=1500
                cpa='none'
            cr=0
            ctr=0
            if customApprove!='':
                try:
                    int(customApprove)
                    approve=customApprove
                except ValueError:
                    return make_response(
                                    redirect(url_for("valNotFound", 
                                                        value="approve")))
            else:
                approve=25
                customApprove='none'
            epc=0
            ecpm=0
        pred_n = int(request.form.get('pred_n'))
        minAccurancy = float(request.form.get('accurancy'))
        try:
            resultDict = fullCalc(bid=bid, approve=approve, cr=cr, 
                        ctr=ctr, epc=epc, ecpm=ecpm, pred_n=pred_n,
                        minAccurancy=minAccurancy,
                        campaignId=campaignId,
                        campaignName=campaignName, 
                        custom_approve=customApprove,
                        custom_bid=cpa)
        except ch.errors.SocketTimeoutError:
            
            
        try:
            if resultDict['err'] == "No shows":
                return make_response(
                            redirect(url_for("valNotFound", 
                                            value="campaign name/id")))
        except KeyError:
            pass
        
        meanClicks=resultDict['meanClicks'] 
        stdClicks=resultDict['stdClicks'] 
        medianClicks=resultDict['medianClicks']
        meanPostbacks=resultDict['meanPostbacks']
        stdPostbacks=resultDict['stdPostbacks']
        medianPostbacks=resultDict['medianPostbacks']
        meanConfirmPostbacks=resultDict['meanConfirmPostbacks']
        stdConfirmPostbacks=resultDict['stdConfirmPostbacks']
        medianConfirmPostbacks=resultDict['medianConfirmPostbacks']

        campaign=resultDict['campaign']
        campaign=campaign.replace(' | ', '_')
        if len(resultDict.values()) == 1:
            res = make_response(redirect('/not_found'))
            res.set_cookie('campaign', campaign)
        else:
            diffShowsForecastUnform = -int(resultDict['median']) + int(int(resultDict['sumShows'])/
                                                                int(resultDict['pred_n']/24))
            if  diffShowsForecastUnform>=0:
                diffShowsCell = 'darkgreen'
                arrPathShows = url_for('static', filename='img/arrowUp.svg')
            else:
                diffShowsCell = 'darkred'
                arrPathShows = url_for('static', filename='img/arrowDown.svg')

            diffClicksForecastUnform = -int(resultDict['medianClicks']) + \
                                                                int(int(resultDict['sumClicks'])/
                                                                int(resultDict['pred_n']/24))
            if  diffClicksForecastUnform>=0:
                diffClicksCell = 'darkgreen'
                arrPathClicks = url_for('static', filename='img/arrowUp.svg')
            else:
                diffClicksCell = 'darkred'
                arrPathClicks = url_for('static', filename='img/arrowDown.svg')

            diffPostForecastUnform = -int(resultDict['medianPostbacks']) + \
                                                                int(int(resultDict['sumPostbacksUnconf'])/
                                                                int(resultDict['pred_n']/24))
            if  diffPostForecastUnform>=0:
                diffPostCell = 'darkgreen'
                arrPathPost = url_for('static', filename='img/arrowUp.svg')
            else:
                diffPostCell = 'darkred'
                arrPathPost = url_for('static', filename='img/arrowDown.svg')

            diffConfPostForecastUnform = -int(resultDict['medianConfirmPostbacks']) + \
                                                                int(int(resultDict['sumPostbacksConf'])/
                                                                int(resultDict['pred_n']/24))
            if  diffConfPostForecastUnform>=0:
                diffConfPostCell = 'darkgreen'
                arrPathConfPost = url_for('static', filename='img/arrowUp.svg')
            else:
                diffConfPostCell = 'darkred'
                arrPathConfPost = url_for('static', filename='img/arrowDown.svg')

            res = make_response(render_template('full_result.html', 
                            bid='{:,}'.format(round(resultDict['bid'], 3)).replace(',', ' '),
                            userBid=cpa,
                            approve='{:,}'.format(round(resultDict['approve'], 3)).replace(',', ' '),
                            userApprove=customApprove,
                            cr='{:,}'.format(round(resultDict['cr'],3)).replace(',', ' '),
                            ctr=round(resultDict['ctr'], 3),
                            epc=round(resultDict['epc'], 3),
                            ecpm=round(resultDict['ecpm'], 3),
                            accurancy=round(resultDict['accurancy'], 3),
                            mean='{:,}'.format(int(resultDict['mean'])).replace(',', ' '), 
                            std='{:,}'.format(int(resultDict['std'])).replace(',', ' '),
                            median='{:,}'.format(int(resultDict['median'])).replace(',', ' '), 
                            meanClicks='{:,}'.format(int(meanClicks)).replace(',', ' '), 
                            stdClicks='{:,}'.format(int(stdClicks)).replace(',', ' '),
                            medianClicks='{:,}'.format(int(medianClicks)).replace(',', ' '), 
                            meanPost='{:,}'.format(int(meanPostbacks)).replace(',', ' '), 
                            stdPost='{:,}'.format(int(stdPostbacks)).replace(',', ' '),
                            medianPost='{:,}'.format(int(medianPostbacks)).replace(',', ' '),
                            meanConfirmPostbacks='{:,}'.format(int(meanConfirmPostbacks)).replace(',', ' '),
                            stdConfirmPostbacks='{:,}'.format(int(stdConfirmPostbacks)).replace(',', ' '),
                            medianConfirmPostbacks='{:,}'.format(int(medianConfirmPostbacks)).replace(',', ' '),
                            predictLength=int(resultDict['pred_n']/24),
                            alpha=round(resultDict['alpha'], 3), 
                            beta=round(resultDict['beta'],3),
                            gamma=round(resultDict['gamma'],3), 
                            tableName=url_for('fullTable', campaign=campaign),
                            backlink=url_for('fullCalculator'),
                            plotNameShows=url_for('fullPlotShows', campaign=campaign),
                            plotNameClicks=url_for('fullPlotClicks', campaign=campaign),
                            plotNamePostbacks=url_for('fullPlotPostbacks', campaign=campaign),
                            campaign=campaign,
                            sumShows='{:,}'.format(int(resultDict['sumShows'])).replace(',', ' '),
                            sumClicks='{:,}'.format(int(resultDict['sumClicks'])).replace(',', ' '),
                            sumPostbacksUnconf='{:,}'.format(int(resultDict['sumPostbacksUnconf'])).replace(',', ' '),
                            sumPostbacksConf='{:,}'.format(int(resultDict['sumPostbacksConf'])).replace(',', ' '), 
                            dailySumShows='{:,}'.format(int(int(resultDict['sumShows'])/int(resultDict['pred_n']/24))).replace(',', ' '),
                            dailySumClicks='{:,}'.format(int(int(resultDict['sumClicks'])/int(resultDict['pred_n']/24))).replace(',', ' '),
                            dailySumPost='{:,}'.format(int(int(resultDict['sumPostbacksUnconf'])/int(resultDict['pred_n']/24))).replace(',', ' '),
                            dailySumConfPost='{:,}'.format(int(int(resultDict['sumPostbacksConf'])/int(resultDict['pred_n']/24))).replace(',', ' '),
                            diffShowsCell=diffShowsCell,
                            diffShowsForecast='{:,}'.format(diffShowsForecastUnform).replace(',', ' '),
                            diffClicksCell=diffClicksCell,
                            diffClicksForecast='{:,}'.format(diffClicksForecastUnform).replace(',', ' '),
                            diffPostCell=diffPostCell,
                            diffPostForecast='{:,}'.format(diffPostForecastUnform).replace(',', ' '),
                            diffConfPostCell=diffConfPostCell,
                            diffConfPostForecast='{:,}'.format(diffConfPostForecastUnform).replace(',', ' '),
                            arrPathShows=arrPathShows, arrPathClicks=arrPathClicks,
                            arrPathPost=arrPathPost, arrPathConfPost=arrPathConfPost))
            
            with open(f'./resultsBin/full_{campaign}.pickle', 'wb') as f:
                    pickle.dump(resultDict, f, protocol=pickle.HIGHEST_PROTOCOL)
            res.set_cookie('plotName', url_for('plot', campaign=campaign))
            res.set_cookie('tableName', url_for('table', campaign=campaign))
            res.set_cookie('campaign', campaign)
            if os.path.exists('./resultsBin/fullCalcListCam.pickle'):
                with open('./resultsBin/fullCalcListCam.pickle', 'rb') as f:
                    campaignDict = pickle.load(f)
                campaignDict.update({campaign: url_for('fullLastResult', campaigns=campaign)})
                with open('./resultsBin/fullCalcListCam.pickle', 'wb') as f:
                    pickle.dump(campaignDict, f, protocol=pickle.HIGHEST_PROTOCOL)
            else:
                campaignDict = {campaign: url_for('fullLastResult', campaigns=campaign)}
                with open('./resultsBin/fullCalcListCam.pickle', 'wb') as f:
                    pickle.dump(campaignDict, f, protocol=pickle.HIGHEST_PROTOCOL)
        return res

    elif request.method == 'GET':
        if os.path.exists('./resultsBin/fullCalcListCam.pickle'):
            with open('./resultsBin/fullCalcListCam.pickle', 'rb') as f:
                fullCalcDict = pickle.load(f)
        else:
            fullCalcDict = {}
        return render_template('full_calculator.html', 
                                    length=len(fullCalcDict), 
                                    links=fullCalcDict)


@app.route('/full_results/<campaigns>', methods=['GET'])
def fullLastResult(campaigns):
    try:
        with open(f'./resultsBin/full_{campaigns}.pickle', 'rb') as f:
            dictArgs = pickle.load(f)
        res = make_response(render_template('full_result.html', 
                            bid='{:,}'.format(round(dictArgs['bid'], 3)).replace(',', ' '),
                            approve='{:,}'.format(round(dictArgs['approve'], 3)).replace(',', ' '),
                            cr='{:,}'.format(round(dictArgs['cr'],3)).replace(',', ' '),
                            ctr=round(dictArgs['ctr'], 3),
                            epc=round(dictArgs['epc'], 3),
                            ecpm=round(dictArgs['ecpm'], 3),
                            accurancy=round(dictArgs['accurancy'], 3),
                            mean='{:,}'.format(round(dictArgs['mean'],3)).replace(',', ' '), 
                            std='{:,}'.format(round(dictArgs['std'], 3)).replace(',', ' '),
                            median='{:,}'.format(round(dictArgs['median'], 3)).replace(',', ' '), 
                            predictLength=int(dictArgs['pred_n']/24),
                            alpha=round(dictArgs['alpha'], 3), 
                            beta=round(dictArgs['beta'],3),
                            gamma=round(dictArgs['gamma'],3), 
                            tableName=url_for('fullTable', campaign=campaigns),
                            backlink=url_for('fullCalculator'),
                            plotNameShows=url_for('fullPlotShows', campaign=campaigns),
                            plotNameClicks=url_for('fullPlotClicks', campaign=campaigns),
                            plotNamePostbacks=url_for('fullPlotPostbacks', campaign=campaigns),
                            campaign=campaigns,
                            sumShows='{:,}'.format(int(dictArgs['sumShows'])).replace(',', ' '),
                            sumClicks='{:,}'.format(int(dictArgs['sumClicks'])).replace(',', ' '),
                            sumPostbacksUnconf='{:,}'.format(int(dictArgs['sumPostbacksUnconf'])).replace(',', ' '),
                            sumPostbacksConf='{:,}'.format(int(dictArgs['sumPostbacksConf'])).replace(',', ' '),
                            dailySumShows='{:,}'.format(int(int(dictArgs['sumShows'])/int(dictArgs['pred_n']/24))).replace(',', ' '),
                            dailySumClicks='{:,}'.format(int(int(dictArgs['sumClicks'])/int(dictArgs['pred_n']/24))).replace(',', ' '),
                            dailySumPost='{:,}'.format(int(int(dictArgs['sumShows'])/int(dictArgs['pred_n']/24))).replace(',', ' '),
                            dailySumConfPost='{:,}'.format(int(int(dictArgs['sumShows'])/int(dictArgs['pred_n']/24))).replace(',', ' ')))
        return res
    except EOFError:
        res = make_response(render_template('fake_result.html', 
                        campaign=campaigns,
                        backlink=url_for('fullCalculator')))
        return res
        
@app.route('/not_found/<campaign>', methods=['GET'])
def notFound(campaign):
    return render_template('false_result.html', 
                            campaign=campaign, 
                            backlink=url_for("fullCalculator"))

@app.route('/info', methods=['GET'])
def info():
    return render_template('info.html')

@app.route('/lastResult', methods=['GET'])
def listResult():
    if os.path.exists('./resultsBin/fullCalcListCam.pickle'):
        with open('./resultsBin/fullCalcListCam.pickle', 'rb') as f:
            fullCalcDict = pickle.load(f)
    else:
        fullCalcDict = {}
    return render_template('last_predict.html', 
                                length=len(fullCalcDict), 
                                links=fullCalcDict)

@app.route("/plot/<campaign>", methods=['GET'])
def plot(campaign):
    plotName = f'{campaign}.html'
    return render_template(f'plots/plot_{plotName}')

@app.route("/table/<campaign>", methods=['GET'])
def table(campaign):
    tableName = f'{campaign}.html'
    return render_template(f'tables/table_{tableName}')

@app.route("/full_plot_shows/<campaign>", methods=['GET'])
def fullPlotShows(campaign):
    plotName = f'{campaign}.html'
    return render_template(f'plots/fullPlot_shows_{plotName}')

@app.route("/full_plot_clicks/<campaign>", methods=['GET'])
def fullPlotClicks(campaign):
    plotName = f'{campaign}.html'
    return render_template(f'plots/fullPlot_clicks_{plotName}')

@app.route("/full_plot_postbacks/<campaign>", methods=['GET'])
def fullPlotPostbacks(campaign):
    plotName = f'{campaign}.html'
    return render_template(f'plots/fullPlot_postbacks_{plotName}')

@app.route("/full_table/<campaign>", methods=['GET'])
def fullTable(campaign):
    tableName = f'{campaign}.html'
    return render_template(f'tables/fullTable_{tableName}')

@app.route("/value_<value>_not_found", methods=['GET'])
def valNotFound(value):
    return render_template('value_not_found.html', 
                            value=value, 
                            backlink=url_for('fullCalculator'))

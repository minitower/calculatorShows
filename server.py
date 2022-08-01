from cv2 import minAreaRect
from flask import *
import pickle
import os
from pathlib import Path

from main import *
from fullCalc import *

app = Flask(__name__)

if bool(os.environ.get('SERVER_INFO_CLEANER')) == True:
    dirTmpFiles = Path('./resultsBin')
    tmpFilesList = [i for i in os.walk('./resultsBin')][-1][-1]
    for i in tmpFilesList:
        os.remove(dirTmpFiles / Path(i))


@app.route("/", methods=['GET', 'POST'])
def forecastServer():
    if request.method == 'POST':
        campaign=request.form.get('campaign')
        pred_n=int(request.form.get('pred_n'))
        minAccurancy=float(request.form.get('accurancy'))
        result = main(campaign, 
                        pred_n=pred_n, 
                        minAccurancy=minAccurancy)
        campaign=campaign.replace(' | ', '_')
        if len(result) == 1:
            res = make_response(redirect('/not_found'))
            res.set_cookie('campaign', campaign)
        else:
            res = make_response(render_template('result.html', 
                            accurancy=result[0],
                            mean=result[1], std=result[2],
                            median=result[3], 
                            predictLength=pred_n,
                            alpha=result[5], 
                            beta=result[6],
                            gamma=result[7], 
                            tableName=url_for('table', campaign=campaign),
                            backlink=url_for('forecastServer'),
                            plotName=url_for('plot', campaign=campaign),
                            campaign=campaign,
                            sumShows=result[8]))
            with open(f'./resultsBin/{campaign}.pickle', 'wb') as f:
                pickle.dump(result, f, protocol=pickle.HIGHEST_PROTOCOL)
            res.set_cookie('plotName', url_for('plot', campaign=campaign))
            res.set_cookie('tableName', url_for('table', campaign=campaign))
            res.set_cookie('campaign', campaign)
            if os.path.exists('./resultsBin/campaignList.pickle'):
                with open('./resultsBin/campaignList.pickle', 'rb') as f:
                    campaignDict = pickle.load(f)
                campaignDict.update({campaign: url_for('lastResult', campaign=campaign)})
                with open('./resultsBin/campaignList.pickle', 'wb') as f:
                    pickle.dump(campaignDict, f, protocol=pickle.HIGHEST_PROTOCOL)
            else:
                campaignDict = {campaign: url_for('lastResult', campaign=campaign)}
                with open('./resultsBin/campaignList.pickle', 'wb') as f:
                    pickle.dump(campaignDict, f, protocol=pickle.HIGHEST_PROTOCOL)
        return res
    elif request.method == 'GET':
        if os.path.exists('./resultsBin/campaignList.pickle'):
            with open('./resultsBin/campaignList.pickle', 'rb') as f:
                campaignDict = pickle.load(f)
        else:
            campaignDict = {}
        return render_template('index.html', length=len(campaignDict), 
                                links=campaignDict, valsFoot=url_for('fullCalculator'))


@app.route('/full_calculator', methods=['GET', 'POST'])
def fullCalculator():
    if request.method == 'POST':
        bid = float(request.form.get('bid'))
        approve = float(request.form.get('approve'))
        approveDim = request.form.get('approveDim')
        cr = float(request.form.get('cr'))
        crDim = request.form.get('crDim')
        ctr = float(request.form.get('ctr'))
        ctrDim = request.form.get('ctrDim')
        if approveDim == '%':
            approve = approve/100
        if crDim == '%':
            cr = cr/100
        if ctrDim == '%':
            ctr = ctr/100
        epc=bid*cr*approve
        ecpm=epc*ctr*10
        print(request.form.get('accurancy'))
        pred_n = int(request.form.get('pred_n'))
        minAccurancy = float(request.form.get('accurancy'))


        #####TODO: make request and func for request with campaign id#####
        campaignId=request.form.get('campaignId')

        resultDict = fullCalc(bid=bid, approve=approve, cr=cr, 
                                ctr=ctr, pred_n=pred_n,
                                minAccurancy=minAccurancy, ecpm=ecpm)
        campaign=resultDict['campaign']
        print(campaign)
        campaign=campaign.replace(' | ', '_')
        print(campaign)
        if len(resultDict.values()) == 1:
            res = make_response(redirect('/not_found'))
            res.set_cookie('campaign', campaign)
        else:
            res = make_response(render_template('result.html', 
                            accurancy=resultDict['accurancy'],
                            mean=resultDict['mean'], std=resultDict['std'],
                            median=resultDict['median'], 
                            predictLength=resultDict['pred_n'],
                            alpha=resultDict['alpha'], 
                            beta=resultDict['beta'],
                            gamma=resultDict['gamma'], 
                            tableName=url_for('fullTable', campaign=campaign),
                            backlink=url_for('forecastServer'),
                            plotName=url_for('fullPlot', campaign=campaign),
                            campaign=campaign,
                            sumShows=resultDict['sumShows'],
                            sumClicks=resultDict['sumClicks'],
                            sumPostbacksUnconf=resultDict['sumPostbacksUnconf'],
                            sumPostbacksConf=resultDict['sumPostbacksConf']))
            with open(f'./resultsBin/full_{campaign}.pickle', 'wb') as f:
                    pickle.dump(resultDict, f, protocol=pickle.HIGHEST_PROTOCOL)
            res.set_cookie('plotName', url_for('plot', campaign=campaign))
            res.set_cookie('tableName', url_for('table', campaign=campaign))
            res.set_cookie('campaign', campaign)
            if os.path.exists('./resultsBin/fullCalcListCam.pickle'):
                with open('./resultsBin/fullCalcListCam.pickle', 'rb') as f:
                    campaignDict = pickle.load(f)
                campaignDict.update({campaign: url_for('fullLastResult', campaign=campaign)})
                with open('./resultsBin/fullCalcListCam.pickle', 'wb') as f:
                    pickle.dump(campaignDict, f, protocol=pickle.HIGHEST_PROTOCOL)
            else:
                campaignDict = {campaign: url_for('fullLastResult', campaign=campaign)}
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

@app.route('/results/<campaign>', methods=['GET'])
def lastResult(campaign):
    try:
        with open(f'./resultsBin/{campaign}.pickle', 'rb') as f:
            listArgs = pickle.load(f)
        res = make_response(render_template('result.html', 
                            accurancy=listArgs[0],
                            mean=listArgs[1], std=listArgs[2],
                            median=listArgs[3], 
                            predictLength=listArgs[4],
                            alpha=listArgs[5], 
                            beta=listArgs[6],
                            gamma=listArgs[7], 
                            tableName=url_for('table', campaign=campaign),
                            backlink=url_for('forecastServer'),
                            plotName=url_for('plot', campaign=campaign),
                            campaign=campaign,
                            sumShows=listArgs[8]))
        return res
    except EOFError:
        res = make_response(render_template('fake_result.html', 
                        campaign=campaign,
                        backlink=url_for('forecastServer')))
        return res

@app.route('/full_results/<campaign>', methods=['GET'])
def fullLastResult(campaigns):
    try:
        with open(f'./resultsBin/full_{campaigns}.pickle', 'rb') as f:
            dictArgs = pickle.load(f)
        res = make_response(render_template('full_result.html', 
                            accurancy=dictArgs['accurancy'],
                            mean=dictArgs['mean'], std=dictArgs['std'],
                            median=dictArgs['median'], 
                            predictLength=dictArgs['predictLength'],
                            alpha=dictArgs['alpha'], 
                            beta=dictArgs['beta'],
                            gamma=dictArgs['gamma'], 
                            tableName=url_for('table', campaign=campaigns),
                            backlink=url_for('forecastServer'),
                            plotName=url_for('plot', campaign=campaigns),
                            campaign=campaigns,
                            sumShows=dictArgs['sumShows'],
                            sumClicks=dictArgs['sumClicks'],
                            sumPostbacksUnconf=dictArgs['sumPostbacksUnconf'],
                            sumPostbacksConf=dictArgs['sumPostbacksConf']))
        return res
    except EOFError:
        res = make_response(render_template('fake_result.html', 
                        campaign=campaigns,
                        backlink=url_for('forecastServer')))
        return res
        
@app.route('/not_found', methods=['GET'])
def notFound():
    campaign = request.cookies.get('campaign')
    return render_template('false_result.html', 
                            campaign=campaign, 
                            backlink=url_for("forecastServer"))

@app.route("/plot/<campaign>", methods=['GET'])
def plot(campaign):
    plotName = f'{campaign}.html'
    return render_template(f'plot_{plotName}')

@app.route("/table/<campaign>", methods=['GET'])
def table(campaign):
    tableName = f'{campaign}.html'
    return render_template(f'table_{tableName}')


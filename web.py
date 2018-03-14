import sunpy.map
import json
import matplotlib.pyplot as plt
from sunpy.lightcurve import LYRALightCurve
from sunpy.net.helioviewer import HelioviewerClient
from sunpy.net import hek, hek2vso
from sunpy.time import *
import mpld3
from mpld3 import plugins
import HTML
from collections import OrderedDict

from flask import Flask, render_template, request
app = Flask(__name__)
hekc = hek.HEKClient()
h2v = hek2vso.H2VClient()
#event_types = ['AR','CE','CD','CH','CW','CW','FI', 'FE', 'FA', 'FL','LP','OS','SS','EF','CJ','PF','OT','NR','SP','CR','CC','ER','TO','HY']
event_types = ['CE', 'FL', 'SG', 'SS']

def fetch_lightcurve(tstart):
	ly = LYRALightCurve.create(tstart)
	fig = plt.figure()
	ly.plot()
	return mpld3.fig_to_html(fig, template_type='notebook')

def fetch_image(date, obs, ins, det, meas):
	hv = HelioviewerClient()
	filepath = hv.download_jp2(date,observatory=obs, instrument=ins, detector=det, measurement=meas)
	print filepath
	hmi = sunpy.map.Map(filepath)
	hmi.meta['CROTA2'] = 0
	fig = plt.figure()
	hmi.plot()
	plt.colorbar()
	return mpld3.fig_to_html(fig, template_type='notebook')

def fetch_zoomed_image(date, obs, ins, det, meas, x1, x2, y1, y2):
	hv = HelioviewerClient()
	filepath = hv.download_jp2(date,observatory=obs, instrument=ins, detector=det, measurement=meas)
	print filepath
	hmi = sunpy.map.Map(filepath)
	hmi.meta['CROTA2'] = 0
	submap = hmi.submap([x1, x2], [y1, y2])
	fig = plt.figure()
	submap.plot()
	plt.colorbar()
	return mpld3.fig_to_html(fig, template_type='notebook')

def fetch_events(tstart,tend,event_type):
    result = hekc.query(hek.attrs.Time(tstart, tend), hek.attrs.EventType(event_type))
    ele = []
    length = len(result)
    print length
    for i in range(0,length):
	    event = OrderedDict()
	    #event['Type'] = str(result[i]['event_type'])
	    event['Start'] = str(result[i]['event_starttime'])
	    event['End'] = str(result[i]['event_endtime'])
	    event['Probability'] = result[i]['event_probability']
	    event['Importance'] = result[i]['event_importance']
	    if (result[i]['event_type'] == 'CE'):
		    event['Radial lineal velocity'] = str(result[i]['CME_radiallinvel']) + ' ' + str(result[i]['cme_radiallinvelunit'])
		    event['Angular width'] = str(result[i]['cme_angularwidth']) + ' ' + str(result[i]['cme_angularwidthunit'])
	    elif (result[i]['event_type'] == 'FL'):
		    event['Class'] = str(result[i]['fl_goescls'])
		    event['Peak Flux'] = str(result[i]['fl_peakflux']) + ' ' + str(result[i]['fl_peakfluxunit'])
		    event['Peak Temperature'] = str(result[i]['fl_peaktemp']) + ' ' + str(result[i]['fl_peaktempunit'])
	    elif (result[i]['event_type'] == 'SG'):
		    event['Shape'] = str(result[i]['sg_shape'])
		    event['Chirality'] = str(result[i]['sg_chirality'])
		    event['Orientation'] = str(result[i]['sg_orientation'])
	    elif (result[i]['event_type'] == 'SS'):
		    event['Spin Rate'] = str(result[i]['ss_spinrate']) + str(result[i]['ss_spinrateunit'])
	    ele.append(event)
	    print event
    return render_template('figure.html', items=ele, results=result)
#aia = sunpy.map.Map(sunpy.AIA_171_IMAGE)
#aia.plot()

#fightml = mpld3.fig_to_html(fig)
@app.route("/")
def hello():
	hv = HelioviewerClient()
	datasources = hv.get_data_sources()
	entries = []
	for observatory, instruments in datasources.items():
		for inst, detectors in instruments.items():
			for det, measurements in detectors.items():
				for meas, params in measurements.items():
					entry = OrderedDict()				
					entry['name'] = params['nickname']
					entry['obs'] = observatory
					entry['val'] = observatory + "," + inst + "," + det + "," + meas
					entries.append(entry)
	print entries
	return render_template('index.html',evs=event_types, entries=entries)

@app.route("/events", methods=['POST'])
def events():
    data = json.loads(request.data)
    print data
    return fetch_events(data['sdate'], data['edate'], data['etype'])

@app.route("/query", methods=['POST'])
def query():
	data = json.loads(request.data)
	values = data['ent'].split(',');
	print values
	return fetch_image(data['date'], values[0], values[1], values[2], values[3])
#	return fetch_image(data['date'], data['obs'], data['ins'], data['det'], data['meas'])

@app.route("/subquery", methods=['POST'])
def subquery():
	data = json.loads(request.data)
	values = data['ent'].split(',');
	print values
	return fetch_zoomed_image(data['date'], values[0], values[1], values[2], values[3], float(data['x1']), float(data['x2']), float(data['y1']), float(data['y2']))

@app.route("/lightcurve", methods=['POST'])
def spectra():
	data = json.loads(request.data)
	print data
	return fetch_lightcurve(data['sdate'])

@app.route("/vsodata", methods=['GET'])
def vsodata():
	data = json.loads(request.args['val'])
	vso_records = OrderedDict()
	vso_records = hek2vso.translate_results_to_query(data)
	vso_rec = h2v.translate_and_query(data)
	length = len(vso_records)
	return render_template('fig.html', l = length, vso=vso_records, v = vso_rec)

if __name__ == '__main__':
    app.run(debug=True)

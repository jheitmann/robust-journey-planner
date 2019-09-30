
from flask import Flask, request, redirect, url_for, render_template, send_file

import sys
sys.path.append("..")
import datetime
import interface
import mapmaker

app = Flask(__name__)

from itertools import groupby
def route_to_steps(route, fbi):
    """ Transforms the CSA output to data for the webpage """
    steps_grouped = [(k, list(it)) for k, it in groupby(route, lambda s: s["trip_id"])]
    steps = []
    for k, steps_group in steps_grouped:
        walk_or_short = steps_group[0]["type"] == 'Walk' or len(steps_group) == 1
        assert walk_or_short or len(steps_group) == 2 # one trip is [from station 0 to 1, from station n-1 to n] -> len=2
        assert walk_or_short or all(steps_group[0][k] == steps_group[1][k] for k in ("trip_id", "type")) # same trip, same type
        steps.append({
            "trip_ip":steps_group[0]["trip_id"], # maybe not needed
            "type":steps_group[0]["type"],
            "departure_station_name":fbi.index_station[steps_group[0]["departure_station"]],
            "arrival_station_name":fbi.index_station[steps_group[0 if walk_or_short else 1]["arrival_station"]],            
            "departure_ts":steps_group[0]["departure_timestamp"].strftime("%H:%M"), # only hours:minutes like gmaps
            "arrival_ts":steps_group[0 if walk_or_short else 1]["arrival_timestamp"].strftime("%H:%M"), # only hours:minutes like gmaps
            "duration":(steps_group[0 if walk_or_short else 1]["arrival_timestamp"] - steps_group[0]["departure_timestamp"]).seconds // 60
        })
    return steps

def isochrones_from_times(times, t_ranges, fbi):
    """ Transforms mapping station_name->time to mapping timerange->station_names """
    isochrones = {t_range:[] for t_range in t_ranges}
    for station_name, time in times.items():
        for t_range in t_ranges:
            if time in t_range:
                isochrones[t_range].append((station_name, time, fbi.latlon(station_name)))
    return isochrones

SAVED_DATA_ROOT = "saved_data/"

@app.route('/', methods=["GET", "POST"])
def root():
    """ Flask method of the root page with the forms for route planning or isochrone map making """
    fbi = interface.FrontBackInterface(SAVED_DATA_ROOT)
    if request.method == "GET":
        return render_template("dbjp_form.html", all_station_names=list(fbi.station_idx.keys()))
    elif request.method == "POST":
        #print(request.form.get("btn"))
        if request.form.get("btn") == "Compute route":
            #print(f"posted compute route request from          {request.form.get('from')} to {request.form.get('to')} with qvalue {request.form.get('qvalue')}")
            stn_from, stn_to, qvalue, date, time = (request.form.get(k) for k in ("from", "to", "qvalue", "date", "time"))
            return redirect(url_for('result', stn_from=stn_from, stn_to=stn_to, qvalue=qvalue, date=date, time=time))
        elif request.form.get("btn") == "Compute isochrones":
            #print(f"posted compute isochrone request originating at {request.form.get('origin')}")
            stn_origin = request.form.get("origin")
            return redirect(url_for('iso', stn_origin=stn_origin))

@app.route("/result", methods=["GET"])
def result():
    """ Flask method of the route planning results page """
    if request.method == "GET":
        fbi = interface.FrontBackInterface(SAVED_DATA_ROOT)
        #departure_time = datetime.datetime.strptime("02.01.2019 12:00", "%d.%m.%Y %H:%M") placeholder for testing
        departure_time = datetime.datetime.strptime(request.args.get("date") + " " + request.args.get("time"), "%Y-%m-%d %H:%M")
        tolerance = int(request.args.get("qvalue"))*.01

        # Computes route
        route = fbi.journey_plan(request.args.get("stn_from"), request.args.get("stn_to"), departure_time, tolerance)

        # Gets data for webpage from route
        steps = route_to_steps(route, fbi)

        # For map drawing, fetch coordinates and names of points
        coordinates = [fbi.latlon(step["departure_station_name"]) for step in steps]
        coordinates.append(fbi.latlon(steps[-1]["arrival_station_name"]))
        names = [step["departure_station_name"] for step in steps] + [steps[-1]["arrival_station_name"]]
        times = [None,] + [step["departure_ts"] for step in steps]
        walk_bools = [step["type"]=="Walk" for step in steps]
        # Draws route and saves the resulting file localy
        mapmaker.map_steps("steps.html", coordinates, names, times, walk_bools)

        # Returns the HTML file and renders the localy saved file
        return render_template("dbjp_result.html", steps=steps)

@app.route("/iso", methods=["GET"])
def iso():
    """ Flask method of the 4 isochrone maps display page """
    if request.method == "GET":
        TOLERANCES = [0.5, 0.75, 0.9, 1.0]
        departure_time = datetime.datetime.strptime("02.01.2019 12:00", "%d.%m.%Y %H:%M")

        fbi = interface.FrontBackInterface(SAVED_DATA_ROOT)

        # Computes the times to stations from origin
        times_to_stations = [
            fbi.times_to_stations(fbi.station_idx[request.args.get("stn_origin")], departure_time, tolerance)
            for tolerance in TOLERANCES]
        # Computes isochrone ranges + additional "more than" (k+1)*15 = 150 min or more trips
        T_RANGES = [range(k*15, (k+1)*15) for k in range(9)] + [range(150, 241)]
        # Generates the isochrones from the times to stations using helper method
        isochrones_arr = [isochrones_from_times(t2s, T_RANGES, fbi) for t2s in times_to_stations]

        # Draws isochrones in from a reformated array - saves the resulting file localy and renders it
        isochrones_fmted_arr = [[
            [station_data for station_data in isochrone] for t_r, isochrone in isochrones.items()] for isochrones in isochrones_arr]
        for tolerance, isochrones_fmted in zip(TOLERANCES, isochrones_fmted_arr):
            mapmaker.map_isochrones(f"isochrones{str(tolerance)}.html", isochrones_fmted)
        return render_template("dbjp_iso.html")

@app.route("/map")
def map_endpoint():
    # extremely unsafe for now, i know
    #print("resending_file")
    return send_file(request.args.get("fname"), cache_timeout=-1)

def start(**kwargs):
    app.run(host="0.0.0.0", **kwargs)#port=port, debug=debug)
              
if __name__ == '__main__':
    start(debug=True)
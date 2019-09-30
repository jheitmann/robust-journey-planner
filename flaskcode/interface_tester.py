

import sys
sys.path.append("..")
import datetime
import interface


if __name__=="__main__":
    departure_station = "Kloten Balsberg"
    arrival_station = "Zürich Affoltern" 
    departure_time = datetime.datetime.strptime("02.01.2019 12:00", "%d.%m.%Y %H:%M")

    fbi = interface.FrontBackInterface("saved_data")
    res = fbi.journey_plan(departure_station, arrival_station, departure_time, 0.75)
    for step in res:
        #print(fbi.index_station[step['departure_station']])
        print(step['type'], fbi.index_station[step['departure_station']], "===>", fbi.index_station[step['arrival_station']])
    #print(res)
    #for thing in res:
    #    print(thing)

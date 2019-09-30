import os
import pickle
import pandas as pd
from helpers import StochasticCSA
from scipy import sparse


class FrontBackInterface:
    """ This class serves as the interface between the backend implementations of our algorithms and the webserver frontend """

    def __init__(self, mappings_dirpath="saved_data"):
        """ Initializes needed data for the interface """
        # Fetches the index/name station mappings and the timetable
        self.station_idx, self.index_station, self.stochastic_timetable = self.depickle_mappings(mappings_dirpath)

        # Fetches the adjacency matrix
        FNAME_ADJMAT = os.path.join(mappings_dirpath, "adjacency_sparse.npz")
        self.adjacency_sparse = sparse.load_npz(FNAME_ADJMAT)

        # Fetches the list of stations with geo coordinates
        station_meta_path = os.path.join(mappings_dirpath, "bfkoordgeo.csv")
        station_meta_df = pd.read_csv(station_meta_path).head(-1)
        self.station_coord = pd.Series(list(zip(station_meta_df.Longitude,station_meta_df.Latitude)), index=station_meta_df.Remark).to_dict()

        self.n_stations = self.adjacency_sparse.shape[0]
    
    def depickle_mappings(self, mappings_dirpath="saved_data"):
        FNAME_S2I = os.path.join(mappings_dirpath, "station_index.pkl")
        FNAME_I2S = os.path.join(mappings_dirpath, "index_station.pkl")        
        FNAME_STOCHTT = os.path.join(mappings_dirpath, "stochastic_timetable.pkl")
        # Depickles serialized items needed for our interface
        with open(FNAME_S2I, "rb") as s2i, open(FNAME_I2S, "rb") as i2s, open(FNAME_STOCHTT, "rb") as serialized_table:
            return pickle.load(s2i), pickle.load(i2s), pickle.load(serialized_table)

    def journey_plan(self, departure_station, arrival_station, departure_time, tolerance, *, trip_window=4):
        """ Plans one journey from departure_station to arrival_station (names) and returnsw a route structure with the steps """
        departure_idx = self.station_idx[departure_station]
        arrival_idx = self.station_idx[arrival_station]
        csa = StochasticCSA(self.stochastic_timetable,self.adjacency_sparse)
        csa.compute(departure_idx,departure_time,tolerance,trip_window,arrival_station=arrival_idx)
        route = csa.get_route(departure_idx, arrival_idx, departure_time)
        return route

    def times_to_stations(self, departure_idx, departure_time, tolerance, *, trip_window=4):
        """ Computes the times from the origin to all other stations. Impossible routes will convert to trip_window*60 min """
        trip_length = {}
        trip_length[self.index_station[departure_idx]] = 0.
        csa = StochasticCSA(self.stochastic_timetable,self.adjacency_sparse)
        csa.compute(departure_idx, departure_time, tolerance, trip_window)
        for arrival_idx in range(self.n_stations):
            if arrival_idx != departure_idx:
                route = csa.get_route(departure_idx, arrival_idx, departure_time)
                if route:
                    last_c = route[-1]
                    arrival_timestamp = last_c["arrival_timestamp"]
                    difference = (arrival_timestamp-departure_time).seconds // 60
                    trip_length[self.index_station[arrival_idx]] = difference
                else:
                    trip_length[self.index_station[arrival_idx]] = trip_window * 60
                 
        return trip_length

    def times_to_stations_from_hbf(self, departure_time, tolerance, *, trip_window=4):
        """ Legacy function from the previous versions where isochrones were computed from Hauptbahnhof only """
        zurich_idx = self.station_idx["Zürich HB"]
        return self.times_to_stations(zurich_idx,departure_time,tolerance,trip_window=trip_window)

    def latlon(self, station_identifier):
        """ Returns (lon, lat) of station (accepts id:int or name:str) """
        lon, lat = self.station_coord[station_identifier]
        return lat, lon

    def get_stations_metadata(self):
        """ Returns a df of stations metadata """
        station_meta_path = 'metadata/bfkoordgeo.csv'
        station_meta_df = pd.read_csv(station_meta_path).head(-1)
        return station_meta_df

if __name__=="__main__":
    # testing calls
    fbi = FrontBackInterface()
    print(fbi.depickle_mappings())
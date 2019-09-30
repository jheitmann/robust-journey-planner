from datetime import timedelta

class StochasticCSA:
    """
    An abstraction of the Connection Scan Algorithm
    """
    
    class StochasticTable:
        """
        A data structure to store the entries at a given station, 
        correponding to different paths, with increasing arrival 
        time and route probability.
        """
    
        CONNECTION_IDX = 0 # idx in the stochastic timetable
        ARRIVAL_TS = 1 # Arrival timestamp at station X
        IN_ROUTE = 2 # idx in the preceding StochasticTable
        ROUTE_PROB = 3 # Arrival probability of the route that ends at X

        def __init__(self, max_ts): 
            self.entries = [(-1,max_ts,-1,0)]
            
        def get_indices(self, i):
            e = self.entries[i]
            return e[self.CONNECTION_IDX], e[self.IN_ROUTE]
        
        def get_probability(self, i):
            e = self.entries[i]
            return e[self.ROUTE_PROB]
            
        def earliest_arrival(self):
            return self.entries[0][self.ARRIVAL_TS]

        def update_table(self, connection_idx, arrival_ts, in_route, route_prob):
            """
            Adds an entry to the table, meaning a new connection that was appended to 
            a certain route, with an updated route probability. Both arrival timestamps
            and route probabilites are (must be) stored in increasing order.
            """
            new_entry = (connection_idx, arrival_ts, in_route, route_prob)
            if arrival_ts > self.entries[-1][self.ARRIVAL_TS]:
                if route_prob > self.entries [-1][self.ROUTE_PROB]:
                    self.entries.append(new_entry)
            else:
                i = 0
                prev_prob = 0
                while arrival_ts > self.entries[i][self.ARRIVAL_TS]:
                    prev_prob = self.entries[i][self.ROUTE_PROB]
                    i += 1
                if route_prob > prev_prob:
                    next_ts = self.entries[i][self.ARRIVAL_TS]
                    next_prob = self.entries[i][self.ROUTE_PROB]
                    if route_prob >= next_prob: 
                        j = i
                        while j < len(self.entries) and route_prob >= self.entries[j][self.ROUTE_PROB]:
                            j += 1
                        self.entries = self.entries[:i] + [new_entry] + self.entries[j:]
                    elif arrival_ts != next_ts:
                        self.entries = self.entries[:i] + [new_entry] + self.entries[i:]

        def best_connecting(self, stochastic_timetable, departure_timestamp):
            """
            Given a new connection departing at 'departure_timestamp', finds the best 
            route that arrives at station X. Makes use of the CDF of the incoming 
            connection at X (last connection of the route), to compute the updated 
            route probability.  
            """
            max_e_idx = -1
            max_prb = 0
            for e_idx, e in enumerate(self.entries):
                arrival_timestamp = e[self.ARRIVAL_TS]
                if arrival_timestamp <= departure_timestamp:
                    c_idx = e[self.CONNECTION_IDX]
                    route_prb = e[self.ROUTE_PROB]
                    difference = (departure_timestamp-arrival_timestamp).seconds // 60
                    prev_cdf = stochastic_timetable[c_idx]["cdf"]
                    extended_route_prb = route_prb * (1 if difference >= 10 else prev_cdf[difference])
                    if extended_route_prb > max_prb:
                        max_e_idx = e_idx
                        max_prb = extended_route_prb
            return max_e_idx, max_prb    
            
    
    def __init__(self, stochastic_timetable, walking_times):
        self.stochastic_timetable = stochastic_timetable
        self.walking_times = walking_times
        self.n_stations = walking_times.get_shape()[0]
        
    def check_neighborhood(self, arrival_station, arrival_timestamp):
        """
        Checks the neighborhood of a certain station (reachable stations), and updates 
        the StochasticTables accordingly.
        """
        rows, cols = self.walking_times.nonzero() 
        neighborhood = (rows == arrival_station)
        outs = []
        for station in cols[neighborhood]:
            walking_time = self.walking_times[arrival_station,station]
            walk_timestamp = arrival_timestamp + timedelta(minutes=walking_time)
            yield station, walk_timestamp
                
    def main_loop(self, arrival_station):
        """
        Main component of the CSA
        """
        earliest = self.max_ts
        
        for i, c in enumerate(self.stochastic_timetable):
            
            c_trip_id = c["trip_id"]
            c_departure_station = c["departure_station"]
            c_arrival_station = c["arrival_station"]
            c_departure_ts = c["departure_timestamp"]
            c_arrival_ts = c["arrival_timestamp"]
            
            if c_departure_ts > earliest:
                return
            elif c_departure_ts >= self.stochastic_tables[c_departure_station].earliest_arrival() \
                or c_trip_id in self.stochastic_trips:
                
                e_idx, route_prb  = self.stochastic_tables[c_departure_station].best_connecting(self.stochastic_timetable, c_departure_ts)
                c_idx = i
                
                if c_trip_id in self.stochastic_trips:
                    _, _, trip_prb = self.stochastic_trips[c_trip_id][-1]
                    if trip_prb < route_prb: 
                        # update trip initial connection
                        self.stochastic_trips[c_trip_id].append((c_idx,e_idx,route_prb))
                    else: # jump to initial connection
                        e_idx = -len(self.stochastic_trips[c_trip_id])
                        route_prb = trip_prb
                else:
                    self.stochastic_trips[c_trip_id] = [(c_idx,e_idx,route_prb)]
                   
                if route_prb >= self.tolerance:
                    for station, walk_timestamp in self.check_neighborhood(c_arrival_station, c_arrival_ts):
                        self.stochastic_tables[station].update_table(c_idx,walk_timestamp,e_idx,route_prb)
                        if station == arrival_station:
                            earliest = self.stochastic_tables[station].earliest_arrival()
        
    def generate_walk(self, departure_station, arrival_station, departure_timestamp):
        """
        Create a connection that represents a walk
        """
        walk_connection = {'trip_id': '', 'type': 'Walk'}
        walk_connection['departure_station'] = departure_station
        walk_connection['arrival_station'] = arrival_station
        walk_connection['departure_timestamp'] = departure_timestamp
        walking_time = self.walking_times[departure_station,arrival_station]
        arrival_timestamp = departure_timestamp + timedelta(minutes=walking_time)
        walk_connection['arrival_timestamp'] = arrival_timestamp
        
        return walk_connection
        
    def get_route(self, departure_station, arrival_station, departure_time):
        """
        Reconstruct the route from 'departure_station' to 'arrival_station', starting 
        at 'departure_time'
        """
        route = []
        
        if self.stochastic_tables[arrival_station].earliest_arrival() == self.max_ts:
            print("NO SOLUTION")
        else:
            c_idx, e_idx = self.stochastic_tables[arrival_station].get_indices(0)
            route_prb = self.stochastic_tables[arrival_station].get_probability(0)
            next_station = arrival_station
            next_trip = ""
            print("Route probability:",route_prb)
            
            c_departure_station = None
            while c_idx != -1:
                connection = self.stochastic_timetable[c_idx]
                
                c_departure_station = connection["departure_station"]
                c_arrival_station = connection["arrival_station"]
                c_trip_id = connection["trip_id"]
                
                if c_trip_id != next_trip and c_arrival_station != next_station:
                    c_arrival_timestamp = connection["arrival_timestamp"]
                    route.append(self.generate_walk(c_arrival_station,next_station,c_arrival_timestamp))
                
                route.append(connection)
                next_station = c_departure_station
                next_trip = c_trip_id
                
                if e_idx < 0:
                    trip_initial = -e_idx - 1
                    c_idx, e_idx, _ = self.stochastic_trips[c_trip_id][trip_initial]
                else:
                    c_idx, e_idx = self.stochastic_tables[c_departure_station].get_indices(e_idx)            
                        
            if c_departure_station != next_station:
                route.append(self.generate_walk(departure_station,next_station,departure_time))
        
        return route[::-1]             
        
    def compute(self, departure_station, departure_time, tolerance, max_delta, *, arrival_station=None):
        """
        Run the CSA from 'departure_station', at 'departure_time'
        """
        self.max_ts = departure_time + timedelta(hours=max_delta)
        self.tolerance = tolerance
        self.stochastic_tables = [StochasticCSA.StochasticTable(self.max_ts) for _ in range(self.n_stations)]
        
        for station, walk_timestamp in self.check_neighborhood(departure_station, departure_time):
            self.stochastic_tables[station].update_table(-1,walk_timestamp,-1,1)
            
        self.stochastic_trips = {}
        
        self.main_loop(arrival_station)
        
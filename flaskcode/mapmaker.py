import folium

def map_route(fpath, route):
    """ Tests local serialization """
    m = folium.Map(location=[47.3769, 8.5417])
    m.save(fpath)
    print("saved route map to", fpath)
    return m

# Legacy shades gradient for our isochrones (it looks ugly)
COLORS = ['black', 'darkred', 'red', 'orange', 'yellow', 'green', 'lightblue', 'blue', "purple", "pink"]
# Green shades gradient for our isochrones (imposes max 10 granularity due to fixed size)
TERRAIN2 = ["#ffffe5", "#f7fcb9", "#d9f0a3", "#addd8e", "#78c679", "#41ab5d", "#238443", "#006837", "#004529", "#000000"]

def map_isochrones(fpath, isochrones, colors=TERRAIN2):
    # Centers the map on Hauptbahnhof
    HBF_LOC = (47.3784, 8.5384)
    m = folium.Map(location=HBF_LOC, zoom_start=11)

    # Draws a point on each station of the green shade of the coresp. isochrone, or red if unreachable
    for i, isochrone in enumerate(isochrones):        
        for station in isochrone:
            displayed_len = str(station[1]) + " min" if station[1] < 240 else "impossible"
            m.add_child(
                folium.CircleMarker(
                    location=station[2], fill='true', radius=6, popup=f"{station[0]}: {displayed_len}", fill_color=colors[i] if station[1] < 240 else "red", color='clear', fill_opacity=1))

    # Serializes the file localy
    m.save(fpath)


def map_steps(fpath, coordinates, names, times, walk_bools):        
    # Load map centred on average coordinates
    avg = [sum(p[i] for p in coordinates)/len(coordinates) for i in (0, 1)]
    m = folium.Map(location=avg, zoom_start=12)

    # Draws a line between each pair of stations on the route
    for (p0, p1), is_walk in zip(zip(coordinates[:-1], coordinates[1:]), walk_bools):
        # Sets additional parameters to make a dashed line for walking segments
        sup_kwargs = dict(dash_array='6, 6', dash_offset='3') if is_walk else {}
        folium.PolyLine([p0, p1], color="red", weight=4, opacity=1, **sup_kwargs).add_to(m)

    # Draws the station nodes on top of the lines
    for coord, name, ts in zip(coordinates, names, times):
        m.add_child(
            folium.CircleMarker(
                location=coord, fill='true', radius=4, popup=name + (", arr. " + str(ts) if coord != coordinates[0] else ""), fill_color='white', color='black', fill_opacity=1))

    # Serializes the file localy
    m.save(fpath)

if __name__=="__main__":
    map_route("test_direct.html", None)
    

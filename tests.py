from mapper import *

def test_solver(trip):
    # Setup a smaller pathway array
    # Set solver to use an input pathway array
    new = RouteOptimizer(trip.trail_network, maxdist=30)
    #new.set_trip_length(0,30)
    new.setup_lp()
    new.set_grouping_constraint(1)
    new.solve()
    new.get_results()
    return new

def test_trips():
    trip = TripPlanner("Boulder, Colorado")
    trip.create_network()
    return trip
    
def test_save_GPX(opt):
    new.save_gpx(Path, "saved_trips/30km.gpx")
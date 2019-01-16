from ortools.linear_solver import pywraplp
import networkx as nx
from shapely.geometry import Point, LineString, MultiLineString
import gpxpy
import os

class RouteOptimizer():
    def __init__(self, trail_network, mindist = 0, maxdist = 100):
        """
        This is a mixed-integer linear program.  It will maximize distance
        such that each node is gone through symetrically from either side
        """
        # Make Path object a more callable object -- Fix all this
        self.trail_network   = trail_network
        self.mindist         = mindist
        self.maxdist         = maxdist
        self.variables       = {}
        self.path_groups     = {}
        self.group_vars      = {}
        self.group_list      = []
        self.starting_trails = {}
        self.constraints     = {}
        self.solver          = None
        self.objective       = None
        self.results         = None
        self.node_variables  = {}
        self.edge_limit      = {}
        
    def set_trip_length(self, mindist, maxdist):
        self.mindist = mindist
        self.maxdist = maxdist
        self.set_distance_constraint()
        
    def setup_solver(self):
        self.solver    = pywraplp.Solver('Backpack Trip Planner',
                            pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
                            
        self.objective = self.solver.Objective()
        self.objective.SetMaximization()
        
    def setup_variables(self):
        """
        Each path is setup as an integer variable.  It can either be 0 or 1.
        Paths can go from Origin_to_Destination, or Destnation_to_Origin
        """
        
        self.set_distance_constraint()

        start = self.constraints["start_node"] = self.solver.Constraint(0, 1)   
        for path in self.trail_network.edges(data=True):
            pathwaycons  = self.constraints[path[2]["name"]] = self.solver.Constraint(0, 1)
            pathd        = path[2]["length"]
            constraint   = self.constraints["Trip Distance"]
            forward      = (path[0],path[1], path[2]["name"])
            reverse      = (path[1],path[0], path[2]["name"])
            
            # Add the node variables
            if path[0] not in self.node_variables:
                node1 = self.node_variables[path[0]] = self.solver.IntVar(0,1,"node_var"+str(path[0]))
                start.SetCoefficient(node1, 1)
            
            if path[1] not in self.node_variables:
                node2 = self.node_variables[path[1]] = self.solver.IntVar(0,1,"node_var"+str(path[1]))
                start.SetCoefficient(node2, 1)
            
            
                
            #Had previously set values at 2, not sure why?
            self.variables[forward] = self.solver.IntVar(0, 1, "forward_"+str(forward))
            self.variables[reverse] = self.solver.IntVar(0, 1, "reverse_"+str(reverse))
            
            # Add constraints so a pathway can go either forward or backward
            pathwaycons.SetCoefficient(self.variables[forward], 1)
            pathwaycons.SetCoefficient(self.variables[reverse], 1)

            # Add distances to the total distance constraint
            constraint.SetCoefficient(self.variables[forward], pathd)
            constraint.SetCoefficient(self.variables[reverse], pathd)
            
            # Add distances to objective function
            self.objective.SetCoefficient(self.variables[forward], pathd)
            self.objective.SetCoefficient(self.variables[reverse], pathd)
            
    def set_node_constraints(self):
        """
        Each Pathway represents leaving a node or joining a node.
        All nodes must stay at 0, otherwise it is impossible to return to
        your origin
        """
        
    
        # Have each node be a variable (Start Node) <-- Done: X
        # Constraint:  Only have 1 start-node
        # Node Coefficient: 1 for Node Variable
        #Pathway Constraints Below can be 0 or 1
            # Start constraint prevents a -1
            # Pathway in single direction prevents doubling back
        
        if not self.variables:
            raise Exception("Pathway variables need to be setup first")

        for pathway in self.variables:
            intvar = self.variables[pathway]

            
            if pathway[0] not in self.constraints:
                self.constraints[pathway[0]] = self.solver.Constraint(0, 1)
                edge1 = self.edge_limit[pathway[0]] = self.solver.Constraint(0,2)
                
            
            if pathway[1] not in self.constraints:
                self.constraints[pathway[1]] = self.solver.Constraint(0, 1)
                edge2 = self.edge_limit[pathway[1]] = self.solver.Constraint(0,2)
                
            node1 = self.constraints[pathway[0]]
            node2 = self.constraints[pathway[1]]
            edge1 = self.edge_limit[pathway[0]]
            edge2 = self.edge_limit[pathway[1]]
        
            
            node1.SetCoefficient(intvar, 1)
            node2.SetCoefficient(intvar, -1)
            edge1.SetCoefficient(intvar, 1)
            edge2.SetCoefficient(intvar, 1)
            
            # Allow start_condition to add a +1
            node1.SetCoefficient(self.node_variables[pathway[0]],1)
            node2.SetCoefficient(self.node_variables[pathway[1]],1)
        
    def set_distance_constraint(self):
        if "Distance" not in self.constraints:
            self.constraints["Trip Distance"] = self.solver.Constraint(self.mindist, self.maxdist)
        else:
            self.constraints["Trip Distance"].SetBounds(self.mindist, self.maxdist)
    
    def establish_groups(self):
        d = list(nx.connected_component_subgraphs(self.trail_network))
        for i, group in enumerate(d):
            for node in group:
                self.path_groups[node] = i
            self.group_list.append(i)
        
        
    def set_grouping_constraint(self, unique_starts = 1):
        """
        A Constraint that allows only a number of networks equal to [unique_starts] chosen
        in a given area
        """
        if not self.path_groups:
            self.establish_groups()
            
        grp_constraint = self.constraints["Trail Groups"] = self.solver.Constraint(0, unique_starts)
        for group in self.group_list:
            grp_id = self.group_vars[group] = self.solver.IntVar(0,1,str(group))
            grp_constraint.SetCoefficient(grp_id, 1)
            
        for path_key in self.variables:
            """
            Allows a path to be selected if it falls in the same group as the
            chosen hiking group
            """
            grp_id     = self.path_groups[path_key[0]]
            identifier = "constraint_%s" % str(grp_id)
            
            cons       = self.group_vars[identifier] = self.solver.Constraint(0,self.solver.infinity())
            path_var   = self.variables[path_key]
            grp_var    = self.group_vars[grp_id]
            
            cons.SetCoefficient(path_var,-1)
            cons.SetCoefficient(grp_var, 1)
            
        
    def setup_lp(self):
        self.setup_solver()
        self.setup_variables()
        self.set_node_constraints()
        
    def solve(self):
        result_status = self.solver.Solve()
        return result_status
    
    def get_results(self):
        results = []
        print("Total Trip Length: %s km" % self.objective.Value())
        for key in self.variables:
            intvar = self.variables[key]
            if intvar.solution_value() > 0:
                results.append(key)
                
        self.results = results
        return results
        
    def save_gpx(self, path_object, filename="saved_trips/temp.gpx"):
        """
        Paths is the values from .get_results() function
        for the solved LP problem
        """
        
        # Need some way to order the results together
        if not self.results:
            self.get_results()
        
        results = self.results
        
        self.make_new_gpx(filename)
        gpx_file = open(filename, 'r')
        gpx = gpxpy.parse(gpx_file)
        gpx       = gpxpy.gpx.GPX()
        
        gpx_segment = {}
        for path_name in results:
            gpx_track = gpxpy.gpx.GPXTrack()
            gpx.tracks.append(gpx_track)
            gpx_segment[path_name] = gpxpy.gpx.GPXTrackSegment()
            gpx_track.segments.append(gpx_segment[path_name])
            
            path = path_object.get(path_name).points
            if path.type == 'LineString':
                points = path.coords
            
            else:
                points = path[0].coords
    
            for coord in points:
                gpx_segment[path_name].points.append(gpxpy.gpx.GPXTrackPoint(coord[1], coord[0]))
        
        f = open(filename, 'w+')
        f.write(gpx.to_xml())
        f.close()
        
    
    def make_new_gpx(self, filename = "saved_trips/output.gpx"):
        import xml.etree.cElementTree as ET
        if not os.path.exists(os.path.dirname(filename)):
            try:
                os.makedirs(os.path.dirname(filename))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
        gpx = ET.Element("gpx")
        metadata = ET.SubElement(gpx, "metadata")
        link = ET.SubElement(metadata, "link", href="http://placeholder")
        ET.SubElement(link,"text").text="Backpacking XML Generator"
        
        tree = ET.ElementTree(gpx)
        tree.write(filename)
    


        
        
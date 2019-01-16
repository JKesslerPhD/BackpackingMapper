import requests
from lxml import html
import os
import configparser

config = configparser.ConfigParser()
config.sections()
config.read('config.ini')
global email
global password
global API_key

email     = config['HikingProject.com']['email']
password  = config['HikingProject.com']['password']
API_key   = config['HikingProject.com']['API_key']



class HikingProject():
    def __init__(self, lat=40.0274, lon=-105.2519, maxdistance=50):
        self.session_requests = None
        self.trails = None
        
        self.get_trail_list(key = API_key, lat=lat, lon=lon, maxdistance=maxdistance)
        self.login(email, password)

    @classmethod
    def get_gps_from_location(cls, location):
        pass
        """
        Use google API or something else to get latitude and longitude from
        a place name
        """    
        
    def get_trail_list(self, key, lat, lon, maxdistance):
        payload = { "key":key, 
                    "lat":lat, 
                    "lon":lon,
                    "maxResults":500, 
                    "maxDistance":maxdistance}
        r = requests.get('https://www.hikingproject.com/data/get-trails', params = payload)
        self.trails = r.json()["trails"]

    @classmethod    
    def get_downloaded(cls,directory=os.getcwd()):
        file_list = []
        for content in os.listdir(directory):
            if content.endswith(".gpx"):
                file_list.append(content.split(".gpx")[0])
                
        return file_list
                
        
    def download_trails(self, directory = os.getcwd()):
        downloaded = HikingProject.get_downloaded(directory)
        for trail in self.trails:
            gpx_id = trail["id"]
            
            if str(gpx_id) not in downloaded:
                url      = "https://www.hikingproject.com/trail/gpx/%s" % str(gpx_id)
                print("downloading:%s" % url)
                gpxfile  = directory+"/"+str(gpx_id) + ".gpx"
                try:
                    data     = self.session_requests.get(url, headers = dict(referer = url), allow_redirects = True)
                except:
                    raise Exception("Could not download gpx for %i" % gpx_id)
                     
                with open(gpxfile, 'w+') as f:
                    f.write(data.text)
                            
    def login(self, email, password):
        self.session_requests = requests.session()
        
        login_url = "https://www.hikingproject.com/auth/login"
        email_url = "https://www.hikingproject.com/auth/login/email"
        result = self.session_requests.get(login_url)
        
        tree = html.fromstring(result.text)
        authenticity_token = list(set(tree.xpath("//input[@name='_token']/@value")))[0]
        
        payload = {"email":email, "pass":password, "_token":authenticity_token}
        
        result = self.session_requests.post(
            email_url,
            data = payload,
            headers = dict(referer=login_url))
            
        if result.status_code != 200:
            raise Exception("Unable to Login to HikingProject. Please check login credentials")
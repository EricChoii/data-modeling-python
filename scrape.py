# project: p3
# submitter: hchoi256
# partner: none
# hours: 10

from collections import deque
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import pandas as pd
import requests
import time

class GraphScraper:
    def __init__(self):
        self.visited = set()
        self.order = []

    def go(self, node):
        raise Exception("must be overridden in sub classes -- don't change me here!")

    def dfs_search(self, node):        
        self.visited.clear()
        self.order.clear()
        # start recursive search by calling dfs_visit        
        self.dfs_visit(node)

    def dfs_visit(self, node):
        if node in self.visited:
            return
        self.visited.add(node)
        self.order.append(node)
        for c in self.go(node):
            self.dfs_visit(c)
            
    def bfs_search(self, node):  
        self.visited.clear()
        self.order.clear()
        queue = deque([])
        queue.append(node) # current node            
        # start recursive search
        while queue:
            node = queue.popleft()            
            if node not in self.visited:                
                self.visited.add(node)
                self.order.append(node)
                queue.extend(self.go(node))
                
class MatrixSearcher(GraphScraper):
    def __init__(self, df):
        super().__init__() # call constructor method of parent class
        self.df = df

    def go(self, node):
        children = []
        for c, has_edge in self.df.loc[node].items():
            if has_edge:
                children.append(c)
        return children    


class FileSearcher(GraphScraper):
    def __init__(self):
        super().__init__() # call constructor method of parent class    
        self.msg = []
    
    def go(self, file):       
        children = []
        f = open("file_nodes/"+file, 'r') # assume only two lines in file        
        self.msg.append(f.readline().strip())        
        children.extend(f.readline().strip().split(','))
        f.close()            
        return children
    
    def message(self):
        return ''.join(self.msg)

class WebSearcher(GraphScraper):
    def __init__(self, ws):
        super().__init__() # call constructor method of parent class    
        self.ws = ws # receive WebSearcher object
        self.tb = pd.DataFrame()
    
    def go(self, node):   
        urls = []        
        self.ws.get(node)  
        try:          
            hyperlinks = self.ws.find_elements(By.TAG_NAME, 'a')        
            for hl in hyperlinks:
                urls.append(hl.get_attribute("href"))  
            # read table from url     
            tb = pd.read_html(node, attrs = {'id': 'locations-table'}, encoding='utf-8')[0]                     
            self.tb = pd.concat([self.tb, tb], ignore_index=True)        
        except NoSuchElementException:
            print("couldn't find it")
            
        return urls 
    
    def table(self):
        return self.tb

def reveal_secrets(driver, url, travellog):
    location = ''
    # save password
    password = [str(item) for item in travellog["clue"].tolist()] # Convert each integer to a string
    password = ''.join(password)    
    # visit url wit1h the driver
    driver.get(url)        
    try:
        # automate typing password and clicking "GO"
        pw = driver.find_element_by_id("password")
        pw.send_keys(password)            
        driver.find_element_by_id("attempt-button").click()
        time.sleep(1)
        # click View Location
        driver.find_element_by_id("securityBtn").click()
        time.sleep(1)
        # save location
        location = driver.find_element_by_id("location").text
        time.sleep(1)
        # save image
        img_url = driver.find_element_by_id("image").get_attribute("src")  
        # cite below from https://www.kite.com/python/answers/how-to-download-an-image-using-requests-in-python      
        response = requests.get(img_url)
        file = open("Current_Location.jpg", "wb")
        file.write(response.content)
        file.close()
    except NoSuchElementException:
        print("couldn't find it")        

    return location
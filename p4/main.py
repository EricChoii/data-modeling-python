###############################################################################
# Data Source ('main.csv')
# title: Locations of Fire Stations in Madison City
# format: 15 (rows) x 13 (columns)
# changes: 
#    1. added a new column 'EMS_STATUS' which contains either 0 for no EMS and 1 for EMS.
#    2. for column 'FIRE_STATION_STATUS, changed 'A' to 1 and 'P' to 0
#    3. for column 'EMS', changed 'Y' to 1 and 'N' to 0
# url: https://data-cityofmadison.opendata.arcgis.com/datasets/cityofmadison::fire-stations/explore?showTable=true
###############################################################################

import pandas as pd
import re
import time
import matplotlib.pyplot as plt
from io import StringIO
from flask import Flask, request, jsonify, Response
#matplotlib.use('Agg')

app = Flask(__name__)
df = pd.read_csv("main.csv")
user_ip = dict()
visited = vA = vB = 0
is_curr_ver_A = False
LIMIT = 60

def count_donate():
    global vA, vB
    version = request.args.get('from')
    if version == "A":
        vA = vA + 1
    else:
        vB = vB + 1

def count_visited():    
    global visited, vA, vB, is_curr_ver_A
    if visited < 10:        
        if visited % 2 == 0:
            is_curr_ver_A = True
        else:
            is_curr_ver_A = False
        visited = visited + 1
    else:
        # Pick Best Version
        if vA >= vB:
            is_curr_ver_A = True
        else:
            is_curr_ver_A = False

@app.route('/')
def home():
    # Visit Management
    count_visited()    
    
    # template HTML
    with open("index.html") as f:
        html = f.read()
    
    # dynamically add donations hyperlinks
    if is_curr_ver_A == True:
        html = html.replace("$donations", """<a href = "donate.html?from=A" style="color:blue"> donate A </a>""")       
    else:
        html = html.replace("$donations", """<a href = "donate.html?from=B" style="color:red"> donate B </a>""")
    
    return html

@app.route("/location.svg")
def location():
    fig, ax = plt.subplots()
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    
    # check if query string passed in
    if "cmap" not in request.args:
        ax.set_title("Scatter plot of Fire Station Loations")
        ax = df.plot.scatter(x='X',y='Y', s=30, ax=ax)    
    else:
        c = request.args["cmap"]
        ax.set_title("Scatter plot of Fire Station Loations: Status (Active/Proposed)")      
        ax = df.plot.scatter(x='X',y='Y', c=df.columns.get_loc(c), colormap='viridis', s=30, ax=ax) 
        df[['X','Y','COMMENT']].apply(lambda x: ax.text(*x),axis=1)
        
    # "save" to a string in the SVG format
    f = StringIO()
    ax.get_figure().savefig(f, format="svg", bbox_inches="tight")    
    
    # close the plot to avoid memory leak
    plt.close(fig)
    
    return Response(f.getvalue(),
                    headers={"Content-Type": "image/svg+xml"})

@app.route("/ems.svg")
def location_ems():
    fig, ax = plt.subplots()
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
      
    ax.set_title("Scatter plot of Fire Station Loations: EMS (Y/N)")      
    ax = df.plot.scatter(x='X',y='Y', c=df.columns.get_loc('EMS_STATUS'), colormap='viridis', s=30, ax=ax) 
    df[['X','Y','EMS']].apply(lambda x: ax.text(*x),axis=1)
        
    # "save" to a string in the SVG format
    f = StringIO()
    ax.get_figure().savefig(f, format="svg", bbox_inches="tight")    
    
    # close the plot to avoid memory leak
    plt.close(fig)
    
    return Response(f.getvalue(),
                    headers={"Content-Type": "image/svg+xml"})
                             
@app.route('/browse.json')
def browse_json():
    global user_ip
    ip = request.remote_addr
    if ip in user_ip:    
        if time.time() - user_ip[ip] <= LIMIT:                    
            html = "too many requests, come back later"
            return Response(html, status=429, headers={"Retry-After": LIMIT})     
    user_ip[ip] = time.time()    
    return df.to_dict('index')
        
@app.route('/browse.html')
def browse():  
    html = """<h1>Browse</h1>""" + df.to_html()
    return html
            
@app.route('/donate.html') 
def donate():
    # a/b Version Management
    count_donate()
    return """<html><body style="background-color:lightblue">
               <h1>Donations</h1>      
               Your donation will greatly contribute to our ability to support the essential programs that we provide for the sustainability of our city.<br>
               <button onclick="location.href='/'"> back </button>
               </body></html>"""

@app.route('/email', methods=["POST"])
def email():    
    email = str(request.data, "utf-8")
    if re.match(r"^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$", email): # 1        
        with open("emails.txt", "a+") as f: # open file in append mode            
            f.write(email + "\n") # 2
        num_subscribed = 0
        with open("emails.txt", "r") as f:
            num_subscribed = f.read().count("@")          
        return jsonify(f"thanks, you're subscriber number {num_subscribed}!")
    return jsonify("invalid email address!") # 3

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, threaded=False) # don't change this line!

# NOTE: app.run never returns (it runs for ever, unless you kill the process)
# Thus, don't define any functions after the app.run call, because it will
# never get that far.
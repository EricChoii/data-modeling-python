import re
import pandas as pd
import netaddr
from bisect import bisect

ips = pd.read_csv("ip2location.csv")

def lookup_region(ipaddr):
    ipaddr = re.sub("[^\d\.]", "0", ipaddr)
    ipaddr = int(netaddr.IPAddress(ipaddr))
    idx = bisect(ips.low, ipaddr)
    code = ips.iloc[idx-1][3]
    
    return code

class Filing:
    def __init__(self, html):
        self.dates = []
        dates = re.findall(r"\d{4}-\d{2}-\d{2}", html)
        for date in dates:
            if date[:2] == '20' or date[:2] == '19':
                self.dates.append(date)
        
        if re.search(r"SIC=(\d+)", html):
            self.sic = int(re.findall(r"SIC=(\d+)", html)[0])
        else:
            self.sic = None
        
        self.addresses = []
        for addr_html in re.findall(r'<div class="mailer">([\s\S]+?)</div>', html):
            lines = []
            addr = ''
            for line in re.findall(r'<span class="mailerAddress">([\s\S]+?)</span>', addr_html):     
                if len(line) != 0:
                    lines.append(line.strip())
            for ele in lines: 
                    addr += ele
                    addr += '\n'            
            if addr:
                self.addresses.append(addr.strip())  

    def state(self):
        regex = r"\s*([A-Z]{2})\s+\d{5}"
        for addr in self.addresses:
            if re.search(regex, addr):
                
                return re.findall(regex, addr)[0]
            else:
                pass
        return None
            
       
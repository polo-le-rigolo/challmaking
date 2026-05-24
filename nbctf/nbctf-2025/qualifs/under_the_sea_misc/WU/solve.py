import xml.etree.ElementTree as ET
from statistics import mean

tree = ET.parse("divelog.xml")
root = tree.getroot()

min_ndl = float('inf')
depth_at_min_ndl = None
temps = []

for sample in root.iter('sample'):
    ndl = sample.get('ndl')
    temp = sample.get('temp')
    depth = sample.get('depth')

    if temp:
        try:
            temps.append(float(temp.split()[0]))  
        except ValueError:
            pass

    if ndl and depth:
        try:
            mm, rest = ndl.split(':')
            ss = rest.split()[0]
            ndl_minutes = int(mm) + int(ss) / 60  
            if ndl_minutes < min_ndl:
                min_ndl = ndl_minutes
                depth_at_min_ndl = float(depth.split()[0]) 
        except Exception:
            pass

avg_temp = mean(temps) if temps else None

if depth_at_min_ndl and avg_temp:
    print(f"NBCTF{{{depth_at_min_ndl:.2f}_{avg_temp:.2f}}}")
else:
    print("ton xml est pété chef")


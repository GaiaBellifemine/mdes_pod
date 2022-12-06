#!/usr/bin/env python

import csv
import os.path

def writeOnFile(node_name, cpu_cores, memory, cnt, task, par, start_time):
    header = ['NAME NODE', 'CPU (cores)', 'MEMORY (bytes)', 'ACTIVE PODS', 'TASK', 'PARAMETER', 'EXECUTION START TIME (seconds)']
    file_exists = os.path.isfile('/home/ec2-user/script/DRL/TaskCarousel/metrics.csv')
    f = open('/home/ec2-user/script/DRL/TaskCarousel/metrics.csv', 'a', newline='') #apertura file
    writer = csv.writer(f, delimiter=";") #creazione writer
    
    if not file_exists:
        writer.writerow(header) #scrittura dell'header sul file

    row = [node_name, cpu_cores, memory, cnt, task, par, start_time]
    writer.writerow(row)           
  
    f.close() #chiusura del file


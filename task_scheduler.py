#!/usr/bin/env python
# coding=utf-8

from datetime import datetime
import time
import random as r
import os
from random import *
from kubernetes import client, config, watch
from subprocess import PIPE, run
import task_metrics
from kubernetes.client.exceptions import ApiException
from urllib3.exceptions import ProtocolError as protocol_error

config.load_kube_config()
v1 = client.CoreV1Api()

max_par = 5

def takeStartTime():  # tempo di inizio esecuzione (metrica del tempo)
    now = datetime.now()
    time = now.strftime("%H:%M:%S")
    h = now.strftime("%H")
    m = now.strftime("%M")
    s = now.strftime("%S")
    start_time = int(h) * 3600 + int(m) * 60 + int(s)
    print("Task started at: ", start_time, "seconds of 86400")
    return start_time


def active_pods():
    command = ['kubectl', 'get', 'pods']
    result = run(command, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    x = result.stdout.split("\n")
    #print(x[0])
    cnt = 0
    for i in range(len(x)):
        if "Running" in x[i] or "ContainerCreating" in x[i]:
            cnt = cnt+1
            #print(x[i])
    
    return cnt

def removeCompleted():
    command = ['kubectl', 'get', 'pods']
    result = run(command, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    x = result.stdout.split("\n")
    for i in range(len(x)):
        if "Completed" in x[i]:
            os.system('kubectl delete pod '+x[i].split(" ")[0])

def getStats():
    command = ['kubectl', 'top', 'nodes']
    result = run(command, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    x=result.stdout.split("\n")
    mem=""
    cpu=""
    nome="cs-modeling1"
    for i in range(len(x)):
        if "cs-modeling1" in x[i]:
            lst=x[i].split(" ")
            lst = list(filter(None, lst))
            cpu=lst[1]
            mem=lst[3]
            break
    return nome, cpu, mem

def best_request_time(nodes):  # seleziona in modo randomico il task e i parametri
    if not nodes:
        return []

    task = str(r.randint(1, 3))
    par = str(r.randint(1, 5))
    return nodes[0], task, par

def nodes_available():  # restituisce i nodi in stato di pronto
    ready_nodes = []
    for n in v1.list_node().items:
        # This loops over the nodes available. n is the node. We are trying to schedule the pod on one of those nodes.
        for status in n.status.conditions:  # ricerca dei nodi pronti
            if status.status == "True" and status.type == "Ready":
                ready_nodes.append(n.metadata.name)
    return ready_nodes

def createDeployment(name, task, par):

    return '''apiVersion: v1
kind: Pod
metadata:
  name: '''+name+'''
  labels:
    purpose: demonstrate-command
spec:
  containers:
  - name: custom-scheduler-container
    image: giulia99/task_carousel:first_tag
    command: ["python","task_driver.py"]
    args: ["'''+str(task)+'''", "'''+str(par)+'''"]
  restartPolicy: OnFailure'''

def main(resource_version=None):
    w = watch.Watch()
    cnt = 1
    oldtime=time.time()
    cronometro=0
    firstTime=False
    while True:
        try:
            for event in w.stream(v1.list_namespaced_pod, "default", resource_version=resource_version):
                num_pod=active_pods()
                if num_pod<=5:
                    print("Active pods: ", num_pod)
                    node, task, par=best_request_time(nodes_available())
                    name="custom-scheduler"+str(cnt)
                    deplo=createDeployment(name, task, par)
                    f = open("/home/ec2-user/script/DRL/TaskCarousel/deplo.yaml", "w")
                    f.write(deplo)
                    f.close()
                    os.system('kubectl apply -f /home/ec2-user/script/DRL/TaskCarousel/deplo.yaml')
                    start_time = takeStartTime()
                    cnt=cnt+1
                    print("\t\t------------------------------------------------------------")
                    print("\t\t|Now: ", time.time(), "|\n\t\t|Oldtime: ", oldtime, "|\n\t\t|Diff: ", time.time()-oldtime, "|")
                    print("\t\t------------------------------------------------------------")
                    oldtime=time.time()
                    time.sleep(60)
                    name, cpu, mem = getStats()
                    print("\t\t\t--------------------------")
                    print("\t\t\t|INFO NODO")
                    print("\t\t\t|1) Nome: ", name)
                    print("\t\t\t|2) CPU: ", cpu)
                    print("\t\t\t|3) Memoria: ", mem)
                    print("\t\t\t--------------------------")

                    task_metrics.writeOnFile(node, cpu, mem, num_pod, task, par, start_time)
                    removeCompleted()
        except ApiException as e:
            if e.status==410:
                return main(resource_version=None)
            else:
                raise
        except protocol_error as e:
            print("urllib3 Connection reset error: %s" % str(e))
            time.sleep(5)
            continue
    return last_resource_version


if __name__ == '__main__':
    last_resource_version=main()
    print('last_resource_version', last_resource_version)
    main(last_resource_version)



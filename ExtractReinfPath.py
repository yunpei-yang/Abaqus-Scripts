#This script uses detects the reinforcement element sets in an odb file and use them to create a path for analyzing simulation data
#It detects reinforcement elements, extract connecting nodes, and sequence the nodes in the correct order
#Sequencing is done by starting from an end point on the left and counting the elements and nodes using element and node connectivity data
#Works for belts ,overlays, and plies
#Works for 2d axisymmetric models, where reinforcement elements are wires, need more sophisticated method if model is 3d

#How to use: keep the script at a desired location, change name variable to the part instance in the odb and path variable to the directory for this script
#Run this script in CAE with your desired odb open will extract the path for the reinforcements

#Created by Yunpei Yang 08/10/2022

from abaqus import *
from abaqusConstants import *
from caeModules import *
from driverUtils import executeOnCaeStartup
import sys
#from importlib import reload #This line will be needed if using python 3, python 2 do not need this

#Instance names which the script will extract the path from
#Instances=['BT',] 
Instances=['BELTANDTREAD-1','CARCASS-1']
path='/u/rdsnfs3/ac39898/Abaqus/Scripts' #Keep the script some place handy and write the path here
Reinforced=['BELT','OVERLAY','PLY']

if __name__=='__main__':
    if path in sys.path: #Add the path of the script to the python module paths
        pass
    else:
        sys.path.append(path)
    #from ExtractReinfPath2 import ExtractPath 
    #from ExtractReinfPath2 import pathcreation1
    import ExtractReinfPath #Import the module
    reload(ExtractReinfPath) #The reload command allows changes in the modules to take effect without closing/reopening CAE, need to use importlib module if using python 3
    ExtractReinfPath.ExtractPath(Instances,Reinforced)

def ExtractPath(Instances,Reinforced):

    odb=session.odbs[session.odbs.keys()[0]] #By default, use the first odb open in the session to extract the path

    for Name in Instances:
        try:
            part=odb.rootAssembly.instances[Name]
        except:
            print('Instance %s not found'%Name)
            continue
        nodelabel2num={}
        nodenum2label={}
        for i in range(len(part.nodes)):
            nodelabel2num[part.nodes[i].label]=i
            nodenum2label[i]=part.nodes[i].label
            
        elesetlst=part.elementSets.keys()
        beltcntr=1
        for eleset in elesetlst: #cycle through all element set in the BT part instance
            eleset=eleset.upper()
            Reinfcpn=False
            for component in Reinforced: #Check to see if this element set belongs to one of the reinforced components
                if eleset.startswith(component):
                    Reinfcpn=True
                    break
            if Reinfcpn:
                if eleset.endswith('CENTERLINE'): # 'Centerline' at the end of the element set is our cue that this element set includes the reinforcement elements
                #if (eleset.endswith('CENTERLINE') or eleset.endswith('REINF')):
                    nodelist =pathcreation(part,eleset, nodelabel2num, nodenum2label)
                    session.Path(name=eleset, type=NODE_LIST, expression=((Name, nodelist), )) #Create path using the same name as the element set
            else:
                pass
        # if eleset.startswith('BELT'): #If the name begins with belt, check further
        #     if (eleset.endswith('CENTERLINE') or eleset.endswith('REINF')): #If the name also ends with centerline or reinf, we can know this set is the reinforcement element set
        #         #nodelist=pathcreation(bt,eleset)
        #         #This block of code extracts the nodes of the reinforcement elments and places them in the same order as the elements
        #         #This assumes that element generation is following a single direction (nodes do not need to be in the same order)
                
        #         nodelist =pathcreation1(bt,eleset, nodelabel2num, nodenum2label)
        #         session.Path(name=eleset, type=NODE_LIST, expression=((Name, nodelist), )) #The loop should reach belt 1 first then belt 2 and the next, thus path names are created accordingly
        # elif eleset.startswith('OVERLAY'):
        #     if eleset.endswith('CENTERLINE'): #or eleset.endswith('REINF')):
        #         #nodelist=pathcreation(bt,eleset)
        #         nodelist =pathcreation1(bt,eleset, nodelabel2num, nodenum2label)
        #         session.Path(name=eleset, type=NODE_LIST, expression=((Name, nodelist), ))
        # else:
        #     pass
    return

def pathcreation(part,eleset, nodelabel2num, nodenum2label): 
    elements=part.elementSets[eleset].elements
    elem2nodemap={}
    node2elemmap={}
    for element in elements:
        elem2nodemap[element.label]=(nodelabel2num[element.connectivity[0]],nodelabel2num[element.connectivity[1]])
        for node in elem2nodemap[element.label]:
            if node in node2elemmap:
                node2elemmap[node].append(element.label)
            else:
                node2elemmap[node]=[element.label,]
    endpoints=[]
    endcoord=[]
    for node in node2elemmap:
        if len(node2elemmap[node])<2:
            endpoints.append(node)
            endcoord.append(part.nodes[node].coordinates[1])
    nodelist=[endpoints[endcoord.index(max(endcoord))],] #Set the startpoint to the be end point which is on the most left
    nodes=elem2nodemap[node2elemmap[nodelist[-1]][0]]
    countedElems=[node2elemmap[nodelist[-1]][0],]
    for node in nodes:
        if not node in nodelist:
            nodelist.append(node)
    while not nodelist[-1] in endpoints:
        elems=node2elemmap[nodelist[-1]]
        for elem in elems:
            if not elem in countedElems:
                nodes=elem2nodemap[elem]
                for node in nodes:
                    if not node in nodelist:
                        nodelist.append(node)
                        countedElems.append(elem)
    # i=0
    # for idx in argsort(coordlist):
    #     nodelist[idx]=nodelist1[i]
    #     i=i+1
    for i in range(len(nodelist)):
        nodelist[i]=nodenum2label[nodelist[i]]
    nodelist=tuple(nodelist)
    return nodelist
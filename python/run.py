#!/usr/bin/python

#-------------------------------------------Imports
from subprocess import call
import os
import webbrowser
from xml.etree import ElementTree as ET
from os import listdir
from os.path import isfile, join
from PIL import Image
import subprocess
from operator import itemgetter
#-------------------------------------------Classes
class OPJ_Image(object):
    def __init__(self):
        self.name = ""
        self.CPUUsageBySoftware ={}
        self.MemUsageBySoftware = {}
        self.sizeInPixel = 0

class OPJ_Software(object):
    def __init__(self):
        self.UniqueName = ""
        self.cmd = ""
        self.optionsString = ""
        self.outputImgExtension = ""

#-------------------------------------------Global variables

softwareList = {}
imageList = {}
inputPath = ""
outputPath = ""
tmpFile = "tmp.txt"
cofFile = "conf.xml"

#-------------------------------------------Function definitions


def parseConfFile():

    tree = ET.parse(cofFile)
    root = tree.getroot()

    #get paths
    global outputPath
    global inputPath

    inputPath = root.find('inputPath').text
    if not inputPath.endswith("/"):
        inputPath += "/"
    outputPath = root.find('outputPath').text
    if not outputPath.endswith("/"):
        outputPath += "/"
        if not os.path.exists(outputPath):
            os.makedirs(outputPath)


    #fill software array
    root = root.find('softwareList')

    for s in root:
        newSoftware = OPJ_Software()
        newSoftware.UniqueName = s.find('UniqueName').text
        newSoftware.cmd = s.find('cmd').text
        newSoftware.optionsString = s.find('optionsString').text
        newSoftware.outputImgExtension = s.find('outputImgExtension').text
        softwareList[newSoftware.UniqueName] = newSoftware

def getSizeInPixel(filepath):
    width, height = Image.open(open(filepath)).size
    return width*height



def getCPUUsage1Img1Software(imgName, software):
    outputImagePath = outputPath + imgName.split(".")[0] + "." + software.outputImgExtension
    os.system("(time "+software.cmd +" -i " +inputPath+imgName+ " -o " + outputImagePath + " " + software.optionsString + " >/dev/null 2>&1) 2> "+tmpFile)
    tmpFileRef = open(tmpFile, 'r')
    cmd_out = tmpFileRef.read().split("user")[0].split("real")[1].strip()
    realTimeInSeconds = int(cmd_out.split("m")[0]) * 60 + float(cmd_out.split("m")[1].split("s")[0])
    tmpFileRef.close()
    os.remove(tmpFile)
    return realTimeInSeconds

def getMemoryUsage1Img1Software(imgName, software):
    tmpStackFile = 'tmpStack.txt'
    tmpHeapFile = 'tmpHeap.txt'
    tmpHeapExtraFile = 'tmpHeapExtra.txt'
    outputImagePath = outputPath + imgName.split(".")[0] + "." + software.outputImgExtension
    os.system("(valgrind --smc-check=all --trace-children=yes --tool=massif --pages-as-heap=yes --detailed-freq=1000000 --massif-out-file="+tmpFile+" "+software.cmd +" -i " +inputPath+imgName+ " -o " + outputImagePath + " " + software.optionsString + " )>/dev/null 2>&1")
    #print "(valgrind --smc-check=all --trace-children=yes --tool=massif --pages-as-heap=yes --detailed-freq=1000000 --massif-out-file="+tmpFile+" "+software.cmd +" -i " +inputPath+imgName+ " -o " + outputImagePath + " " + software.optionsString + " )>/dev/null 2>&1"

    os.system("cat "+tmpFile+" | grep mem_stacks_B | cut -d '=' -f2 | sort -nr | head -1 > "+tmpStackFile)
    os.system("cat "+tmpFile+" | grep mem_heap_B | cut -d '=' -f2 | sort -nr | head -1 > "+ tmpHeapFile)
    os.system("cat "+tmpFile+" | grep mem_heap_extra_B | cut -d '=' -f2 | sort -nr | head -1 > " + tmpHeapExtraFile)
    os.system("paste "+tmpStackFile+" "+tmpHeapFile+" "+tmpHeapExtraFile+" -d '+' | bc > " + tmpFile)
    

    tmpFileRef = open(tmpStackFile, 'r')
    totalMemUsage = int(tmpFileRef.read())
    tmpFileRef.close()
    #print "stack: " + str(totalMemUsage)

    tmpFileRef = open(tmpHeapFile, 'r')
    totalMemUsage = int(tmpFileRef.read())
    tmpFileRef.close()
    #print "Heap: " + str(totalMemUsage)

    tmpFileRef = open(tmpHeapExtraFile, 'r')
    totalMemUsage = int(tmpFileRef.read())
    tmpFileRef.close()
    #print "Hep extra: " + str(totalMemUsage)

    os.remove(tmpStackFile)
    os.remove(tmpHeapFile)
    os.remove(tmpHeapExtraFile)
    tmpFileRef = open(tmpFile, 'r')
    totalMemUsage = int(tmpFileRef.read())
    tmpFileRef.close()
    os.remove(tmpFile)
    print "total: " + str(totalMemUsage)
    return totalMemUsage
    

def processImages():
    global inputPath
    global outputPath
    for f in listdir(inputPath):
        if isfile(join(inputPath,f)):
            newImg = OPJ_Image()
            newImg.name = f
            newImg.sizeInPixel = getSizeInPixel(inputPath + newImg.name)
            for s in softwareList:
                newImg.CPUUsageBySoftware[s] = getCPUUsage1Img1Software(newImg.name, softwareList[s])
                newImg.MemUsageBySoftware[s] = getMemoryUsage1Img1Software(newImg.name, softwareList[s])
            imageList[newImg.name] = newImg
            


def printResults():
    for imgIndex in imageList:
        print "Path: " + inputPath +imageList[imgIndex].name
        print "Size in px: " + str(imageList[imgIndex].sizeInPixel)
        for softIndex in softwareList:
            print "\tCPU time using: " + softIndex + " is: " + str(imageList[imgIndex].CPUUsageBySoftware[softIndex])
            print "\tMemory using: " + softIndex + " is: " + str(imageList[imgIndex].MemUsageBySoftware[softIndex])
        print "\n"


def drawCharts():

    # construct the data arrays for the javascript charts
    newImageList = imageList
    ColumnChartTitlesList = ['Software']
    ColumnChartCPUDataList = ['']
    ColumnChartMemDataList = ['']

    LineChartTitlesList = ['Imagesize(Pixels)']
    LineChartCPUDataList = []
    LineChartMemDataList = []
    
    sizeAndCPUPerImg = {}
    sizeAndMemPerImg = {}
    
    for s in softwareList:
        totCPU = 0.0
        totMem = 0.0
        for img in newImageList:
            totCPU += newImageList[img].CPUUsageBySoftware[s]
            totMem += newImageList[img].MemUsageBySoftware[s]
            
            if not img in sizeAndCPUPerImg.keys():
                sizeAndCPUPerImg[img] = [newImageList[img].sizeInPixel]
                sizeAndMemPerImg[img] = [newImageList[img].sizeInPixel]
            sizeAndCPUPerImg[img].append(newImageList[img].CPUUsageBySoftware[s])
            sizeAndMemPerImg[img].append(newImageList[img].MemUsageBySoftware[s])


        ColumnChartTitlesList.append(softwareList[s].UniqueName)
        ColumnChartCPUDataList.append(totCPU)
        ColumnChartMemDataList.append(totMem)
        
        LineChartTitlesList.append(softwareList[s].UniqueName)


    for img in sizeAndCPUPerImg:
        LineChartCPUDataList.append(sizeAndCPUPerImg[img])
        LineChartMemDataList.append(sizeAndMemPerImg[img])

    LineChartCPUDataList = sorted(LineChartCPUDataList, key=itemgetter(0))
    LineChartMemDataList = sorted(LineChartMemDataList, key=itemgetter(0))
    LineChartCPUDataList.insert(0,LineChartTitlesList)
    LineChartMemDataList.insert(0,LineChartTitlesList)

    #Stringify lists to put them in the HTML code
    ColumnChartStringDataCPU = str([ColumnChartTitlesList, ColumnChartCPUDataList])
    ColumnChartStringDataMem = str([ColumnChartTitlesList, ColumnChartMemDataList])

    LineChartStringDataCPU = str(LineChartCPUDataList)
    LineChartStringDataMem = str(LineChartMemDataList)

    print ColumnChartStringDataCPU
    print ColumnChartStringDataMem

    print LineChartStringDataCPU
    print LineChartStringDataMem

    ColumnChartOptionsCPU = """{title:'Time(Seconds)',hAxis:{title:'Software',titleTextStyle:{color:'black'}}}"""
    ColumnChartOptionsMem = """{title:'Memory(Bytes)',hAxis:{title:'Software',titleTextStyle:{color:'black'}}}"""

    LineChartOptionsCPU = """{title:'Image size vs. Time',hAxis:{title:'Image size(Pixels)'},vAxis:{title:'Time(Seconds)'}, curveType:'function', legend: { position: 'bottom' }, pointSize : 5}"""
    LineChartOptionsMem = """{title:'Image size vs. Memory',hAxis:{title:'Image size(Pixels)'},vAxis:{title:'Memory(Bytes)'}, curveType:'function', legend: { position: 'bottom' }, pointSize : 5}"""
    

    #HTML construction
    htmlFileName = "chart.html"
    f = open(htmlFileName,'w')
    chartHTML = """
<html>
   <head>
      <script type="text/javascript" src="https://www.google.com/jsapi"></script>
      <script type="text/javascript">
         google.load("visualization", "1", {packages:["corechart"]});
         google.setOnLoadCallback(drawChart);
         function drawChart() {
         
         
         //First chart
         var data = google.visualization.arrayToDataTable("""+ColumnChartStringDataCPU+""");
         
         var options = """+ColumnChartOptionsCPU+""";
         
         var chart = new google.visualization.ColumnChart(document.getElementById('chart_div'));
         
         chart.draw(data, options);
         
         
         //Second chart
         data = google.visualization.arrayToDataTable("""+ColumnChartStringDataMem+""");
         
         options = """+ColumnChartOptionsMem+""";
         
         chart = new google.visualization.ColumnChart(document.getElementById('chart_div2'));
         
         chart.draw(data, options);
         
         //Third chart
         data = google.visualization.arrayToDataTable("""+LineChartStringDataCPU+""");
         //data.sort([{column: 1}]);
         
         options = """+LineChartOptionsCPU+""";
         
         chart = new google.visualization.LineChart(document.getElementById('chart_div3'));
         
         chart.draw(data, options);
         
         
         
         //Fourth chart
         data = google.visualization.arrayToDataTable("""+LineChartStringDataMem+""");
         //data.sort([{column: 1}]);
         options = """+LineChartOptionsMem+""";
         
         chart = new google.visualization.LineChart(document.getElementById('chart_div4'));
         
         chart.draw(data, options);
         
         
         
         }
      </script>
   </head>
   <body>
      <div id="chart_div" style="width: 50%; height: 500px;float:left"></div>
      <div id="chart_div2" style="width: 50%; height: 500px;float:left"></div>
      <div id="chart_div3" style="width: 50%; height: 500px;float:left"></div>
      <div id="chart_div4" style="width: 50%; height: 500px;float:left"></div>
   </body>
</html>
"""

    f.write(chartHTML)
    f.close()
    webbrowser.open_new_tab(htmlFileName)
    #os.remove(htmlFileName)

#-------------------------------------------Starting the script
parseConfFile()
processImages()
printResults()
drawCharts()




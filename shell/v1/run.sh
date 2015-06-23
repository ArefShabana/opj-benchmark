#!/bin/bash
source ./conf.cfg


###################functions

Calculate_time () {
(time $1 >/dev/null 2>&1) 2> tmp.txt
TMP=$(cat tmp.txt | grep real | awk '{$2=$2}1' | cut -d ' ' -f2)
TMP_TO_RET_TIME=$(paste <(echo $TMP | cut -d 'm' -f1) <(echo " * 60") | bc)
TMP_TO_RET_TIME=$(paste <(echo $TMP | cut -d 'm' -f2 | cut -d 's' -f1) <(echo " + $TMP_TO_RET_TIME") | bc)

}


Calculate_mem () {
(valgrind --smc-check=all --trace-children=yes --tool=massif --pages-as-heap=yes --detailed-freq=1000000 --massif-out-file=tmp.txt $1 )>/dev/null 2>&1
TMP_TO_RET_MEM=$(cat tmp.txt | grep mem_heap_B | cut -d '=' -f2 | sort -t= -nr -k3 | head -1)
TMP=$(cat tmp.txt | grep mem_heap_extra_B | cut -d '=' -f2 | sort -t= -nr -k3 | head -1)
TMP1=$(cat tmp.txt | grep mem_stacks_B | cut -d '=' -f2 | sort -t= -nr -k3 | head -1)
TMP_TO_RET_MEM=$(echo "$TMP_TO_RET_MEM + $TMP + $TMP1 " | bc)

}


##return size in Pixels
Calculate_file_size_pixel () {
TMP_TO_RET_SIZE=$(identify $1 | cut -d ' ' -f3 | sed -r 's/[x]+/*/g' | bc)
}



draw_ColumnChart (){

TEMP=$(mktemp -t chart.XXXXX)

cat > $TEMP <<EOF
<html>
  <head>
    <script type="text/javascript" src="https://www.google.com/jsapi"></script>
    <script type="text/javascript">
      google.load("visualization", "1", {packages:["corechart"]});
google.setOnLoadCallback(drawChart);
function drawChart() {


  //First chart
  var data = google.visualization.arrayToDataTable($1);

  var options = $2;

  var chart = new google.visualization.ColumnChart(document.getElementById('chart_div'));

  chart.draw(data, options);


  //Second chart
  data = google.visualization.arrayToDataTable($3);

  options = $4;

  chart = new google.visualization.ColumnChart(document.getElementById('chart_div2'));

  chart.draw(data, options);


  //Third chart
  data = google.visualization.arrayToDataTable($5);
  data.sort([{column: 1}]);

        options = $6;

        chart = new google.visualization.LineChart(document.getElementById('chart_div3'));

        chart.draw(data, options);



  //Fourth chart
  data = google.visualization.arrayToDataTable($7);
  data.sort([{column: 1}]);
        options = $8;

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

EOF

# open browser
case $(uname) in
   Darwin)
      open -a /Applications/Google\ Chrome.app $TEMP
      ;;

   Linux|SunOS)
      firefox $TEMP
      ;;
 esac


if [ -f $TEMP ];
then
   rm $TEMP
fi
}



#####################

echo "Test : $TEST_NAME"

TOTAL_TIME_1=0
TOTAL_TIME_2=0
TOTAL_MEM_1=0
TOTAL_MEM_2=0
SIZE_VS_TIME="[['Imagesize(Pixels)','OpenJPEG Time(Seconds)','KKDU Time(Seconds)']"
SIZE_VS_MEM="[['Imagesize(Pixels)','OpenJPEG Memory(Bytes)','KKDU Memory(Bytes)']"

IMAGES=$(ls $INPUT_FOLDER -1 | tr '\n' ';')
IFS=';' read -a IMAGES <<< "${IMAGES}"

for i in "${!IMAGES[@]}"
do 
	#printf "%s/%s" "$INPUT_FOLDER" "${IMAGES[$i]}"
	IMAGES[$i]=$(printf "%s/%s" "$INPUT_FOLDER" "${IMAGES[$i]}")
done 


for i in "${IMAGES[@]}" 
do 
  #calculate time 1
	echo "$SOFTWARE_1 -i $i -o tmp.jp2 $SOFTWARE_1_OPTIONS"
	Calculate_time "$SOFTWARE_1 -i $i -o tmp.jp2 $SOFTWARE_1_OPTIONS"
	TOTAL_TIME_1=$(echo $TOTAL_TIME_1 + $TMP_TO_RET_TIME | bc)
	rm tmp.jp2

    #calculate memory 1
	echo "Memory ---- $SOFTWARE_1 -i $i -o tmp.jp2 $SOFTWARE_1_OPTIONS"
	Calculate_mem "$SOFTWARE_1 -i $i -o tmp.jp2 $SOFTWARE_1_OPTIONS"
	TOTAL_MEM_1=$(echo $TOTAL_MEM_1 + $TMP_TO_RET_MEM | bc)
	rm tmp.jp2

    #add element [size, time1 to size-vs-time array
    # and element [size, mem1 to size-vs-mem array
    Calculate_file_size_pixel $i
    SIZE_VS_TIME=$(echo $SIZE_VS_TIME,[$TMP_TO_RET_SIZE,$TMP_TO_RET_TIME)
    SIZE_VS_MEM=$(echo $SIZE_VS_MEM,[$TMP_TO_RET_SIZE,$TMP_TO_RET_MEM)


    #calculate time 2
	Calculate_time "$SOFTWARE_2 -i $i -o tmp.j2c $SOFTWARE_2_OPTIONS"
	TOTAL_TIME_2=$(echo $TOTAL_TIME_2 + $TMP_TO_RET_TIME | bc)
	rm tmp.j2c


    #calculate memory 2
	Calculate_mem "$SOFTWARE_2 -i $i -o tmp.j2c $SOFTWARE_2_OPTIONS"
	TOTAL_MEM_2=$(echo $TOTAL_MEM_2 + $TMP_TO_RET_MEM | bc)
	rm tmp.j2c

    #add element ,time 2] to size-vs-time array, it becomes [size, time 1, time 2]]
    #and element ,mem 2] to size-vs-mem array, it becomes [size, mem 1, mem 2]]
    SIZE_VS_TIME=$(echo $SIZE_VS_TIME,$TMP_TO_RET_TIME])
    SIZE_VS_MEM=$(echo $SIZE_VS_MEM,$TMP_TO_RET_MEM])

done 

#close the array of the size
SIZE_VS_TIME=$(echo $SIZE_VS_TIME])
SIZE_VS_MEM=$(echo $SIZE_VS_MEM])

NUM_IMAGES=${#IMAGES[@]}

TOTAL_TIME_1=$(echo $TOTAL_TIME_1 / $NUM_IMAGES | bc -l)
TOTAL_TIME_2=$(echo $TOTAL_TIME_2 / $NUM_IMAGES | bc -l)
TOTAL_MEM_1=$(echo $TOTAL_MEM_1 / $NUM_IMAGES | bc -l)
TOTAL_MEM_2=$(echo $TOTAL_MEM_2 / $NUM_IMAGES | bc -l)


ARG1="[['Software','OpenJPEG','Kakadu'],['',$TOTAL_TIME_1,$TOTAL_TIME_2]]"
ARG2="{title:'Time(Seconds)',hAxis:{title:'Software',titleTextStyle:{color:'black'}}}"
ARG3="[['Software','OpenJPEG','Kakadu'],['',$TOTAL_MEM_1,$TOTAL_MEM_2]]"
ARG4="{title:'Memory(Bytes)',hAxis:{title:'Software',titleTextStyle:{color:'black'}}}"
ARG5=$SIZE_VS_TIME
ARG6="{title:'Image size vs. Time',hAxis:{title:'Image size(Pixels)'},vAxis:{title:'Time(Seconds)'}, curveType:'function', legend: { position: 'bottom' }, pointSize : 5}"
ARG7=$SIZE_VS_MEM
ARG8="{title:'Image size vs. Memory',hAxis:{title:'Image size(Pixels)'},vAxis:{title:'Memory(Bytes)'}, curveType:'function', legend: { position: 'bottom' }, pointSize : 5}"

draw_ColumnChart "$ARG1" "$ARG2" "$ARG3" "$ARG4" "$ARG5"  "$ARG6" "$ARG7"  "$ARG8"

if [ -f tmp.txt ];
then
   rm tmp.txt
fi

#(time $1 >/dev/null 2>&1) 2> tmp.txt
#time $SOFTWARE_1


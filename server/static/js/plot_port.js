function plot_port(myChart, tables1, tables2, x_label, cpu, wait_cpu, mem, jvm, tcp, time_wait, close_wait, is_jvm, iodelay, rkbs, wkbs, net) {
    // 以下是使用快速排序算法排序
    /*let cpu_sorted = quickSort(cpu);
    let IO_sorted = quickSort(IO);
	let net_sorted = quickSort(net);*/
	// 以下是使用默认的排序方法，冒泡排序
	let cpu_sorted = [...cpu];
	//let wait_cpu_sorted = [...wait_cpu];
    let iodelay_sorted = [...iodelay];
    let rkbs_sorted = [...rkbs];
    let wkbs_sorted = [...wkbs];
    let net_sorted = [...net];
    cpu_sorted.sort(function (a, b) {return a - b});
    rkbs_sorted.sort(function (a, b) {return a - b});
    wkbs_sorted.sort(function (a, b) {return a - b});
    iodelay_sorted.sort(function (a, b) {return a - b});
    net_sorted.sort(function (a, b) {return a - b});
	// 以上是冒泡排序方法

    let start_time = Date.parse(new Date(x_label[0]));
    let end_time = Date.parse(new Date(x_label[x_label.length - 1]));
    let dur = ((end_time - start_time) / 3600000).toFixed(2);
    let duration = dur + 'h';
    if (dur < 1) {
        dur = ((end_time - start_time) / 60000).toFixed(2);
        duration = dur + 'm';
        if (dur < 1) {
            dur = ((end_time - start_time) / 1000).toFixed(2);
            duration = dur + 's';
        }
    }

    option = {
        title: [
            {
                text: 'CPU(%), Max: ' + cpu_sorted.slice(-1)[0].toFixed(2) + '%, 90%Line: ' + cpu_sorted[parseInt(0.9 * cpu_sorted.length)].toFixed(2) + '%, Duration: ' + duration,
                x: 'center',
                y: 5,
                textStyle: {
                    fontSize: 13,
                },
            },
            {
                text: 'Memory(G), Max: ' + findMax(mem).toFixed(2) + 'G, Duration: ' + duration,
                x: 'center',
                y: 350,
                textStyle: {
                    fontSize: 13,
                },
            },
            {
                text: 'IO, IOdelay: ' + iodelay_sorted.slice(-1)[0].toFixed(2) + '%, Max Read: ' + rkbs_sorted.slice(-1)[0].toFixed(2) + 'Mb/s, Max Write: ' + wkbs_sorted.slice(-1)[0].toFixed(2) + 'Mb/s, Duration: ' + duration,
                x: 'center',
                y: 700,
                textStyle: {
                    fontSize: 13
                }
            },
            {
                text: 'TCP, TCP: ' + findMax(tcp).toFixed(2) + ', Duration: ' + duration,
                x: 'center',
                y: 1050,
                textStyle: {
                    fontSize: 13,
                },
            }
        ],

        grid: [
            {
                left: '5%',
                right: '5%',
                top: 50,
                height: 250
            },
            {
                left: '5%',
                right: '5%',
                top: 400,
                height: 250
            },
            {
                left: '5%',
                right: '5%',
                top: 750,
                height: 250
            },
            {
                left: '5%',
                right: '5%',
                top: 1100,
                height: 250
            }
        ],

        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross'
            }
        },

        color: ['red', 'blue', 'red', 'blue', 'orange', 'blue', 'red', 'orange', 'blue', 'red'],
        legend: [
            {
                data: ['CPU', 'Wait_CPU'],
                x: 'center',
                y: 25,
                icon: 'line'
            },
            {
                data: ['Memory'],
                x: 'center',
                y: 375,
                icon: 'line'
            },
            {
                data: ['rMb/s', 'wMb/s', 'IO_Delay'],
                x: 'center',
                y: 725,
                icon: 'line'
            },
            {
                data: ['CLOSE_WAIT', 'TIME_WAIT', 'TCP'],
                x: 'center',
                y: 1075,
                icon: 'line'
            }
        ],

        dataZoom: [
            {
                xAxisIndex: [0, 1, 2, 3],
                type: 'inside',
                startValue: 0,
                endValue: cpu.length
            },
            {
                xAxisIndex: [0, 1, 2, 3],
                type: 'slider',
                startValue: 0,
                endValue: cpu.length
            }
        ],

        xAxis: [
            {
                gridIndex: 0,
                type: 'category',
                boundaryGap: false,
                data: x_label,
                axisTick: {
                    alignWithLabel: true,
                    interval: 'auto'
                },
                axisLabel: {
                    interval: 'auto',
                    showMaxLabel: true
                }
            },
            {
                gridIndex: 1,
                type: 'category',
                boundaryGap: false,
                data: x_label,
                axisTick: {
                    alignWithLabel: true,
                    interval: 'auto'
                },
                axisLabel: {
                    interval: 'auto',
                    showMaxLabel: true
                }
            },
            {
                gridIndex: 2,
                type: 'category',
                boundaryGap: false,
                data: x_label,
                axisTick: {
                    alignWithLabel: true,
                    interval: 'auto'
                },
                axisLabel: {
                    interval: 'auto',
                    showMaxLabel: true
                }
            },
            {
                gridIndex: 3,
                type: 'category',
                boundaryGap: false,
                data: x_label,
                axisTick: {
                    alignWithLabel: true,
                    interval: 'auto'
                },
                axisLabel: {
                    interval: 'auto',
                    showMaxLabel: true
                }
            }
        ],

        yAxis: [
            {
                gridIndex: 0,
                name: 'CPU(%)',
                type: 'value',
                max: 100
            },
            {gridIndex: 0},
            {
                gridIndex: 1,
                name: 'Memory(G)',
                type: 'value',
                max: (findMax(mem) + 1).toFixed(2)
            },
            {gridIndex: 1},
            {
                gridIndex: 2,
                name: 'Speed(Mb/s)',
                type: 'value',
                max: Math.max(rkbs_sorted.slice(-1)[0], wkbs_sorted.slice(-1)[0]).toFixed(2)
            },
            {
                gridIndex: 2,
                name: 'IO_Delay(%)',
                type: 'value',
                max: iodelay_sorted.slice(-1)[0].toFixed(2)
            },
            {
                gridIndex: 3,
                name: 'TCP',
                type: 'value',
                max: Math.max(findMax(time_wait), findMax(close_wait)).toFixed(2)
            },
            {
                gridIndex: 3,
                name: 'TCP',
                type: 'value',
                max: findMax(tcp).toFixed(2),
            }
        ],
        series: [
            {
                name: 'CPU',
                type: 'line',
                xAxisIndex: 0,
                yAxisIndex: 0,
                showSymbol: false,
                lineStyle: {
                    width: 1,
                    color: 'red'
                },
                data: cpu
            },
            {
                name: 'Wait_CPU',
                type: 'line',
                xAxisIndex: 0,
                yAxisIndex: 0,
                showSymbol: false,
                lineStyle: {
                    width: 1,
                    color: 'blue'
                },
                data: wait_cpu
            },
            {
                name: 'Memory',
                type: 'line',
                xAxisIndex: 1,
                yAxisIndex: 2,
                showSymbol: false,
                lineStyle: {
                    width: 1,
                    color: 'red'
                },
                data: mem
            },
            {
                name: 'JVM',
                type: 'line',
                xAxisIndex: 1,
                yAxisIndex: 2,
                showSymbol: false,
                lineStyle: {
                    width: 1,
                    color: 'blue'
                },
                data: []
            },
            {
                name: 'rMb/s',
                type: 'line',
                xAxisIndex: 2,
                yAxisIndex: 4,
                showSymbol: false,
                lineStyle: {
                    width: 1,
                    color: 'orange'
                },
                data: rkbs
            },
            {
                name: 'wMb/s',
                type: 'line',
                xAxisIndex: 2,
                yAxisIndex: 4,
                showSymbol: false,
                lineStyle: {
                    width: 1,
                    color: 'blue'
                },
                data: wkbs
            },
            {
                name: 'IO_Delay',
                type: 'line',
                xAxisIndex: 2,
                yAxisIndex: 5,
                showSymbol: false,
                lineStyle: {
                    width: 1,
                    color: 'red'
                },
                data: iodelay
            },
            {
                name: 'CLOSE_WAIT',
                type: 'line',
                xAxisIndex: 3,
                yAxisIndex: 6,
                showSymbol: false,
                lineStyle: {
                    width: 1,
                    color: 'orange'
                },
                data: close_wait
            },
            {
                name: 'TIME_WAIT',
                type: 'line',
                xAxisIndex: 3,
                yAxisIndex: 6,
                showSymbol: false,
                lineStyle: {
                    width: 1,
                    color: 'blue'
                },
                data: time_wait
            },
            {
                name: 'TCP',
                type: 'line',
                xAxisIndex: 3,
                yAxisIndex: 7,
                showSymbol: false,
                lineStyle: {
                    width: 1,
                    color: 'red'
                },
                data: tcp
            }
        ]
    };

    if (is_jvm === 1){
        option['title'][1].text = 'Memory(G), Max: ' + findMax(mem).toFixed(2) + 'G; JVM(G), Max: ' + findMax(jvm).toFixed(2) + 'G, Duration: ' + duration;
        option['legend'][1].data = ['Memory', 'JVM'];
        option['series'][3].data = jvm;
    }

    myChart.clear();
    myChart.setOption(option);

    tables1.rows[1].cells[1].innerHTML = cpu_sorted[parseInt(0.75 * cpu_sorted.length)].toFixed(2);
    tables1.rows[2].cells[1].innerHTML = cpu_sorted[parseInt(0.9 * cpu_sorted.length)].toFixed(2);
    tables1.rows[3].cells[1].innerHTML = cpu_sorted[parseInt(0.95 * cpu_sorted.length)].toFixed(2);
    tables1.rows[4].cells[1].innerHTML = cpu_sorted[parseInt(0.99 * cpu_sorted.length)].toFixed(2);
    tables1.rows[1].cells[2].innerHTML = rkbs_sorted[parseInt(0.75 * rkbs_sorted.length)].toFixed(2);
    tables1.rows[2].cells[2].innerHTML = rkbs_sorted[parseInt(0.9 * rkbs_sorted.length)].toFixed(2);
    tables1.rows[3].cells[2].innerHTML = rkbs_sorted[parseInt(0.95 * rkbs_sorted.length)].toFixed(2);
    tables1.rows[4].cells[2].innerHTML = rkbs_sorted[parseInt(0.99 * rkbs_sorted.length)].toFixed(2);
    tables1.rows[1].cells[3].innerHTML = wkbs_sorted[parseInt(0.75 * wkbs_sorted.length)].toFixed(2);
    tables1.rows[2].cells[3].innerHTML = wkbs_sorted[parseInt(0.9 * wkbs_sorted.length)].toFixed(2);
    tables1.rows[3].cells[3].innerHTML = wkbs_sorted[parseInt(0.95 * wkbs_sorted.length)].toFixed(2);
    tables1.rows[4].cells[3].innerHTML = wkbs_sorted[parseInt(0.99 * wkbs_sorted.length)].toFixed(2);
    tables1.rows[1].cells[4].innerHTML = iodelay_sorted[parseInt(0.75 * iodelay_sorted.length)].toFixed(2);
    tables1.rows[2].cells[4].innerHTML = iodelay_sorted[parseInt(0.9 * iodelay_sorted.length)].toFixed(2);
    tables1.rows[3].cells[4].innerHTML = iodelay_sorted[parseInt(0.95 * iodelay_sorted.length)].toFixed(2);
    tables1.rows[4].cells[4].innerHTML = iodelay_sorted[parseInt(0.99 * iodelay_sorted.length)].toFixed(2);
    tables1.rows[1].cells[7].innerHTML = net_sorted[parseInt(0.75 * net_sorted.length)].toFixed(2);
    tables1.rows[2].cells[7].innerHTML = net_sorted[parseInt(0.9 * net_sorted.length)].toFixed(2);
    tables1.rows[3].cells[7].innerHTML = net_sorted[parseInt(0.95 * net_sorted.length)].toFixed(2);
    tables1.rows[4].cells[7].innerHTML = net_sorted[parseInt(0.99 * net_sorted.length)].toFixed(2);
    myChart.on('dataZoom', function (param) {
        let start_index = myChart.getOption().dataZoom[0].startValue;
        let end_index = myChart.getOption().dataZoom[0].endValue;
        
		// 以下是使用默认的排序方法，冒泡排序
        let cpu_sorted = cpu.slice(start_index, end_index);
        let iodelay_sorted = iodelay.slice(start_index, end_index);
        let rkbs_sorted = rkbs_sorted.slice(start_index, end_index);
        let wkbs_sorted = wkbs_sorted.slice(start_index, end_index);
        let net_sorted = net.slice(start_index, end_index);
        cpu_sorted.sort();
        iodelay_sorted.sort();
        rkbs_sorted.sort();
        wkbs_sorted.sort();
        net_sorted.sort();
		// 以上是冒泡排序方法
		
		// 以下是使用快速排序算法排序
        /*let cpu_sorted = quickSort(cpu.slice(start_index, end_index));
        let IO_sorted = quickSort(IO.slice(start_index, end_index));
		let net_sorted = quickSort(net.slice(start_index, end_index));*/

        let start_time = Date.parse(new Date(x_label[start_index]));
        let end_time = Date.parse(new Date(x_label[end_index]));
        let dur = ((end_time - start_time) / 3600000).toFixed(2);
        let duration = dur + 'h';
        if (dur < 1) {
            dur = ((end_time - start_time) / 60000).toFixed(2);
            duration = dur + 'm';
            if (dur < 1) {
                dur = ((end_time - start_time) / 1000).toFixed(2);
                duration = dur + 's';
            }
        }

        if (is_jvm === 1){
            myChart.setOption({
            title: [
                {text: 'CPU(%), Max: ' + cpu_sorted.slice(-1)[0].toFixed(2) + '%, 90%Line: ' + cpu_sorted[parseInt(0.9 * cpu_sorted.length)].toFixed(2) + '%, Duration: ' + duration, x: 'center', y: 5, textStyle: {fontSize: 13}},
                {text: 'Memory(G), Max: ' + findMax(mem).toFixed(2) + 'G; JVM(G), Max: ' + findMax(jvm).toFixed(2) + 'G, Duration: ' + duration, x: 'center', y: 350, textStyle: {fontSize: 13}},
                {text: 'IO, IOdelay: ' + iodelay_sorted.slice(-1)[0].toFixed(2) + '%, Max Read: ' + rkbs_sorted.slice(-1)[0].toFixed(2) + 'Mb/s, Max Write: ' + wkbs_sorted.slice(-1)[0].toFixed(2) + 'Mb/s, Duration: ' + duration, x: 'center', y: 700, textStyle: {fontSize: 13}},
                {text: 'TCP, TCP: ' + findMax(tcp).toFixed(2) + ', Duration: ' + duration, x: 'center', y: 1050, textStyle: {fontSize: 13}}
            ]});
        } else {
            myChart.setOption({
                title: [
                    {text: 'CPU(%), Max: ' + cpu_sorted.slice(-1)[0].toFixed(2) + '%, 90%Line: ' + cpu_sorted[parseInt(0.9 * cpu_sorted.length)].toFixed(2) + '%, Duration: ' + duration, x: 'center', y: 5, textStyle: {fontSize: 13}},
                    {text: 'Memory(G), Max: ' + findMax(mem).toFixed(2) + 'G, Duration: ' + duration, x: 'center', y: 350, textStyle: {fontSize: 13}},
                    {text: 'IO, IOdelay: ' + iodelay_sorted.slice(-1)[0].toFixed(2) + '%, Max Read: ' + rkbs_sorted.slice(-1)[0].toFixed(2) + 'Mb/s, Max Write: ' + wkbs_sorted.slice(-1)[0].toFixed(2) + 'Mb/s, Duration: ' + duration, x: 'center', y: 700, textStyle: {fontSize: 13}},
                    {text: 'TCP, TCP: ' + findMax(tcp).toFixed(2) + ', Duration: ' + duration, x: 'center', y: 1050, textStyle: {fontSize: 13}}
                ]});}

        tables1.rows[1].cells[1].innerHTML = cpu_sorted[parseInt(0.75 * cpu_sorted.length)].toFixed(2);
        tables1.rows[2].cells[1].innerHTML = cpu_sorted[parseInt(0.9 * cpu_sorted.length)].toFixed(2);
        tables1.rows[3].cells[1].innerHTML = cpu_sorted[parseInt(0.95 * cpu_sorted.length)].toFixed(2);
        tables1.rows[4].cells[1].innerHTML = cpu_sorted[parseInt(0.99 * cpu_sorted.length)].toFixed(2);
        tables1.rows[1].cells[2].innerHTML = rkbs_sorted[parseInt(0.75 * rkbs_sorted.length)].toFixed(2);
        tables1.rows[2].cells[2].innerHTML = rkbs_sorted[parseInt(0.9 * rkbs_sorted.length)].toFixed(2);
        tables1.rows[3].cells[2].innerHTML = rkbs_sorted[parseInt(0.95 * rkbs_sorted.length)].toFixed(2);
        tables1.rows[4].cells[2].innerHTML = rkbs_sorted[parseInt(0.99 * rkbs_sorted.length)].toFixed(2);
        tables1.rows[1].cells[3].innerHTML = wkbs_sorted[parseInt(0.75 * wkbs_sorted.length)].toFixed(2);
        tables1.rows[2].cells[3].innerHTML = wkbs_sorted[parseInt(0.9 * wkbs_sorted.length)].toFixed(2);
        tables1.rows[3].cells[3].innerHTML = wkbs_sorted[parseInt(0.95 * wkbs_sorted.length)].toFixed(2);
        tables1.rows[4].cells[3].innerHTML = wkbs_sorted[parseInt(0.99 * wkbs_sorted.length)].toFixed(2);
        tables1.rows[1].cells[4].innerHTML = iodelay_sorted[parseInt(0.75 * iodelay_sorted.length)].toFixed(2);
        tables1.rows[2].cells[4].innerHTML = iodelay_sorted[parseInt(0.9 * iodelay_sorted.length)].toFixed(2);
        tables1.rows[3].cells[4].innerHTML = iodelay_sorted[parseInt(0.95 * iodelay_sorted.length)].toFixed(2);
        tables1.rows[4].cells[4].innerHTML = iodelay_sorted[parseInt(0.99 * iodelay_sorted.length)].toFixed(2);
        tables1.rows[1].cells[7].innerHTML = net_sorted[parseInt(0.75 * net_sorted.length)].toFixed(2);
        tables1.rows[2].cells[7].innerHTML = net_sorted[parseInt(0.9 * net_sorted.length)].toFixed(2);
        tables1.rows[3].cells[7].innerHTML = net_sorted[parseInt(0.95 * net_sorted.length)].toFixed(2);
        tables1.rows[4].cells[7].innerHTML = net_sorted[parseInt(0.99 * net_sorted.length)].toFixed(2);
    });
}

function findMax(arr) {
    let len = arr.length
    let max = arr[0];
    while (len--) {
        if (arr[len] > max) {
            max = arr[len];
        }
    }
    return max;
}

function findMin(arr) {
    let len = arr.length
    let min = arr[0];
    while (len--) {
        if (arr[len] < min) {
            min = arr[len];
        }
    }
    return min;
}

function quickSort(arr){
    if(arr.length<=1){
        return arr;
    }
    let temp = arr.pop();
    let left = [];
    let right = [];
    for(let i=0;i<arr.length;i++){
        if(arr[i]<temp){
            left.push(arr[i]);
        }else{
            right.push(arr[i]);
        }
    }
    return quickSort(left).concat(temp,quickSort(right));
}

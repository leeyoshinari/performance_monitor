function plot_port(myChart, tables1, tables2, x_label, cpu, mem, jvm, tcp, time_wait, close_wait, is_jvm, IO, net) {
    // 以下是使用快速排序算法排序
    /*let cpu_sorted = quickSort(cpu);
    let IO_sorted = quickSort(IO);
	let net_sorted = quickSort(net);*/
	// 以下是使用默认的排序方法，冒泡排序
	let cpu_sorted = [...cpu];
    let IO_sorted = [...IO];
    let net_sorted = [...net];
    cpu_sorted.sort(function (a, b) {return a - b});
    IO_sorted.sort(function (a, b) {return a - b});
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
                text: 'CPU(%), 最大值: ' + cpu_sorted.slice(-1)[0].toFixed(2) + '%, 90%Line: ' + cpu_sorted[parseInt(0.9 * cpu_sorted.length)].toFixed(2) + '%, 时间: ' + duration,
                x: 'center',
                y: 5,
                textStyle: {
                    fontSize: 13,
                },
            },
            {
                text: '内存(G), 最大值: ' + findMax(mem).toFixed(2) + 'G, 时间: ' + duration,
                x: 'center',
                y: 350,
                textStyle: {
                    fontSize: 13,
                },
            },
            {
                text: 'TCP, TCP最大值: ' + findMax(tcp).toFixed(2) + ', 时间: ' + duration,
                x: 'center',
                y: 700,
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
            }
        ],

        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross'
            }
        },

        color: ['red', 'red', 'red', 'blue', 'orange'],
        legend: [
            {
                data: ['CPU使用率'],
                x: 'center',
                y: 25,
                icon: 'line'
            },
            {
                data: ['内存'],
                x: 'center',
                y: 375,
                icon: 'line'
            },
            {
                data: ['TCP', 'TIME_WAIT', 'CLOSE_WAIT'],
                x: 'center',
                y: 725,
                icon: 'line'
            }
        ],

        dataZoom: [
            {
                xAxisIndex: [0, 1, 2],
                type: 'inside',
                startValue: 0,
                endValue: cpu.length
            },
            {
                xAxisIndex: [0, 1, 2],
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
                name: '内存(G)',
                type: 'value',
                max: (findMax(mem) + 1).toFixed(2)
            },
            {gridIndex: 1},
            {
                gridIndex: 2,
                name: 'TCP',
                type: 'value',
                max: Math.max(findMax(time_wait), findMax(close_wait)).toFixed(2)
            },
            {
                gridIndex: 2,
                name: 'TCP',
                type: 'value',
                max: findMax(tcp).toFixed(2),
            }
        ],
        series: [
            {
                name: 'CPU使用率',
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
                name: '内存',
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
                name: 'JVM内存',
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
                name: 'CLOSE_WAIT',
                type: 'line',
                xAxisIndex: 2,
                yAxisIndex: 4,
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
                xAxisIndex: 2,
                yAxisIndex: 4,
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
                xAxisIndex: 2,
                yAxisIndex: 5,
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
        option['title'][1].text = '内存(G), 最大值: ' + findMax(mem).toFixed(2) + 'G; JVM(G), 最大值: ' + findMax(jvm).toFixed(2) + 'G, 时间: ' + duration;
        option['legend'][1].data = ['内存', 'JVM内存'];
        option['series'][2].data = jvm;
        option['color'] = ['red', 'red', 'blue', 'red', 'blue', 'orange'];
    }

    myChart.clear();
    myChart.setOption(option);

    tables1.rows[1].cells[1].innerHTML = cpu_sorted[parseInt(0.75 * cpu_sorted.length)].toFixed(2);
    tables1.rows[2].cells[1].innerHTML = cpu_sorted[parseInt(0.9 * cpu_sorted.length)].toFixed(2);
    tables1.rows[3].cells[1].innerHTML = cpu_sorted[parseInt(0.95 * cpu_sorted.length)].toFixed(2);
    tables1.rows[4].cells[1].innerHTML = cpu_sorted[parseInt(0.99 * cpu_sorted.length)].toFixed(2);
    tables1.rows[1].cells[4].innerHTML = IO_sorted[parseInt(0.75 * IO_sorted.length)].toFixed(2);
    tables1.rows[2].cells[4].innerHTML = IO_sorted[parseInt(0.9 * IO_sorted.length)].toFixed(2);
    tables1.rows[3].cells[4].innerHTML = IO_sorted[parseInt(0.95 * IO_sorted.length)].toFixed(2);
    tables1.rows[4].cells[4].innerHTML = IO_sorted[parseInt(0.99 * IO_sorted.length)].toFixed(2);
    tables1.rows[1].cells[7].innerHTML = net_sorted[parseInt(0.75 * net_sorted.length)].toFixed(2);
    tables1.rows[2].cells[7].innerHTML = net_sorted[parseInt(0.9 * net_sorted.length)].toFixed(2);
    tables1.rows[3].cells[7].innerHTML = net_sorted[parseInt(0.95 * net_sorted.length)].toFixed(2);
    tables1.rows[4].cells[7].innerHTML = net_sorted[parseInt(0.99 * net_sorted.length)].toFixed(2);
    myChart.on('dataZoom', function (param) {
        let start_index = myChart.getOption().dataZoom[0].startValue;
        let end_index = myChart.getOption().dataZoom[0].endValue;
        
		// 以下是使用默认的排序方法，冒泡排序
        let cpu_sorted = cpu.slice(start_index, end_index);
        let IO_sorted = IO.slice(start_index, end_index);
        let net_sorted = net.slice(start_index, end_index);
        cpu_sorted.sort();
        IO_sorted.sort();
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
                {text: 'CPU(%), 最大值: ' + cpu_sorted.slice(-1)[0].toFixed(2) + '%, 90%Line: ' + cpu_sorted[parseInt(0.9 * cpu_sorted.length)].toFixed(2) + '%, 时间: ' + duration, x: 'center', y: 5, textStyle: {fontSize: 13}},
                {text: '内存(G), 最大值: ' + findMax(mem).toFixed(2) + 'G; JVM(G), 最大值: ' + findMax(jvm).toFixed(2) + 'G, 时间: ' + duration, x: 'center', y: 350, textStyle: {fontSize: 13}},
                {text: 'TCP, TCP最大值: ' + findMax(tcp).toFixed(2) + ', 时间: ' + duration, x: 'center', y: 700, textStyle: {fontSize: 13}}
            ]});
        } else {
            myChart.setOption({
                title: [
                    {text: 'CPU(%), 最大值: ' + cpu_sorted.slice(-1)[0].toFixed(2) + '%, 90%Line: ' + cpu_sorted[parseInt(0.9 * cpu_sorted.length)].toFixed(2) + '%, 时间: ' + duration, x: 'center', y: 5, textStyle: {fontSize: 13}},
                    {text: '内存(G), 最大值: ' + findMax(mem).toFixed(2) + 'G, 时间: ' + duration, x: 'center', y: 350, textStyle: {fontSize: 13}},
                    {text: 'TCP, TCP最大值: ' + findMax(tcp).toFixed(2) + ', 时间: ' + duration, x: 'center', y: 700, textStyle: {fontSize: 13}}
                ]});}

        tables1.rows[1].cells[1].innerHTML = cpu_sorted[parseInt(0.75 * cpu_sorted.length)].toFixed(2);
        tables1.rows[2].cells[1].innerHTML = cpu_sorted[parseInt(0.9 * cpu_sorted.length)].toFixed(2);
        tables1.rows[3].cells[1].innerHTML = cpu_sorted[parseInt(0.95 * cpu_sorted.length)].toFixed(2);
        tables1.rows[4].cells[1].innerHTML = cpu_sorted[parseInt(0.99 * cpu_sorted.length)].toFixed(2);
        tables1.rows[1].cells[4].innerHTML = IO_sorted[parseInt(0.75 * IO_sorted.length)].toFixed(2);
        tables1.rows[2].cells[4].innerHTML = IO_sorted[parseInt(0.9 * IO_sorted.length)].toFixed(2);
        tables1.rows[3].cells[4].innerHTML = IO_sorted[parseInt(0.95 * IO_sorted.length)].toFixed(2);
        tables1.rows[4].cells[4].innerHTML = IO_sorted[parseInt(0.99 * IO_sorted.length)].toFixed(2);
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

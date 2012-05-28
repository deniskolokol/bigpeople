function pad(number, length) {
    var str= '' + number;
    while (str.length < length) {
        str= '0' + str;
    }   
    return str
}


function ms2time(ms) {
    var sec= Math.floor(ms/1000)
    ms= ms % 1000
    t= pad(ms, 3)

    var min= Math.floor(sec/60)
    sec= sec % 60
    t= pad(sec, 2) + ":" + t

    var hr= Math.floor(min/60)
    min= min % 60
    t= pad(min, 2) + ":" + t

    return t
}


function textDurCountStatic(global_table, cnt_id_total, add_val) {
    // count time globally across the table
    var tds= global_table.getElementsByTagName('td');
    var sum= 0;
    for(var i= 0; i < tds.length; i++) {
        if(tds[i].className == 'count') {
            sum += isNaN(tds[i].innerHTML) ? 0 : parseInt(tds[i].innerHTML);
        }
    };
    sum += parseInt(add_val);
    cnt_id_total.value= ms2time(sum)
}


function textDurCountAsType(field, cntfield_ms, cntfield_time) {
    //count number of words and multiply it by average speed of the speech
    var speechSpeedAve= 500; //milliseconds per word
    cnt= 0;
    noLineBreaks= field.value.replace(/\s/g,' ').split(' ');
    for (i= 0; i < noLineBreaks.length; i++) {if (noLineBreaks[i].length > 0) cnt++;}

    // set local fields
    cntfield_ms.value= cnt * speechSpeedAve; // milliseconds
    cntfield_time.value= ms2time(cntfield_ms.value)
}


function textDurCount(field, cntfield_ms, cntfield_time, global_table, cnt_id_total) {
    textDurCountAsType(field, cntfield_ms, cntfield_time);
    textDurCountStatic(global_table, cnt_id_total, cntfield_ms.value);
}
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


function textDurCountStatic(global_table, cnt_id_total, raw_id_total, add_val) {
    // count time globally across the table
    var tds= global_table.getElementsByTagName('td');
    var sum= 0;
    for(var i= 0; i < tds.length; i++) {
        if(tds[i].className == 'count') {
            sum += isNaN(tds[i].innerHTML) ? 0 : parseInt(tds[i].innerHTML);
        }
    };
    sum += parseInt(add_val);
    cnt_id_total.value= ms2time(sum);
    raw_id_total.value= sum;
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


function textDurCount(field, cntfield_ms, cntfield_time, global_table, raw_id_total, cnt_id_total) {
    textDurCountAsType(
        field, // text field
        cntfield_ms, // milliseconds
        cntfield_time // formatted dur
    );
    textDurCountStatic(
        global_table, // table
        cnt_id_total, // table total formatted
        raw_id_total, // table total milliseconds
        cntfield_ms.value // add vaule to total
    );
}

function showHideElt(name, show) {
    var bts= document.getElementsByName(name);
    for(var i= 0; i < bts.length; i++) {
        if(bts[i].type == 'submit') {
            bts[i].style.display= show;
        }
    };
}

function showComplete(target_name, cond_id, floor, ceil) {
    cond= parseInt(document.getElementById(cond_id).value);
    if((cond >= floor) && (cond < ceil)) {
        showHideElt(target_name, 'block');
    } {
        showHideElt(target_name, 'hide');
    };
}

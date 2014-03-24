//cookie操作
function setCookie(name,value,option){
 //用于存储赋值给document.cookie的cookie格式字符串
 var str=name+"="+escape(value);  
 if(option){
  //如果设置了过期时间
  if(option.expireDays){
   var date=new Date();
   var ms=option.expireDays*24*3600*1000;
   date.setTime(date.getTime()+ms);
   str+="; expires="+date.toGMTString();
  } 
  if(option.path)str+="; path="+path;   //设置访问路径
  if(option.domain)str+="; domain"+domain; //设置访问主机
  if(option.secure)str+="; true";    //设置安全性
 }
 document.cookie=str;
}
function getCookie(name){
 var cookieArray=document.cookie.split("; "); //得到分割的cookie名值对
 var cookie=new Object();
 for(var i=0;i<cookieArray.length;i++){
  var arr=cookieArray[i].split("=");    //将名和值分开
  if(arr[0]==name)return unescape(arr[1]); //如果是指定的cookie，则返回它的值
 }
 return "";
}

function deleteCookie(name){
 this.setCookie(name,"",{expireDays:-1}); //将过期时间设置为过去来删除一个cookie
}

// setup the angularjs
function inArray(array,str){
	for(var i in array){
		if(array[i]==str) return true;
	}
	return false;
}
//搜索数组中是否有类似的字符串
function searchArray(array,str){
	for(var i in array){
		if(array[i].indexOf(str)>=0) return true;
	}
	return false;
}
function buildMap(a1,a2){
	var temp = {};
	for(var i in a1){
		var t1 = a1[i];
		temp[t1]={}
		for(var j in a2){
			var t2 = a2[j]
			temp[t1][t2]=false;
		}
	}
	return temp;
}
//
function datetime_to_unix(datetime){
	if( datetime.length < 4  ) return null;
    var tmp_datetime = datetime.replace(/:/g,'-');
    tmp_datetime = tmp_datetime.replace(/ /g,'-');
    var arr = tmp_datetime.split("-");
    if( arr.length  < 6 ){
    	arr[5] = 0
    }
    var now = new Date(Date.UTC(arr[0],arr[1]-1,arr[2],arr[3]-8,arr[4],arr[5]));
    return parseInt(now.getTime()/1000);
}
function unix_to_datetime(unix) {
    var now = new Date(parseInt(unix));
    return now.getFullYear()+"-"+padZero(now.getMonth()+1,2)+"-"+padZero(now.getDate(),2)+" "
    	+padZero(now.getHours(),2)+":"+padZero(now.getMinutes(),2)+":"+padZero(now.getSeconds());
}
function get_now_hms(){
	var now = new Date();
	return padZero(now.getHours(),2)+":"+padZero(now.getMinutes(),2)+":"+padZero(now.getSeconds())
}
function unix_to_datetimeNoSecond(unix) {
    var now = new Date(parseInt(unix));
    return now.getFullYear()+"-"+padZero(now.getMonth()+1,2)+"-"+padZero(now.getDate(),2)+" "
    	+padZero(now.getHours(),2)+":"+padZero(now.getMinutes(),2);
}
function unix_to_datetimeInHighchart(unix) {
    var now = new Date(parseInt(unix));
    return now.getFullYear()+"-"+padZero(now.getMonth()+1,2)+"-"+padZero(now.getDate(),2)+"<br>"
    	+padZero(now.getHours(),2)+":"+padZero(now.getMinutes(),2);
}
function padZero(inStr, length) {
	var str = String(inStr)
    var strLen = str.length;
    return length > strLen ? new Array(length - strLen + 1).join("0") + str : str;
}
function get_now_time(){
	return new Date().valueOf();
}
function get_unix_time(){
	return Math.floor(new Date().valueOf()/1000);
}
//json 格式化
function formatJson(txt,compress/*是否为压缩模式*/){/* 格式化JSON源码(对象转换为JSON文本) */  
    var indentChar = '    ';   
    if(/^\s*$/.test(txt)){   
        alert('数据为空,无法格式化! ');   
        return;   
    }   
    try{var data=eval('('+txt+')');}   
    catch(e){   
        alert('数据源语法错误,格式化失败! 错误信息: '+e.description,'err');   
        return;   
    };   
    var draw=[],last=false,This=this,line=compress?'':'\n',nodeCount=0,maxDepth=0;   
       
    var notify=function(name,value,isLast,indent/*缩进*/,formObj){   
        nodeCount++;/*节点计数*/  
        for (var i=0,tab='';i<indent;i++ )tab+=indentChar;/* 缩进HTML */  
        tab=compress?'':tab;/*压缩模式忽略缩进*/  
        maxDepth=++indent;/*缩进递增并记录*/  
        if(value&&value.constructor==Array){/*处理数组*/  
            draw.push(tab+(formObj?('"'+name+'":'):'')+'['+line);/*缩进'[' 然后换行*/  
            for (var i=0;i<value.length;i++)   
                notify(i,value[i],i==value.length-1,indent,false);   
            draw.push(tab+']'+(isLast?line:(','+line)));/*缩进']'换行,若非尾元素则添加逗号*/  
        }else   if(value&&typeof value=='object'){/*处理对象*/  
                draw.push(tab+(formObj?('"'+name+'":'):'')+'{'+line);/*缩进'{' 然后换行*/  
                var len=0,i=0;   
                for(var key in value)len++;   
                for(var key in value)notify(key,value[key],++i==len,indent,true);   
                draw.push(tab+'}'+(isLast?line:(','+line)));/*缩进'}'换行,若非尾元素则添加逗号*/  
            }else{   
                    if(typeof value=='string')value='"'+value+'"';   
                    draw.push(tab+(formObj?('"'+name+'":'):'')+value+(isLast?'':',')+line);   
            };   
    };   
    var isLast=true,indent=0;   
    notify('',data,isLast,indent,false);   
    return draw.join('');   
}  

function getZooid(host){
	var i = 0;
	for(var index in host){
		i+= host.charCodeAt(index)
	}
	return i;
}
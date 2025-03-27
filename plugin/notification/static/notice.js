function cbi_t_switch(section, container) {
		var o =document.querySelectorAll('div[id^="container."]');
        var s=document.querySelectorAll('li[id^="tab."]');
        // var o=document.getElementById('container.' + container);
		// var sec= document.getElementById('tab.' + section);
        // console.log(s)
        for( let sec of s){
           
            if(sec.id==='tab.' + section){
                sec.className=sec.className.replace(/(^| )cbi-tab-disabled( |$)/, " cbi-tab ");
            }
            else{
                sec.className=sec.className.replace(/(^| )cbi-tab( |$)/, " cbi-tab-disabled ");
            }
        }
        o.forEach(con=>{
                if(con.id==='container.runlog'){
                     con.children[0].children[0].children[0].style.width='100%'
                    con.children[0].children[0].children[1].style.width='100%'
                    fetch('/plugin/notice/logs')
                    .then(response => {
                        if (!response.ok) {
                        throw new Error('Network response was not ok');
                        }
                        return response.json();
                    })
                    .then(data => {
                        console.log(data.message);
                        const mes=data.message
                        const textarea=document.getElementById('log_display');
                        const displayText = mes.map(str => str + '\n').join('');
                        textarea.textContent=displayText
                    })
                    .catch(error => {
                        console.error('There was a problem with the fetch operation:', error);
                    });

                }
                if(con.id==='container.'+container){
                    con.style.display = 'block'
                }
                else
                {
                    con.style.display = 'none'
                }
            }
        )
	return false
}
//这里本应该使用json数据直接提交的，不过因为后端已经适配表单提交的默认格式，所以还是改前端好一点。
function smtpsubmit(e)
{
    e.preventDefault();
    const checkbox = document.getElementById('smtp_enabled');
    if (checkbox.checked) {
        checkbox.value = 'true';
    }
    const form = e.currentTarget;
    const formData = new FormData(form);
    if (!checkbox.checked) {
        formData.append('smtp_enabled', 'false');
    }
    const body = convent_formdata_to_urlsearchparams(formData)
    // const data=Object.fromEntries(formData )
     fetch(form.action, {
        method: 'POST',
        headers:{
            'Content-Type': 'application/x-www-form-urlencoded'
          },
        body: body
    }).then(function (response) {
        return response.json();
    }).then(function (data) {
        // 处理服务器返回的数据，更新页面
        // 更新页面逻辑...
        if(data.message){
            
            const h1_info=document.getElementById('h1-info');
            h1_info.innerHTML = data.message;
        }
    }).catch(function (error) {
        // 处理错误
    });
}
function convent_formdata_to_urlsearchparams(formData)
{
    // 将FormData转换为普通对象
    const formDataObj = {};
    formData.forEach((value, key) => {
    formDataObj[key] = value;
    });

    // 构建URLSearchParams并转换为字符串
    const urlSearchParams = new URLSearchParams(formDataObj);
    const body = urlSearchParams.toString();
    return body
}
function emptysubmit(e)
{
    e.preventDefault();
    const form = e.currentTarget;
    // const data=Object.fromEntries(formData )
     fetch(form.action, {
        method: 'POST',
        headers:{
            'Content-Type': 'application/x-www-form-urlencoded'
          },
    }).then(function (response) {
        return response.json();
    }).then(function (data) {
        // 处理服务器返回的数据，更新页面
        // 更新页面逻辑...
        if(data.message.includes('清空')){
            const textarea=document.getElementById('log_display');
            textarea.textContent='';
        }
        
    }).catch(function (error) {
        // 处理错误
    });
}
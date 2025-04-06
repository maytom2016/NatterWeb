
document.addEventListener('DOMContentLoaded', function() {
            const sidebar = document.querySelector('.sidebar');
            const toggleBtn = document.querySelector('.toggle-btn');
            const rightLayout = document.querySelector('.right-layout');
            toggleBtn.addEventListener('click', function() {
                sidebar.classList.toggle('collapsed');
                if (sidebar.classList.contains('collapsed')) {
                    rightLayout.style.marginLeft = '4rem'; // .sidebar的折叠宽度
                } else {
                    rightLayout.style.marginLeft = '12.5rem'; // .sidebar的展开宽度
                  }
            });
});
function isMobileDevice() {
    return /Mobi|Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}
console.log(isMobileDevice())
function bindevent_Mobinav(){
    const sidebar = document.querySelector('.sidebar');
    const toggleBtn = document.querySelector('.toggle-btn');
    const rightLayout = document.querySelector('.right-layout');

    // 在这里执行所有资源加载完成后的操作
    sidebar.classList.toggle('collapsed');
    if (sidebar.classList.contains('collapsed')) {
        rightLayout.style.marginLeft = '4rem'; // .sidebar的折叠宽度
    } else {
        rightLayout.style.marginLeft = '12.5rem'; // .sidebar的展开宽度
    }
}
//window.addEventListener("load", function() {
//    console.log("整个页面及所有依赖资源加载完成");
//});
function removeScriptsExceptFilename(exceptFilename) {
    var scripts = document.getElementsByTagName('script');
    for (let i = scripts.length - 1; i >= 0; i--) {
        if (scripts[i].src.indexOf(exceptFilename) === -1) {
            scripts[i].remove();
        }
    }
}
function getPathFromURL(url) {
    try {
        let urlObj = new URL(url);
        return urlObj.pathname;
    } catch (error) {
        console.error('Invalid URL:', url);
        return null;
    }
}
function addUniqueLinksToHead(doc,htmlData) {
        // 获取新的link标签
    var newLinks = doc.getElementsByTagName('link');

    // 获取当前页面的所有link标签
    var currentLinks = document.querySelectorAll('link');
    var currentHrefs = Array.from(currentLinks).map(link => link.href);

    // 添加新link标签到当前页面
    for (let i = 0; i < newLinks.length; i++) {
        let href = newLinks[i].href;
//        console.log(href);
//        console.log(i);
        // 检查是否已存在相同的link

        if (!currentHrefs.includes(href)) {
            // 创建新的link元素
            var newLink = document.createElement('link');
            newLink.rel = newLinks[i].rel;
            newLink.href = href;
            newLink.type = newLinks[i].type;
            // 将新link添加到页面尾部
            document.head.appendChild(newLink);

        }
    }
}
function addScriptIfNotExists(src) {
  // 检查head中是否已经有该src的script标签
  url=getPathFromURL(src);
  var existingScript = document.querySelector("script[src='" + url + "']");
  if (!existingScript) {
    // 如果不存在，则创建并添加新的script标签
    var script = document.createElement('script');
    script.src = url;
//    script.onload = function() {
//            console.log('Script loaded and executed!');
//        };
    document.body.appendChild(script);
  }

}
function Ajax_update(url)
{
    var section = document.getElementById('content-layout');
    section.innerHTML = '';
    // 创建Headers对象并添加自定义请求头
    var headers = new Headers();
    headers.append('X-Update-Content', 'true'); // 添加自定义请求头
    // 使用fetch API发起Ajax请求
    fetch(url, {
    method: 'GET',
    headers: headers
    })
    .then(response => response.text()) // 将响应体文本读取出来
    .then(data => {
//    console.log(data);
    // 返回的数据是xx_content.html
    history.pushState({}, '', url);
    // 解析HTML字符串
    var doc = new DOMParser().parseFromString(data, "text/html");
    // 获取所有非<script>和非<link>元素
    const elementsToMove = [...doc.body.children].filter(
        el => !['script', 'link'].includes(el.nodeName.toLowerCase())
    );
    // 将元素转换为HTML字符串
    const elementsHTML = elementsToMove.map(el => el.outerHTML).join('');
    //向section增加所有非<script>和非<link>元素
    section.innerHTML = elementsHTML;


    // 获取页面中所有的script标签
    var scripts = doc.getElementsByTagName('script');

    // 遍历所有script标签
    for (var i = 0; i < scripts.length; i++) {
     //页面标签中的script不应该加入到section中，要单独处理
      var clonedScript = scripts[i].cloneNode(true); // 确保克隆深度足够
//      console.log(scripts[i].src)
      addScriptIfNotExists(scripts[i].src)
    }
    //添加link css标签
    addUniqueLinksToHead(doc,data)
    if (document.querySelector(".task_success")) {
        updateTextColor();
    }
    //        addScriptIfNotExists('/static'+url+'js');
    //        var script = document.createElement('script');
    //        script.src = '/static/manager.js'; // 新脚本的路径
    //        document.head.appendChild(script);

    //        // 如果返回数据包含新的URL，可以更新浏览器的URL
    //        const parsedData = JSON.parse(data);
    //        if (parsedData.redirectUrl) {
    //          history.pushState({}, '', parsedData.redirectUrl);
    //        }
    })
    .catch(error => {
    console.error('Failed to load content:', error);
    });
}
function navclick(e){
    e.preventDefault()
    removeScriptsExceptFilename("ajax.js");
//    let currentPath = window.location.pathname;
      // 获取a标签的href属性，这将作为Ajax请求的URL
    var url = this.getAttribute('href');
//    if(currentPath==url){
//    console.log("原地tp,什么也不做");
//    return false;}
    Ajax_update(url)

}
document.addEventListener('DOMContentLoaded', function() {
  // 为所有类名为'ajax-link'的a标签添加点击事件监听器
  //获取当前路径
var ajaxLinks = document.querySelectorAll('.ajax-link');
for (let i = 0; i < ajaxLinks.length; i++) {
    ajaxLinks[i].onclick = navclick;
}
if(isMobileDevice()){
bindevent_Mobinav()
}
//  document.querySelectorAll('.ajax-link').forEach(function(link) {
//    link.addEventListener('click', function(e) {
//      e.preventDefault(); // 阻止a标签的默认跳转行为



//    });
//  });
});


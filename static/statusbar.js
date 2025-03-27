function updatenattypespan(data) {
    // 选取所有带有data-nat属性的span元素
    var elements = document.querySelectorAll('[data-nat]');
    // 遍历所有元素并更新文本

    elements.forEach(function(element) {
        var natType = element.dataset.nat;
        if (natType === "tcpnat") {
            element.textContent = data.tcpnat;
        }
        else if (natType === "udpnat") {
            element.textContent = data.udpnat;
        }
    });
}
function updatebtn()
{
    // 获取当前页面的URL作为referer
            const referer = window.location.href;

            // 发起向/updatenattype的POST请求，并附带referer
            fetch('/updatenattype', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `referer=${referer}`
            })
            .then(response => response.json())
            .then(data => {
                // 根据返回的数据更新页面或显示提示
//                console.log(typeof data); // 应该输出 "object"
//                console.log(Object.keys(data)); // 应该输出 ["tcpnat", "udpnat"]
                updatenattypespan(data)
            })
            .catch(error => {
                console.error('Error:', error);
            });
}

if (typeof updateBtns  === 'undefined') {
   let updateBtns;
}
updateBtns = document.querySelectorAll('.update-btn');
    // 选择所有update-btn元素
    // 为每个update-btn添加点击事件监听器
    updateBtns.forEach(button => {
        button.addEventListener('click', function(event) {
            updatebtn()
        });
    });
//document.addEventListener('DOMContentLoaded', function() {
//
//});
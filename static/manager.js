if (typeof gbrowData === 'undefined') {
let gbrowData;
}
if (typeof gbrow === 'undefined') {
let gbrow;
}
function openModal() {
  document.getElementById('myModal').style.display = 'block';
  }

function closeModal() {
  document.getElementById('myModal').style.display = 'none';
}
function checkruleok(ruleData,action)
{

  const rulename=ruleData.rulename
  const hostip=ruleData.hostip
  const port=ruleData.port
  let errors=[];
    // 验证规则名称
  if (rulename.length > 12) {
    errors.push('规则名称不能超过12个字符');
  }
  if (rulename.length == 0) {
    errors.push('规则名称未设置');
  }
  // 验证局域网IP
  const ipv4Pattern = /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/;
  if (!ipv4Pattern.test(hostip)) {
    errors.push('主机局域网IP必须是x.x.x.x范围内的有效IPv4地址');
  }

  // 验证端口
  if (port < 1 || port > 65535 || isNaN(port)) {
    errors.push('映射端口必须是1到65535之间的整数');
  }
  if (isDuplicate(ruleData) && action=='new') {

    errors.push('规则已存在，请检查!');
  }
  return errors
}
function adderrorstoweb(errors)
{

    const errorList = document.getElementById('errorList');
    errorList.innerHTML = ''; // 清空已有错误信息
    errors.forEach(error => {
      const li = document.createElement('li');
      li.textContent = error;
      errorList.appendChild(li);
    });
}
function sendFormData() {
  // 检查数据合法性

  let ruleData = {
    rulename: document.getElementById('rulename').value,
    hostip: document.getElementById('hostip').value,
    protocol: document.getElementById('protocol').value,
    port: document.getElementById('port').value,
    upnp: document.getElementById('upnp').checked,
    enabled: document.getElementById('ruleenabled').checked
};
//const inputs = {
//    rulename: document.getElementById('rulename'),
//    hostip: document.getElementById('hostip'),
//    protocol:document.getElementById('protocol'),
//    port: document.getElementById('port'),
//    upnp: document.getElementById('upnp'),
//    ruleenabled: document.getElementById('ruleenabled'),
//};
//  const { rulename, hostip, protocol,port,upnp:upnp, ruleenabled: enabled } = inputs;
//  let ruleData = {
//    rulename: rulename.value,
//    hostip: hostip.value,
//    protocol:protocol.value,
//    port: port.value,
//    upnp: upnp.checked,
//    enabled: enabled.checked,
//};
  const action=getButtonDataClick('submitbutton')

//console.log(ruleData)
//console.log(hostip)
//console.log(port)

    const errors = checkruleok(ruleData,action)
    if (errors.length > 0) {
        adderrorstoweb(errors)
        document.getElementById('errorMessages').style.display = 'block';
        return;
        }
    if(action=='new'){
        // 数据验证通过，可以继续提交表单
        document.getElementById('errorMessages').style.display = 'none';
        Postaddrule(ruleData)
    }
    else if(action=='edit')
    {
        if(isNothingchange(ruleData,gbrowData)){
            //啥也没改，直接关闭对话框，不做提示
            closeModal()
            return
        }
        document.getElementById('errorMessages').style.display = 'none';
        ruleData.id=gbrow.id
        Posteditrule(ruleData)
        closeModal()
    }
}
function addButtonDataClick(buttonId, value) {
  const button = document.getElementById(buttonId);
  if (button) {
    button.dataset.click = value;
  }
}
function getButtonDataClick(buttonId) {
  const button = document.getElementById(buttonId);
  if (button) {
    return button.dataset.click;
  }
  return null; // 或者你可以选择返回一个默认值
}

function Posteditrule(ruleData)
{
// 发送请求到后端
fetch('/edit_rule/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(ruleData)
})
.then(response => response.json())
.then(data => {
    console.log('Success:', data);
    changerowtable(ruleData)
})
.catch((error) => {
    console.error('Error:', error);
});

}
function changerowtable(ruleData)
{
   const rowid=ruleData.id
   delete ruleData.id
   updateRowData(rowid, ruleData)
}
function updateRowData(rowId, newData) {
    // 确保newData是一个对象，包含要更新的列名和值
    // 例如：{ rulename: 'newName', hostip: 'newIP', port: 'newPort', enabled: true }
    const row = document.getElementById(rowId);

    if (row) {
        // 更新每个单元格的数据

        Object.entries(newData).forEach(([key, value]) => {
            let td;
            switch (key) {
                case 'rulename':
                    td = row.querySelector('td:nth-child(1)');
                    break;
                case 'hostip':
                    td = row.querySelector('td:nth-child(2)');
                    break;
                case 'protocol':
                    td = row.querySelector('td:nth-child(3)');
                    break;
                case 'port':
                    td = row.querySelector('td:nth-child(4)');
                    break;
                case 'upnp':
                    td = row.querySelector('td:nth-child(5) input[type="checkbox"]');
                    value = value ? true : false; // 确保value是布尔值
                    break;
                case 'enabled':
                    td = row.querySelector('td:nth-child(6) input[type="checkbox"]');
                    value = value ? true : false; // 确保value是布尔值
                    break;
                default:
                    console.log(`Unknown key: ${key}`);
                    return;
            }
            if (td) {
                if (td.tagName.toLowerCase() === 'input') {
                    td.checked = value;
                } else {
                    td.textContent = value;
                }
            }
        });
    } else {
        console.log(`Row with ID ${rowId} not found.`);
    }
}
function Postaddrule(ruleData)
{
    console.log('新增数据',ruleData)
   fetch('/add_rule/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(ruleData)
  })
  .then(response => {
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    return response.json();
  })
  .then(data => {
    console.log('uuid:', data.rule_id);
    addRowToTable(data.rule_id,ruleData); // 假设这是你定义的函数，用来在表格中添加新行
    closeModal(); // 确保函数调用后面有括号
  })
  .catch(error => {
    console.error('Error:', error);
  });
}
function isDuplicate(data) {
//    return false;检查服务器规则重复能力
    let rows = document.querySelectorAll('.table tbody tr');
      for (let row of rows) {
        let ip = row.children[1].textContent;
        let port = row.children[3].textContent;
        let protocol=row.children[2].textContent;
//        let checked=row.children[3].children[0].checked;
//        console.log(checked)
       console.log( protocol)
       console.log( data.protocol)
        if (ip === data.hostip && port === data.port.toString() ) {
            if(protocol==data.protocol){
                return true;
            }
            if(protocol=='both' || data.protocol=='both')
            {
                return true;
            }
        }
    }
    return false;
}
function isNothingchange(ruleData,rowData)
{
    //ruleData是对话框内的数据 row是选择行数据
    let data=ruleData
    delete data.id
    const modaldata = Object.values(data);

//    console.log("ruledata",ruleData)
//    console.log("row",rowData)
    if (modaldata.length !== rowData.length) return false;
    for (let i = 0; i < modaldata.length; i++) {
        if (modaldata[i] !== rowData[i]) return false;
    }
    return true;
}
//function uuidv4() {
//    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
//        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
//        return v.toString(16);
//    });
//}
function addRowToTable(rule_id,data) { // 假定data是一个含有所有信息的对象
    let newRow = document.createElement('tr');
      newRow.id=rule_id;
//    newRow.id = uuidv4();
    newRow.innerHTML = `
        <td>${data.rulename}</td>
        <td>${data.hostip}</td>
        <td>${data.protocol}</td>
        <td>${data.port}</td>
        <td><input type="checkbox" ${data.upnp ? 'checked' : ''}></td>
        <td><input type="checkbox" ${data.enabled ? 'checked' : ''}></td>
        <td>
            <div class="button-div">
                <div class="editbutton-container">
                    <button type="button" class="buttondouble" data-action="edit">
                        修改
                    </button>
                    <button type="button" class="buttondouble" data-action="delete">
                        删除
                    </button>
                </div>
            </div>
        </td>
    `;
    // 获取新创建的按钮
    const editButton = newRow.querySelector('.buttondouble[data-action="edit"]');
    const deleteButton = newRow.querySelector('.buttondouble[data-action="delete"]');
    const cells = newRow.querySelectorAll('td');
        const rowData = [];
        cells.forEach(function(cell) {
                // 将每个单元格的内容添加到数组中
                const inputElement = cell.querySelector('input');
                if (inputElement) {
                // 如果存在input元素
                    //console.log(inputElement.checked);
                    rowData.push(inputElement.checked);
                }
                if(cell.textContent!="" && !cell.querySelector('button'))
                {
                    //console.log(cell.textContent.trim());
                    rowData.push(cell.textContent.trim());
                }
        });
    gbrowData=rowData
    gbrow=newRow

    // 添加点击事件
    editButton.addEventListener('click', function(event) {
        editData(gbrowData);
    });

    deleteButton.addEventListener('click', function(event) {
        deleteData(gbrow,gbrowData);
    });

    document.querySelector('.table tbody').appendChild(newRow);
}

// 获取按钮元素
if (typeof addbutton  === 'undefined') {
   let addbutton;
}
if (typeof canclebutton  === 'undefined') {
   let canclebutton;
}
if (typeof submitButton  === 'undefined') {
   let submitButton;
}
if (typeof editbuttons  === 'undefined') {
   let editbuttons;
}
addbutton = document.getElementById('addbutton');
console.log("manager.js")
// 给增加按钮添加点击事件监听器
addbutton.addEventListener('click', () => addData());
// 给取消按钮添加点击事件监听器
canclebutton=document.getElementById('canclebutton');
canclebutton.addEventListener('click', closeModal);

submitButton = document.getElementById('submitbutton');
 // 给提交按钮添加点击事件监听器
submitButton.addEventListener('click', sendFormData);

// 给运行添加点击事件监听器
var runButton = document.getElementById('runbutton');
            runButton.addEventListener('click', function() {
                fetch('/run', {
                    method: 'POST', // 或者 'POST'
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({}), // 可以在这里添加需要发送的数据
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    var remain=document.getElementById('remain-info');
                    remain.innerHTML = data.message;
                    console.log('Success:', data);
                })
                .catch((error) => {
                    console.error('Error:', error);
                });
            });
//给停止按钮增加点击事件监听器
var stopButton = document.getElementById('stopbutton');
stopButton.addEventListener('click', function() {
                fetch('/stop_all', {
                    method: 'POST', // 或者 'POST'
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({}), // 可以在这里添加需要发送的数据
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    var remain=document.getElementById('remain-info');
                    remain.innerHTML = data.message;
                    console.log('Success:', data);
                })
                .catch((error) => {
                    console.error('Error:', error);
                });
            });
// 获取编辑修改按钮
editbuttons = document.querySelectorAll('[data-action]');

// 为每行按钮添加点击事件监听器
editbuttons.forEach(button => {
    button.addEventListener('click', function(event) {
        // 阻止默认行为
        event.preventDefault();
        const row = this.closest('tr');
        // 从行中提取数据
        const cells = row.querySelectorAll('td');
        const rowData = [];
        cells.forEach(function(cell) {
                // 将每个单元格的内容添加到数组中
                const inputElement = cell.querySelector('input');
                if (inputElement) {
                // 如果存在input元素
                    //console.log(inputElement.checked);
                    rowData.push(inputElement.checked);
                }
                if(cell.textContent!="" && !cell.querySelector('button'))
                {
                    //console.log(cell.textContent.trim());
                    rowData.push(cell.textContent.trim());
                }


            });
           console.log(rowData);
           gbrowData=rowData
           gbrow=row
           //js这个精神病设计不让我容易向点击事件内传参，直接不传了，赋值全局变量
        // 根据按钮的动作执行相应操作
        switch (this.getAttribute('data-action')) {
            case 'edit':
                //console.log('编辑数据:', rowData);
                // 调用编辑数据的函数，并传入rowData
                editData(rowData);
                break;
            case 'delete':
                deleteData(row,rowData);
                break;
            default:
                console.log('未知操作');
        }
    });
});
function addData()
{
    openModal()
    addButtonDataClick('submitbutton','new')
    console.log(getButtonDataClick('submitbutton'))
}


function editData(rowData) {
    openModal()
    addButtonDataClick('submitbutton','edit')
    // 获取id为'rulename'的<input>元素
    var ie = document.getElementById('rulename');
    // 向<input>元素中写入内容
    ie.value = rowData[0];
    ie = document.getElementById('hostip');
    ie.value = rowData[1];
    ie = document.getElementById('protocol');
    ie.value = rowData[2];
    ie = document.getElementById('port');
    ie.value =rowData[3];
    ie = document.getElementById('upnp');
    ie.checked=rowData[4];
    ie = document.getElementById('ruleenabled');
    ie.checked=rowData[5];
}

function deleteData(row,data) {
console.log('删除数据:', data);
                // 调用删除数据的函数，并传入rowData
                fetch('/delete_rule', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ id: row.id }) // 将id作为JSON发送
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json(); // 解析服务器返回的JSON
            })
            .then(data => {
                console.log(data); // 在控制台打印服务器返回的数据
                row.remove(); // 从DOM中删除当前tr元素
            })
            .catch(error => {
                console.error('There was a problem with the fetch operation:', error);
            });
    // 实现删除逻辑
}




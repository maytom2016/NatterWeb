function updateTextColor() {
    var elementsWithClass = document.querySelectorAll(".task_success");

elementsWithClass.forEach(function(element) {
    // 在这里对每个元素执行操作，例如打印元素的内容
    // 根据内容判断颜色，这里仅为示例
    var content = element.innerText;
    if (content === "成功连接") {
        element.style.color = "green";
    } else if (content === "未连接") {
        element.style.color = "red";
    } else {
        element.style.color = "black";
    }
   });
}

document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.copy-btn').forEach(button => {
    button.addEventListener('click', () => {
      const textToCopy = button.previousElementSibling;
      if (textToCopy) {
        navigator.clipboard.writeText(textToCopy.textContent).then(() => {
          console.log('Text copied to clipboard');
        }, err => {
          console.error('Failed to copy text: ', err);
        });
      } else {
        console.error('No previous element to copy text from');
      }
    });
  });
});

window.onload = updateTextColor;


function formatTimeElapsed(pastTime) {
  // 1. 解析输入时间（支持Date对象或ISO字符串）
  const past = new Date(pastTime);
  if (isNaN(past.getTime())) {
      throw new Error("Invalid time format. Expected Date object or ISO 8601 string.");
  }

  // 2. 计算时间差（毫秒）
  const now = new Date();
  let diffMs = now - past;

  // 3. 处理未来时间（返回全零）
  if (diffMs < 0) {
      return "00:00:00";
  }

  // 4. 转换为时、分、秒
  const diffSec = Math.floor(diffMs / 1000);
  const hours = Math.floor(diffSec / 3600);
  const minutes = Math.floor((diffSec % 3600) / 60);
  const seconds = diffSec % 60;

  // 5. 格式化为两位数（补零）
  const pad = num => num.toString().padStart(2, '0');
  return `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;
}

function updaterunningtime(task_id)
{
  const create_time=document.getElementById(task_id+'_runtime').getAttribute('data-time');
  // console.log(create_time)
  const timeElement=document.getElementById(task_id+'_runtime');
  timeElement.textContent = "已运行时间:"+formatTimeElapsed(create_time);
}

document.querySelectorAll('.expand-btn').forEach(btn => {
  btn.addEventListener('click', function() {
      const targetId = this.getAttribute('data-target');
      const detailRow = document.getElementById(targetId);
      const isExpanded = detailRow.classList.contains('expanded');
      
      if (isExpanded) {
          // 收起动画
          detailRow.classList.remove('expanded');
          detailRow.querySelector('.detail-content').style.opacity = '0';
          detailRow.querySelector('.detail-content').style.transform = 'translateY(-20px)';
          
          // 动画结束后完全隐藏
          setTimeout(() => {
              detailRow.style.display = 'none';
          }, 300); // 与CSS过渡时间一致
          clearInterval(detailRow.dataset.timerId)
          delete detailRow.dataset.timerId 
          detailRow.dataset.timerId = null;
          

      } else {
          // 展开动画
          detailRow.style.display = 'table-row';
          requestAnimationFrame(() => {
              detailRow.classList.add('expanded');
              detailRow.querySelector('.detail-content').style.opacity = '1';
              detailRow.querySelector('.detail-content').style.transform = 'translateY(0)';
          });
          //计时器
          const timerId = setInterval(() => {
           
            let task_id = targetId.replace(/-detail$/, '');
            // console.log(newStr)
            updaterunningtime(task_id)
            // 获取最新日志并更新textarea
          }, 1000);
          detailRow.dataset.timerId = timerId;
          
      }
      
      this.textContent = isExpanded ? '+' : '-';
  });
});


// document.addEventListener('DOMContentLoaded', function() {
//   // 获取所有展开按钮
//   const expandButtons = document.querySelectorAll('.expand-btn');
  
//   // 为每个按钮添加点击事件
//   expandButtons.forEach(button => {
//       button.addEventListener('click', function() {
//           const targetId = this.getAttribute('data-target');
//           const detailRow = document.getElementById(targetId);
//           const isExpanded = this.getAttribute('aria-expanded') === 'true';
          
//           // 切换状态
//           this.setAttribute('aria-expanded', !isExpanded);
//           detailRow.style.display = isExpanded ? 'none' : 'table-row';
//           this.textContent = isExpanded ? '+' : '-';
          
//           // 可选：关闭其他已展开的行
//           closeOtherExpandedRows(this);
//       });
//   });
  
//   // 关闭其他已展开的行（可选）
//   function closeOtherExpandedRows(currentButton) {
//       const allButtons = document.querySelectorAll('.expand-btn');
//       allButtons.forEach(btn => {
//           if (btn !== currentButton && btn.getAttribute('aria-expanded') === 'true') {
//               const targetId = btn.getAttribute('data-target');
//               document.getElementById(targetId).style.display = 'none';
//               btn.setAttribute('aria-expanded', 'false');
//               btn.textContent = '+';
//           }
//       });
//   }
// });


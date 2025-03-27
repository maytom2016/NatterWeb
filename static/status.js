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
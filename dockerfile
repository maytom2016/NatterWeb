FROM python:3.11-alpine3.21 as builder
WORKDIR /NatterWeb
COPY ./ /NatterWeb
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
EXPOSE 18650
CMD ["python", "app.py"]

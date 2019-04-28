FROM python:2.7

COPY . /Athena

WORKDIR /Athena

RUN pip install -r requirements.txt -i http://pypi.douban.com/simple/ --trusted-host=pypi.douban.com

EXPOSE 8080

CMD ["./start.sh"]

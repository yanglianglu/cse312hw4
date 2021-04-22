FROM python:3.8.2
ENV HOME /root
WORKDIR /root
COPY . .
RUN pip freeze > requirements.txt
RUN pip install -r requirements.txt
RUN pip install pymongo
EXPOSE 8000
ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.2.1/wait /wait
RUN chmod +x /wait
CMD /wait && python app.py

# FROM python:3.8
# ENV HOME /root
# WORKDIR /root
# COPY . .
# EXPOSE 8081

# CMD python3 app.py

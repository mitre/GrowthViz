FROM jupyter/minimal-notebook

MAINTAINER rscalfani@mitre.org

WORKDIR /usr/src/app

RUN pip install pandas
RUN pip install matplotlib
RUN pip install ipywidgets
RUN pip install seaborn
RUN pip install qgrid

COPY . ./

EXPOSE 8888

CMD jupyter notebook
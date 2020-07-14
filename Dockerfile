FROM jupyter/minimal-notebook

MAINTAINER rscalfani@mitre.org

WORKDIR /usr/src/app

RUN pip install pandas
RUN pip install matplotlib
RUN pip install ipywidgets
RUN pip install seaborn
RUN pip install qgrid

COPY . ./

RUN mkdir growthviz-data/output/

EXPOSE 8888

RUN jupyter nbextension enable --py --sys-prefix qgrid

CMD jupyter notebook
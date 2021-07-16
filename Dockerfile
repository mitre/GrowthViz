FROM jupyter/scipy-notebook

LABEL maintainer="Robi Scalfani <rscalfani@mitre.org>"

COPY LICENSE /LICENSE
COPY README.md /README.md

# Switch to root; minimal-notebook switches away, so we have to switch back
# https://github.com/jupyter/docker-stacks/blob/master/minimal-notebook/Dockerfile
USER root

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt
RUN python check_setup.py

RUN chown -R jovyan /app
RUN mkdir /app/.local
RUN chmod -R ugo+rwx /app

RUN mkdir -p /home/jovyan/.cache/matplotlib
RUN chmod -R ugo+rwx /home/jovyan
RUN chmod -R ugo+rwx /home/jovyan/.cache
RUN chmod -R ugo+rwx /home/jovyan/.cache/matplotlib

EXPOSE 8080

# Switch back to regular user
USER jovyan
ENV HOME /app
RUN jupyter nbextension enable --py --sys-prefix qgrid

CMD jupyter notebook --port=8080 --ip='*' --NotebookApp.token='' --NotebookApp.password=''

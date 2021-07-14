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

EXPOSE 8080

RUN jupyter nbextension enable --py --sys-prefix qgrid

# Switch back to regular user
USER jovyan
ENV HOME /app

CMD jupyter notebook --port=8080

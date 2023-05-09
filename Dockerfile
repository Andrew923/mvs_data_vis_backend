FROM theairlab/dsta_ngc_x86:22.08_10_opencv_override

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY dsta_mvs dsta_mvs
COPY dsta_mvs_lightning dsta_mvs_lightning

COPY app.py app.py
COPY gunicorn.sh gunicorn.sh


ENV port=3000
EXPOSE 3000

RUN chmod +x gunicorn.sh
ENTRYPOINT ["./gunicorn.sh"]

#############################################
# Multistage but lots of dependency issues rn
#############################################

# FROM theairlab/dsta_ngc_x86:22.08_10_opencv_override as build

# WORKDIR /app

# RUN pip install --upgrade pip
# RUN pip freeze > reqs.txt 
# # RUN sed -i 's/@ file:\/\/\/.*//g' reqs.txt
# # RUN sed -i '/@/d' reqs.txt

# COPY requirements.txt requirements.txt
# RUN cat reqs.txt requirements.txt > allreqs.txt && \
#     rm reqs.txt && rm requirements.txt

# COPY . .

# FROM continuumio/anaconda3 as main

# COPY --from=build /app /app
# WORKDIR /app

# RUN conda install mamba -c conda-forge && \
#     mamba install -c conda-forge --file allreqs.txt

# ENTRYPOINT ["/bin/bash"]
# ENTRYPOINT ["./gunicorn.sh"]

#######
# Conda
#######

# FROM theairlab/dsta_ngc_x86:22.08_10_opencv_override as build

# WORKDIR /app

# # COPY requirements.txt requirements.txt
# # RUN conda install --file requirements.txt

# RUN conda update --all && \
#     conda install -c conda-forge conda-pack && \
#     conda pack --ignore-missing-files -o env.tar && \
#     mkdir /venv && tar xf env.tar -C /venv && \
#     rm env.tar

# COPY . .

# FROM continuumio/anaconda3 as main

# COPY --from=build /app /app
# COPY --from=build /venv /venv

# RUN /venv/bin/conda-unpack
# RUN pip install -r requirements.txt

# ENTRYPOINT ["/bin/bash"]
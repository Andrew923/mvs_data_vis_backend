FROM theairlab/dsta_ngc_x86:22.08_10_opencv_override

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

ENV port=3000

EXPOSE 3000

# ENTRYPOINT ["./gunicorn.sh"]
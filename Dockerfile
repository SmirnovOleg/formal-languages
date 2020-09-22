FROM graphblas/pygraphblas-minimal:latest

RUN mkdir /formal_languages
WORKDIR /formal_languages

COPY . /formal_languages

RUN pip3 install -r requirements.txt

CMD ["/bin/python3", "-m", "pytest", "--ignore-glob='*big_data.py'"]
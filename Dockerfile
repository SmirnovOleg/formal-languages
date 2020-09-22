FROM graphblas/pygraphblas-minimal:latest

RUN mkdir /formal_languages
WORKDIR /formal_languages

COPY . /formal_languages

RUN pip3 install -r requirements.txt
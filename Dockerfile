FROM graphblas/pygraphblas-minimal:latest

RUN apt-get update && apt-get install -y default-jre curl

RUN cd /usr/local/lib && curl -O https://www.antlr.org/download/antlr-4.9-complete.jar
ENV CLASSPATH=".:/usr/local/lib/antlr-4.9-complete.jar:$CLASSPATH"

RUN mkdir /formal_languages
COPY . /formal_languages
WORKDIR /formal_languages

RUN pip3 install -r requirements.txt
RUN java -jar /usr/local/lib/antlr-4.9-complete.jar -Dlanguage=Python3 antlr/QueryLanguageGrammar.g4

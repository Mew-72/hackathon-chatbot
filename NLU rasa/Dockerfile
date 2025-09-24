FROM python:3.8

WORKDIR /app

COPY ./ /app

RUN pip install -r requirements.txt

CMD ["rasa", "run", "-m", "models", "--enable-api", "--cors", "*", "--debug"]

FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    numpy==1.26.4 \
    pandas==2.2.2 \
    matplotlib==3.8.4

COPY . .

CMD ["sh", "-c", "python verify.py && python run_simulation.py"]
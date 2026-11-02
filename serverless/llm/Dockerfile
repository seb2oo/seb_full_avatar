FROM pytorch/pytorch:2.8.0-cuda12.8-cudnn9-runtime

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY handler.py .
COPY local_llm.py .
COPY human_ai_layer15_v2_vector.pt .

CMD ["python", "handler.py"]
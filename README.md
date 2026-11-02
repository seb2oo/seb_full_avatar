---
title: Seb Full Avatar
emoji: 💬
colorFrom: yellow
colorTo: purple
sdk: gradio
sdk_version: 6.5.1
app_file: app.py
pinned: false
hf_oauth: true
hf_oauth_scopes:
- inference-api
python_version: "3.12.12"
---

An example chatbot using [Gradio](https://gradio.app), [`huggingface_hub`](https://huggingface.co/docs/huggingface_hub/v0.22.2/en/index), and the [Hugging Face Inference API](https://huggingface.co/docs/api-inference/index).

<!-- below if not workin and make issue.. -->
<!-- preload_from_hub:
  - meta-llama/Llama-3.1-8B-Instruct -->


## 1. Project Overview

Seb Full Avatar is a personal AI project focused on building a multimodal conversational digital avatar capable of interacting with users through text, voice and video.

The project combines a customized Large Language Model (LLM), a Retrieval-Augmented Generation (RAG) system, voice synthesis and AI-driven facial animation into a unified application.

The avatar is designed to reproduce my communication style, knowledge and personality, using custom fine-tuning, a personality steering vector and a personal knowledge base.

The entire system has been designed, developed and integrated independently, from model customization to infrastructure deployment and frontend implementation.

## 2. Live Demo
**Try the application:**  
https://huggingface.co/spaces/seb2oo/seb_full_avatar

<p align="center">
  <img src="docs/avatar_demo.gif" width="480" alt="Live avatar demonstration">
</p>


## 3. Screenshots
### Full Avatar Interface
<p align="center">
  <img src="docs/screenshot_full_avatar.png" width="480" alt="Full Avatar Interface">
</p>


### Text Chat Interface
<p align="center">
  <img src="docs/screenshot_text_chat.png" width="480" alt="Text Chat Interface">
</p>

## 4. System Architecture

The application is built around three independent AI inference services, deployed on RunPod Serverless and orchestrated by a Gradio application hosted on Hugging Face Spaces.

Each service runs independently and is activated on demand.

![System Architecture](docs/architecture.png)


1. **LLM:** Processes the user's message, retrieves relevant personal knowledge and generates a response.
2. **TTS:** Converts the generated response into speech using a cloned voice.
3. **Video Generation:** Generates synchronized facial animation based on the synthesized audio.
4. **Frontend:** Delivers the generated text, audio and video to the user.

A text-only interaction mode is also available.

## 5. AI Components

### 5.1 Large Language Model & RAG

- Base model: Meta Llama 3.1 8B Instruct.
- Custom LoRA fine-tuning using personal examples.
- Personality steering vector to influence the model's conversational behavior.
- Hybrid RAG architecture combining:
  - ChromaDB vector similarity search.
  - BM25 lexical retrieval.
- Multilingual text processing and retrieval.
- Context-aware response generation.
- Conversation history and session management.
- Supported conversational languages: French, English, Spanish and German.

### 5.2 Text-to-Speech

- Custom voice cloning.
- Support for four languages.
- Expressive speech generation using audio tags.
- Modified and customized open-source implementation.

### 5.3 AI Video Generation

- Model: MuseTalk 1.5.
- Audio-driven facial animation and lip synchronization.
- Supporting models for face detection, pose estimation and facial processing.
- Modified and customized open-source implementation.

## 6. Infrastructure & Deployment

The system uses a hybrid deployment architecture.

### Hugging Face Spaces

Hosts the Gradio application and manages the user interface, application logic, session handling and communication with the inference services.

### RunPod Serverless

Hosts the three independent GPU inference services:

- LLM inference.
- Text-to-Speech generation.
- AI video generation.

Each service uses a custom Docker image and inference handler.

### Storage & Media Processing

- Amazon S3 for generated audio and video storage.
- FFmpeg for audio/video processing.
- HTTP Range requests for media streaming.
- Custom frontend JavaScript for audio/video synchronization and playback.

## 7. Repository Structure

The repository contains the application source code, serverless deployment configurations and supporting resources.

| File / Directory | Description |
|---|---|
| `app.py` | Application entry point and application routing. |
| `chat.py` | Main conversational engine, LLM orchestration and RAG pipeline. |
| `log_retrieve.py` | Log retrieval and inspection utilities. |
| `avatar_tag_pattern.py` | Avatar expression tags and associated processing. |
| `serverless/` | Docker configurations and inference handlers for the three GPU services. |
| `js/` | Custom JavaScript for frontend interactions and audio/video synchronization. |
| `data/` | Encrypted personal knowledge base. |
| `fine_tuning/` | Encrypted fine-tuning examples. |
| `*.txt` | NLP dictionaries used for text correction and preprocessing. |

### Code Organization

The main conversational engine is intentionally maintained in a single Python file (`chat.py`), organized into logical sections to facilitate navigation and development.

For navigation instructions, see the beginning of `chat.py`.

## 8. Getting Started

The application is primarily intended as a portfolio and demonstration project.

The complete deployment depends on external RunPod Serverless endpoints, Hugging Face configuration and environment secrets.

Running the application independently therefore requires configuring these external services and credentials.

### Main requirements

- Python 3.12
- Gradio 6.5.1
- Hugging Face account and Space configuration
- RunPod Serverless endpoints
- Amazon S3 storage configuration

Python dependencies are listed in `requirements.txt`.

## 9. Demo Instructions

The live demonstration is available through the Hugging Face Space.

### Starting the application

The following guide explains how to start the serverless services and use the application.

![Application Startup Guide](docs/startup.png)

### Starting the application

The RunPod Serverless services automatically scale down after periods of inactivity.

Consequently, the first interaction after inactivity may require additional startup time while the GPU services initialize and load their models.

### Available interaction modes

- **Text:** Text-based conversational interaction.
- **Full Avatar:** Complete interaction pipeline with generated speech and synchronized video.

### Performance considerations

The LLM, TTS and video generation services operate independently.

Although individual media generation can run faster than real-time under certain conditions, the complete pipeline currently processes the stages sequentially. Total response time therefore depends on the combined execution time of the three services.

## 10. Technical Stack

**Programming & Application Development**
- Python
- JavaScript
- FastAPI
- Gradio
- Flask
- Uvicorn

**Artificial Intelligence & Machine Learning**
- PyTorch
- Hugging Face Transformers
- PEFT / LoRA
- LangChain
- ChromaDB
- BM25
- Fish Speech
- MuseTalk

**Infrastructure & Deployment**
- RunPod Serverless
- Docker
- Hugging Face Spaces
- Amazon S3
- Git / GitHub

**Audio & Video Processing**
- FFmpeg
- HTTP Range streaming
- Custom JavaScript synchronization

## 11. Known Limitations & Future Improvements

The current implementation is fully functional as a demonstration system, but several areas could be further optimized.

### Current limitations

- The LLM, TTS and video generation stages currently operate sequentially.
- End-to-end response latency accumulates across the three inference services.
- Concurrent requests share the available inference resources and may be queued depending on worker availability.
- Serverless cold starts introduce additional latency after periods of inactivity.

### Potential improvements

- Streaming LLM output directly into the TTS service.
- Incremental audio generation and video synchronization.
- Overlapping inference stages to reduce total response latency.
- WebSocket or WebRTC-based real-time media delivery.
- Improved concurrency management and request scheduling.

---

**Project developed independently by Sébastien Wermuth.**
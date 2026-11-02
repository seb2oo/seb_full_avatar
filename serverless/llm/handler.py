import os
from pathlib import Path
import shutil
import torch
import runpod

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig
)

from peft import PeftModel

from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage
)

from local_llm import LocalLlamaChatLLM


MODEL_ID = "meta-llama/Llama-3.1-8B-Instruct"
LORA_ID = "seb2oo/my_lora"

STEERING_VECTOR_PATH = (
    "human_ai_layer15_v2_vector.pt"
)



# ============================================================
# HUGGING FACE TOKEN
# ============================================================

HF_TOKEN = os.environ["HF_TOKEN"] 

# ============================================================
# QUANTIFIED ?
# ============================================================

use_quantified = True

# ============================================================
# FIND CACHED MODEL
# ============================================================

def find_cached_model(model_id):

    org, name = model_id.split("/", 1)

    cache_dir = Path(
        "/runpod-volume/huggingface-cache/hub"
    )

    model_dir = cache_dir / (
        f"models--{org}--{name}"
    )

    snapshots_dir = model_dir / "snapshots"

    snapshots = list(snapshots_dir.iterdir())

    if not snapshots:
        raise RuntimeError(
            f"No cached snapshot found for {model_id}"
        )

    return str(snapshots[0])


print("Looking for cached model...")

MODEL_PATH = find_cached_model(MODEL_ID)

print("Cached model found:")
print(MODEL_PATH)



# ============================================================
# CLEANUP MUSETALK OUTPUT DIRECTORY --> I give the endpoint the volume acces just for that
# ============================================================

MUSETALK_DIR = "/runpod-volume/musetalk"

print("\n" + "=" * 70, flush=True)
print("MUSETALK CLEANUP [START]", flush=True)
print(f"Directory: {MUSETALK_DIR}", flush=True)

if os.path.isdir(MUSETALK_DIR):

    deleted_count = 0
    errors = 0

    for name in os.listdir(MUSETALK_DIR):
        path = os.path.join(MUSETALK_DIR, name)

        try:
            # Supprimer les liens symboliques sans suivre leur cible
            if os.path.islink(path) or not os.path.isdir(path):
                os.unlink(path)
            else:
                shutil.rmtree(path)

            deleted_count += 1
            print(f"[DELETED] {name}", flush=True)

        except OSError as e:
            errors += 1
            print(f"[ERROR] {path}: {e}", flush=True)

    print(f"Entries deleted: {deleted_count}", flush=True)
    print(f"Errors: {errors}", flush=True)

else:
    print(
        f"[WARNING] Directory does not exist: {MUSETALK_DIR}",
        flush=True,
    )

print("MUSETALK CLEANUP [END]", flush=True)
print("=" * 70 + "\n", flush=True)



# ============================================================
# QUANTIZATION
# ============================================================
if use_quantified:
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True
    )


# ============================================================
# TOKENIZER
# ============================================================

print("Loading tokenizer...")

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_PATH
)


# ============================================================
# BASE MODEL
# ============================================================

if use_quantified :
    print("Loading 4-bit base model...")
    base_model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        quantization_config=bnb_config,
        device_map="auto"
    )
else:
    print("Loading non-quantized BF16 model...")
    base_model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.bfloat16,
    device_map="auto"
)

# ================================================================================================================
# MODEL VERIFICATION START
# ================================================================================================================

print("\n" + "=" * 80)
print("MODEL VERIFICATION")
print("=" * 80)

print(f"Model path       : {MODEL_PATH}")
print(f"Quantized mode   : {use_quantified}")

# ============================================================
# BASIC MODEL INFO
# ============================================================

total_params = sum(
    p.numel()
    for p in base_model.parameters()
)

print(f"\nTotal parameters : {total_params:,}")
print(f"Parameters (B)   : {total_params / 1e9:.2f}B")

# ============================================================
# PARAMETER DTYPES
# ============================================================

print("\nParameter dtypes:")

dtype_stats = {}

for param in base_model.parameters():

    dtype = str(param.dtype)

    if dtype not in dtype_stats:
        dtype_stats[dtype] = {
            "params": 0,
            "tensors": 0
        }

    dtype_stats[dtype]["params"] += param.numel()
    dtype_stats[dtype]["tensors"] += 1


for dtype, stats in dtype_stats.items():

    percentage = (
        stats["params"] / total_params * 100
    )

    print(
        f"  {dtype:<20} "
        f"{stats['params']:>15,} params "
        f"({percentage:6.2f}%) "
        f"{stats['tensors']} tensors"
    )

# ============================================================
# QUANTIZATION CHECK
# ============================================================

if use_quantified:

    print("\n" + "-" * 80)
    print("4-BIT QUANTIZATION CHECK")
    print("-" * 80)

    try:
        import bitsandbytes as bnb

        print(f"bitsandbytes version: {bnb.__version__}")

    except Exception as e:

        print(f"WARNING: Could not import bitsandbytes: {e}")


    # --------------------------------------------------------
    # Find bitsandbytes quantized modules
    # --------------------------------------------------------

    quantized_modules = []

    for name, module in base_model.named_modules():

        module_name = module.__class__.__name__

        if (
            "Linear4bit" in module_name
            or "Linear8bit" in module_name
            or "Params4bit" in module_name
        ):

            quantized_modules.append(
                (name, module_name)
            )


    print(
        f"\nQuantized modules found: "
        f"{len(quantized_modules)}"
    )

    if quantized_modules:

        print("\nFirst quantized modules:")

        for name, module_name in quantized_modules[:10]:

            print(
                f"  {name:<70} "
                f"{module_name}"
            )

        if len(quantized_modules) > 10:

            print(
                f"  ... and "
                f"{len(quantized_modules) - 10} more"
            )

        print("\n4-bit quantization detected: YES")

    else:

        print("\n4-bit quantization detected: NO")


    # --------------------------------------------------------
    # Check for Params4bit
    # --------------------------------------------------------

    params4bit_count = 0

    for name, param in base_model.named_parameters():

        if param.__class__.__name__ == "Params4bit":

            params4bit_count += 1


    print(
        f"Params4bit tensors: {params4bit_count}"
    )

    # --------------------------------------------------------
    # Quantization configuration
    # --------------------------------------------------------

    if hasattr(base_model, "config"):

        config = base_model.config

        print("\nQuantization config:")

        quant_config = getattr(
            config,
            "quantization_config",
            None
        )

        if quant_config is not None:

            print(
                f"  {quant_config}"
            )

        else:

            print(
                "  No quantization_config found "
                "in model config."
            )

# ============================================================
# BF16 CHECK
# ============================================================

else:

    print("\n" + "-" * 80)
    print("BF16 CHECK")
    print("-" * 80)

    all_bf16 = all(
        param.dtype == torch.bfloat16
        for param in base_model.parameters()
    )

    bf16_params = sum(
        param.numel()
        for param in base_model.parameters()
        if param.dtype == torch.bfloat16
    )

    print(
        f"\nBF16 parameters : "
        f"{bf16_params:,} / {total_params:,}"
    )

    print(
        f"BF16 percentage : "
        f"{bf16_params / total_params * 100:.2f}%"
    )

    print(
        f"All parameters BF16: {all_bf16}"
    )

# ============================================================
# DEVICE CHECK
# ============================================================

print("\n" + "-" * 80)
print("DEVICE CHECK")
print("-" * 80)

device_stats = {}

for param in base_model.parameters():

    device = str(param.device)

    if device not in device_stats:
        device_stats[device] = 0

    device_stats[device] += param.numel()


for device, num_params in device_stats.items():

    percentage = (
        num_params / total_params * 100
    )

    print(
        f"  {device:<15} "
        f"{num_params:>15,} params "
        f"({percentage:6.2f}%)"
    )

# ============================================================
# DEVICE MAP
# ============================================================

print("\nDevice map:")

if hasattr(base_model, "hf_device_map"):

    for device, count in {}.items():
        pass

    print(base_model.hf_device_map)

else:

    print("  No hf_device_map available.")

# ============================================================
# MODEL CONFIG
# ============================================================

print("\n" + "-" * 80)
print("MODEL CONFIG")
print("-" * 80)

print(
    f"  Hidden size       : "
    f"{base_model.config.hidden_size}"
)

print(
    f"  Layers            : "
    f"{base_model.config.num_hidden_layers}"
)

print(
    f"  Attention heads   : "
    f"{base_model.config.num_attention_heads}"
)

print(
    f"  Vocabulary size   : "
    f"{base_model.config.vocab_size}"
)

# ============================================================
# GPU MEMORY
# ============================================================

if torch.cuda.is_available():

    print("\n" + "-" * 80)
    print("GPU MEMORY")
    print("-" * 80)

    for i in range(torch.cuda.device_count()):

        allocated = (
            torch.cuda.memory_allocated(i)
            / 1024**3
        )

        reserved = (
            torch.cuda.memory_reserved(i)
            / 1024**3
        )

        total = (
            torch.cuda.get_device_properties(i).total_memory
            / 1024**3
        )

        print(
            f"GPU {i}: "
            f"{torch.cuda.get_device_name(i)}"
        )

        print(
            f"  Total     : {total:.2f} GB"
        )

        print(
            f"  Allocated : {allocated:.2f} GB"
        )

        print(
            f"  Reserved  : {reserved:.2f} GB"
        )

print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)
# ================================================================================================================
# MODEL VERIFICATION END
# ================================================================================================================



# ============================================================
# LORA
# ============================================================

print("Loading LoRA...")

model = PeftModel.from_pretrained(
    base_model,
    LORA_ID,
    token=HF_TOKEN
)


# ============================================================
# STEERING VECTOR
# ============================================================

print("Loading steering vector...")

human_vector = torch.load(
    STEERING_VECTOR_PATH,
    map_location="cpu"
)

model_dtype = next(
    p for p in model.parameters()
    if p.is_floating_point()
).dtype

steering_vector = human_vector.to(
    device=model.device,
    dtype=model_dtype
)

print("Model dtype:", model_dtype)
print("Model device:", model.device)
print("Steering vector dtype:", steering_vector.dtype)
print("Steering vector device:", steering_vector.device)
print("Steering vector norm:", steering_vector.norm().item())



# ============================================================
# RUNPOD HANDLER
# ============================================================

def handler(event):

    print("Received event:")
    # print(event)

    input_data = event["input"]

    # ========================================================
    # MESSAGES
    # ========================================================

    messages_data = input_data["messages"]

    messages = []

    for message in messages_data:

        role = message["role"]
        content = message["content"]

        if role == "system":

            messages.append(
                SystemMessage(content=content)
            )

        elif role == "user":

            messages.append(
                HumanMessage(content=content)
            )

        elif role == "assistant":

            messages.append(
                AIMessage(content=content)
            )

        else:
            raise ValueError(f"Unsupported role: {role}")

    # ========================================================
    # GENERATION PARAMETERS
    # ========================================================

    temperature = input_data.get(
        "temperature",
        0.7
    )

    max_new_tokens = input_data.get(
        "max_new_tokens",
        200
    )

    top_p = input_data.get(
        "top_p",
        0.9
    )

    top_k = input_data.get(
        "top_k",
        50
    )

    repetition_penalty = input_data.get(
        "repetition_penalty",
        1.0
    )

    stream = input_data.get(
            "stream",
            False
        )

    # ========================================================
    # LORA / STEERING
    # ========================================================

    use_lora = input_data.get(
        "use_lora",
        True
    )

    steering_coefficient = input_data.get(
        "steering_coefficient",
        0.0
    )


    # ========================================================
    # DEBUG
    # ========================================================

    show_statistics = input_data.get(
            "show_statistics",
            False
        )

    show_input = input_data.get(
            "show_input",
            False
        )

    # ========================================================
    # CREATE LLM
    # ========================================================

    llm = LocalLlamaChatLLM(

        model=model,
        tokenizer=tokenizer,
        steering_vector=steering_vector,

        temperature=temperature,
        max_new_tokens=max_new_tokens,

        top_p=top_p,
        top_k=top_k,
        repetition_penalty=repetition_penalty,

        use_lora=use_lora,
        steering_coefficient=steering_coefficient,

        show_statistics=show_statistics,
        show_input=show_input


    )

    if show_statistics:
        print("Generation parameters:")
        print("temperature:", temperature)
        print("max_new_tokens:", max_new_tokens)
        print("top_p:", top_p)
        print("top_k:", top_k)
        print("repetition_penalty:", repetition_penalty)
        print("use_lora:", use_lora)
        print("steering_coefficient:", steering_coefficient)
        print("stream:", stream)
        print("show_statistics:", show_statistics)
        print("show_input:", show_input)

    if show_input:

        messages_for_tokenizer = [
            {
                "role": (
                    "system" if message.type == "system"
                    else "user" if message.type == "human"
                    else "assistant"
                ),
                "content": message.content
            }
            for message in messages
        ]

        print("\n")
        print("Here below the input sent to the model:")

        input_text = tokenizer.apply_chat_template(
            messages_for_tokenizer,
            tokenize=False,
            add_generation_prompt=True
        )

        print(input_text)

   
    if stream:
        print("===== RETURNING STREAM GENERATOR =====",flush=True)

        for chunk in llm.stream(messages):

            if chunk.content:
                yield {"response": chunk.content}

    else:
        print("===== INVOKE MODE =====",flush=True)

        response = llm.invoke(messages)

        yield {
            "response": response.content
        }


# ============================================================
# START SERVERLESS WORKER
# ============================================================

print("RUNPOD VERSION:", runpod.__version__, flush=True)

runpod.serverless.start({
    "handler": handler,
    "return_aggregate_stream": True
})


# {
#   "input": {
#     "messages": [
#       {
#         "role": "system",
#         "content": "You are Sébastien."
#       },
#       {
#         "role": "user",
#         "content": "Who are you?"
#       }
#     ],
#     "temperature": 0.7,
#     "max_new_tokens": 200,
#     "top_p": 0.9,
#     "top_k": 50,
#     "repetition_penalty": 1.1,
#     "use_lora": true,
#     "steering_coefficient": 0.0
#   }
# }
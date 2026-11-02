import torch
import threading

from transformers import TextIteratorStreamer

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    AIMessageChunk
)
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.outputs.chat_generation import ChatGenerationChunk
from pydantic import Field


# show_Statistics = True

class LocalLlamaChatLLM(BaseChatModel):

    temperature: float = 0.7
    max_new_tokens: int = 200

    top_p: float = 0.9
    top_k: int = 50
    repetition_penalty: float = 1.0

    use_lora: bool = True
    steering_coefficient: float = 0.0

    show_statistics: bool = False
    show_input: bool = False

    model: object = Field(
        default=None,
        exclude=True
    )

    tokenizer: object = Field(
        default=None,
        exclude=True
    )

    steering_vector: object = Field(
        default=None,
        exclude=True
    )

    class Config:
        arbitrary_types_allowed = True

    # ============================================================
    # LangChain messages -> Llama chat format
    # ============================================================

    def _convert_messages(self, messages):

        converted = []

        for message in messages:

            if isinstance(message, HumanMessage):
                role = "user"

            elif isinstance(message, AIMessage):
                role = "assistant"

            elif isinstance(message, SystemMessage):
                role = "system"

            else:
                # role = "user"
                raise TypeError(
                f"Unsupported message type: {type(message).__name__}"
                )

            converted.append({
                "role": role,
                "content": message.content
            })

        return converted

    # ============================================================
    # Steering hook
    # ============================================================

    def _make_steering_hook(
        self,
        coefficient,
        stats
    ):

        vector = self.steering_vector

        def hook(module, inputs, output):

            if torch.is_tensor(output):

                hidden_states = output

            elif isinstance(output, tuple):

                hidden_states = output[0]

            else:

                raise TypeError(
                    f"Unexpected layer output type: "
                    f"{type(output)}"
                )

            v = vector.to(
                device=hidden_states.device,
                dtype=hidden_states.dtype
            )

            delta = coefficient * v

            steered_hidden_states = (
                hidden_states + delta
            )

            # ----------------------------------------------------
            # Statistics
            # ----------------------------------------------------

            stats["calls"] += 1

            if stats["delta_norm"] is None:

                stats["delta_norm"] = (
                    delta.float().norm().item()
                )

            # ----------------------------------------------------
            # Return modified output
            # ----------------------------------------------------

            if torch.is_tensor(output):

                return steered_hidden_states

            return (
                steered_hidden_states,
                *output[1:]
            )

        return hook

    # ============================================================
    # Generation
    # ============================================================

    @torch.no_grad()
    def _generate_text(
        self,
        messages,
        temperature,
        max_new_tokens,
        top_p,
        top_k,
        repetition_penalty,
        show_statistics,
        show_input
    ):

        # global show_Statistics

        formatted_messages = (
            self._convert_messages(messages)
        )

        inputs = self.tokenizer.apply_chat_template(
            formatted_messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
            return_dict=True
        ).to(self.model.device)

        stats = {
            "calls": 0,
            "delta_norm": None
        }

        # --------------------------------------------------------
        # LoRA ON / OFF
        # --------------------------------------------------------

        if self.use_lora:

            self.model.enable_adapter_layers()

        else:

            self.model.disable_adapter_layers()

        # --------------------------------------------------------
        # Steering
        # --------------------------------------------------------

        layer_module = (
            self.model
            .base_model
            .model
            .model
            .layers[14]
        )

        hook = None

        if (
            self.steering_coefficient != 0
            and self.steering_vector is not None
        ):

            hook = layer_module.register_forward_hook(
                self._make_steering_hook(
                    self.steering_coefficient,
                    stats
                )
            )

        # --------------------------------------------------------
        # Sampling
        # --------------------------------------------------------

        do_sample = temperature > 0

        generation_kwargs = {
            **inputs,

            "max_new_tokens": max_new_tokens,

            "do_sample": do_sample,

            "repetition_penalty": (
                repetition_penalty
            ),

            "use_cache": True,

            "eos_token_id": [
                self.tokenizer.eos_token_id,

                self.tokenizer.convert_tokens_to_ids(
                    "<|eot_id|>"
                )
            ]
        }

        if do_sample:

            generation_kwargs["temperature"] = (
                temperature
            )

            generation_kwargs["top_p"] = (
                top_p
            )

            generation_kwargs["top_k"] = (
                top_k
            )

        # --------------------------------------------------------
        # Generation
        # --------------------------------------------------------

        try:

            outputs = self.model.generate(
                **generation_kwargs
            )

        finally:

            if hook is not None:
                hook.remove()

        # --------------------------------------------------------
        # Decode
        # --------------------------------------------------------

        prompt_length = (
            inputs["input_ids"].shape[-1]
        )

        generated_tokens = outputs[0][
            prompt_length:
        ]

        response = self.tokenizer.decode(
            generated_tokens,
            skip_special_tokens=True
        )

        # --------------------------------------------------------
        # Statistics
        # --------------------------------------------------------

        # if show_Statistics:
        if show_statistics:

            print("\n")
            print(
                "===== INFERENCE STATISTICS ====="
            )

            print(
                "LoRA requested:",
                self.use_lora
            )

            print(
                "Active adapters:",
                getattr(
                    self.model,
                    "active_adapters",
                    "N/A"
                )
            )

            print(
                "Steering coefficient:",
                self.steering_coefficient
            )

            print(
                "Steering vector:",
                self.steering_vector is not None
            )

            print(
                "Steering hook calls:",
                stats["calls"]
            )

            print(
                "Steering delta norm:",
                stats["delta_norm"]
            )

            print(
                "================================"
            )

        return response, stats

    # ============================================================
    # LangChain invoke()
    # ============================================================

    def _generate(
        self,
        messages,
        stop=None,
        run_manager=None,
        **kwargs
    ):

        temperature = kwargs.get(
            "temperature",
            self.temperature
        )

        max_new_tokens = kwargs.get(
            "max_new_tokens",
            self.max_new_tokens
        )

        top_p = kwargs.get(
            "top_p",
            self.top_p
        )

        top_k = kwargs.get(
            "top_k",
            self.top_k
        )

        repetition_penalty = kwargs.get(
            "repetition_penalty",
            self.repetition_penalty
        )

        show_statistics = kwargs.get(
            "show_statistics",
            self.show_statistics
        )

        show_input = kwargs.get(
            "show_input",
            self.show_input
        )

        

        response, stats = self._generate_text(
            messages,
            temperature,
            max_new_tokens,
            top_p,
            top_k,
            repetition_penalty,
            show_statistics,
            show_input
        )

        return ChatResult(
            generations=[
                ChatGeneration(
                    message=AIMessage(
                        content=response
                    )
                )
            ]
        )

    # ============================================================
    # LangChain streaming
    # ============================================================

    def _stream(
        self,
        messages,
        stop=None,
        run_manager=None,
        **kwargs
    ):

        # global show_Statistics

        # --------------------------------------------------------
        # Parameters
        # --------------------------------------------------------

        temperature = kwargs.get(
            "temperature",
            self.temperature
        )

        max_new_tokens = kwargs.get(
            "max_new_tokens",
            self.max_new_tokens
        )

        top_p = kwargs.get(
            "top_p",
            self.top_p
        )

        top_k = kwargs.get(
            "top_k",
            self.top_k
        )

        repetition_penalty = kwargs.get(
            "repetition_penalty",
            self.repetition_penalty
        )

        show_statistics = kwargs.get(
            "show_statistics",
            self.show_statistics
        )
        
        show_input = kwargs.get(
            "show_input",
            self.show_input
        )

        # --------------------------------------------------------
        # Messages
        # --------------------------------------------------------

        formatted_messages = (
            self._convert_messages(messages)
        )

        inputs = self.tokenizer.apply_chat_template(
            formatted_messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
            return_dict=True
        ).to(self.model.device)

        # --------------------------------------------------------
        # Streamer
        # --------------------------------------------------------

        streamer = TextIteratorStreamer(
            self.tokenizer,
            skip_prompt=True,
            skip_special_tokens=True
        )

        # --------------------------------------------------------
        # Statistics
        # --------------------------------------------------------

        stats = {
            "calls": 0,
            "delta_norm": None
        }

        # --------------------------------------------------------
        # LoRA ON / OFF
        # --------------------------------------------------------

        if self.use_lora:

            self.model.enable_adapter_layers()

        else:

            self.model.disable_adapter_layers()

        # --------------------------------------------------------
        # Steering
        # --------------------------------------------------------

        layer_module = (
            self.model
            .base_model
            .model
            .model
            .layers[14]
        )

        hook = None

        if (
            self.steering_coefficient != 0
            and self.steering_vector is not None
        ):

            hook = layer_module.register_forward_hook(
                self._make_steering_hook(
                    self.steering_coefficient,
                    stats
                )
            )

        # --------------------------------------------------------
        # Sampling
        # --------------------------------------------------------

        do_sample = temperature > 0

        generation_kwargs = {
            **inputs,

            "streamer": streamer,

            "max_new_tokens": max_new_tokens,

            "do_sample": do_sample,

            "repetition_penalty": (
                repetition_penalty
            ),

            "use_cache": True,

            "eos_token_id": [
                self.tokenizer.eos_token_id,

                self.tokenizer.convert_tokens_to_ids(
                    "<|eot_id|>"
                )
            ]
        }

        if do_sample:

            generation_kwargs["temperature"] = (
                temperature
            )

            generation_kwargs["top_p"] = (
                top_p
            )

            generation_kwargs["top_k"] = (
                top_k
            )

        # --------------------------------------------------------
        # Generation thread
        # --------------------------------------------------------

        generation_exception = []

        def generate():

            try:

                with torch.no_grad():

                    self.model.generate(
                        **generation_kwargs
                    )

            except Exception as e:

                generation_exception.append(e)

                # Important:
                # unblock the streamer if generation fails
                streamer.on_finalized_text(
                    "",
                    stream_end=True
                )

            finally:

                if hook is not None:
                    hook.remove()

        thread = threading.Thread(
            target=generate
        )

        thread.start()

        # --------------------------------------------------------
        # Streaming
        # --------------------------------------------------------

        try:

            for token in streamer:

                if run_manager is not None:

                    run_manager.on_llm_new_token(
                        token
                    )

                yield ChatGenerationChunk(
                    message=AIMessageChunk(
                        content=token
                    )
                )

        finally:

            thread.join()

        # --------------------------------------------------------
        # Generation error
        # --------------------------------------------------------

        if generation_exception:

            raise generation_exception[0]

        # --------------------------------------------------------
        # Statistics
        # --------------------------------------------------------

        # if show_Statistics:
        if show_statistics:

            print("\n")
            print(
                "===== INFERENCE STATISTICS ====="
            )

            print(
                "LoRA requested:",
                self.use_lora
            )

            print(
                "Active adapters:",
                getattr(
                    self.model,
                    "active_adapters",
                    "N/A"
                )
            )

            print(
                "Steering coefficient:",
                self.steering_coefficient
            )

            print(
                "Steering vector:",
                self.steering_vector is not None
            )

            print(
                "Steering hook calls:",
                stats["calls"]
            )

            print(
                "Steering delta norm:",
                stats["delta_norm"]
            )

            print(
                "================================"
            )

    # ============================================================
    # Type
    # ============================================================

    @property
    def _llm_type(self):

        return (
            "local-llama-3.1-8b-lora-steering"
        )
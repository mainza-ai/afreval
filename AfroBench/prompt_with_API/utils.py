from __future__ import annotations
import os

import openai
import asyncio
import logging
import aiolimiter

from aiohttp import ClientSession
from tqdm.asyncio import tqdm_asyncio

from typing import Any
from typing import List

from together import Together
import google.generativeai as genai


def create_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def get_language(langcode):
    language_dict = {
        "am": "Amharic",
        "bm": "Bambara",
        "ee": "Ewe",
        "en": "English",
        "fr": "French",
        "ha": "Hausa",
        "ig": "Igbo",
        "rw": "Kinyarwanda",
        "lg": "Luganda",
        "ny": "Chichewa",
        "sn": "chiShona",
        "sw": "Kiswahili",
        "tn": "Setswana",
        "tw": "Twi",
        "wo": "Wolof",
        "xh": "isiXhosa",
        "yo": "Yoruba",
        "zu": "isiZulu",
        "amh": "Amharic",
        "ewe": "Ewe",
        "fra": "French",
        "hau": "Hausa",
        "ibo": "Igbo",
        "kin": "Kinyarwanda",
        "lin": "Lingala",
        "lug": "Luganda",
        "orm": "Oromo",
        "sna": "Shona",
        "sot": "Sotho",
        "swa": "Swahili",
        "twi": "Twi",
        "wol": "Wolof",
        "xho": "Xhosa",
        "yor": "Yoruba",
        "zul": "Zulu",
        "eng": "English",
        "bbj": "Gbomala",
        "luo": "Luo",
        "mos": "Mossi",
        "pcm": "Nigerian Pidgin",
        "bam": "Bambara",
        "fon": "Fon",
        "nya": "Chichewa",
        "tsn": "Setswana",
        "arq": "Algerian Arabic",
        "ary": "Moroccan Arabic",
        "por": "Mozambique Portuguese",
        "tir": "Tigrinya",
        "tso": "Xithonga",
        "ach": "Acholi",
        "lgg": "Lugbara",
        "teo": "Ateso",
        "run": "Rundi",
        "nyn": "Runyankole",
        "som": "Somali",
        "AR_XY": "Arabic",
        "SW_KE": "Swahili",
        "YO_NG": "Yoruba",
        "ace_Latn": "Acehnese (Latin script)",
        "ace_Arab": "Acehnese (Arabic script)",
        "acq_Arab": "Ta’izzi-Adeni Arabic",
        "aeb_Arab": "Tunisian Arabic",
        "afr_Latn": "Afrikaans",
        "aka_Latn": "Akan",
        "amh_Ethi": "Amharic",
        "ary_Arab": "Moroccan Arabic",
        "arz_Arab": "Egyptian Arabic",
        "bam_Latn": "Bambara",
        "ban_Latn": "Balinese",
        "bem_Latn": "Bemba",
        "cjk_Latn": "Chokwe",
        "dik_Latn": "Southwestern Dinka",
        "dyu_Latn": "Dyula",
        "ewe_Latn": "Ewe",
        "eng_Latn": "English",
        "fon_Latn": "Fon",
        "fra_Latn": "French",
        "fuv_Latn": "Nigerian Fulfulde",
        "hau_Latn": "Hausa",
        "ibo_Latn": "Igbo",
        "kab_Latn": "Kabyle",
        "kam_Latn": "Kamba",
        "knc_Arab": "Central Kanuri (Arabic script)",
        "knc_Latn": "Central Kanuri (Latin script)",
        "kbp_Latn": "Kabiyè",
        "kea_Latn": "Kabuverdianu",
        "kik_Latn": "Kikuyu",
        "kin_Latn": "Kinyarwanda",
        "kmb_Latn": "Kimbundu",
        "kon_Latn": "Kikongo",
        "lin_Latn": "Lingala",
        "lua_Latn": "Luba-Kasai",
        "lug_Latn": "Luganda",
        "luo_Latn": "Luo",
        "plt_Latn": "Plateau Malagasy",
        "por_Latn": "Portuguese",
        "mos_Latn": "Mossi",
        "nso_Latn": "Northern Sotho",
        "nus_Latn": "Nuer",
        "nya_Latn": "Nyanja",
        "gaz_Latn": "Oromo",
        "run_Latn": "Rundi",
        "sag_Latn": "Sango",
        "sna_Latn": "Shona",
        "som_Latn": "Somali",
        "sot_Latn": "Southern Sotho",
        "ssw_Latn": "Swati",
        "sun_Latn": "Sundanese",
        "swh_Latn": "Swahili",
        "tir_Ethi": "Tigrinya",
        "taq_Latn": "Tamasheq",
        "taq_Tfng": "Tamasheq (Tifinagh script)",
        "tsn_Latn": "Setswana",
        "tso_Latn": "Tsonga",
        "tum_Latn": "Tumbuka",
        "twi_Latn": "Twi",
        "tzm_Tfng": "Central Atlas Tamazight",
        "umb_Latn": "Umbundu",
        "wol_Latn": "Wolof",
        "xho_Latn": "Xhosa",
        "yor_Latn": "Yoruba",
        "zul_Latn": "Zulu",
        "arb_Arab": "Arabic",
        "mey_Arab": "Hassaniya Arabic",
        "mlg_Latn": "Malagasy",
        "msa_Latn": "Malay",
        "nde_Latn": "North Ndebele",
        "orm_Ethi": "Oromo",
        "shi_Arab": "Tachelhit",
        "swa_Latn": "Swahili",
        "tam_Taml": "Tamil",
        "tel_Telu": "Telugu",
        "ton_Latn": "Tongan",
        "urd_Arab": "Urdu",
        "ven_Latn": "Venda",

    }
    return language_dict[langcode]


async def dispatch_openai_requests(
        messages_list: List[List[dict[str, str]]],
        model: str,
        temperature: float,
        max_tokens: int,
        top_p: float,
) -> List[str]:
    """Dispatches requests to OpenAI API asynchronously.

    Args:
        messages_list: List of messages to be sent to OpenAI ChatCompletion API.
        model: OpenAI model to use.
        temperature: Temperature to use for the model.
        max_tokens: Maximum number of tokens to generate.
        top_p: Top p to use for the model.

    Returns:
        List of responses from OpenAI API.
    """
    async_responses = [
        openai.ChatCompletion.acreate(
            model=model,
            messages=x,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
        )
        for x in messages_list
    ]
    return await asyncio.gather(*async_responses)


async def _throttled_openai_chat_completion_acreate(
        model: str,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
        top_p: float,
        limiter: aiolimiter.AsyncLimiter,
) -> dict[str, Any]:
    async with limiter:
        for _ in range(100):
            try:
                return await openai.ChatCompletion.acreate(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=top_p,
                )
            except openai.error.RateLimitError:
                logging.warning("OpenAI API rate limit exceeded. Sleeping for 50 seconds.")
                await asyncio.sleep(50)
            except asyncio.exceptions.TimeoutError:
                logging.warning("OpenAI API timeout. Sleeping for 50 seconds.")
                await asyncio.sleep(50)
            except openai.error.ServiceUnavailableError:
                logging.warning("OpenAI Server overload. Sleeping for 1 minute.")
                await asyncio.sleep(60)
            except openai.error.APIConnectionError:
                logging.warning("OpenAI Communication Error. Sleeping for 2 minutes.")
                await asyncio.sleep(120)
            except openai.error.Timeout:
                logging.warning("OpenAI Timeout. Sleeping for 2 minutes.")
                await asyncio.sleep(120)
            except openai.error.APIError as e:
                logging.warning(f"OpenAI API error: {e}")
                break
        return {"choices": [{"message": {"content": ""}}]}


async def generate_from_openai_chat_completion(
        full_contexts: List[List[dict[str, str]]],
        model_config: str,
        temperature: float,
        max_tokens: int,
        top_p: float,
        requests_per_minute: int = 300,
) -> list[str]:
    """Generate from OpenAI Chat Completion API.

    Args:
        full_contexts: List of full contexts to generate from.
        model_config: Model configuration.
        temperature: Temperature to use.
        max_tokens: Maximum number of tokens to generate.
        top_p: Top p to use.
        requests_per_minute: Number of requests per minute to allow.

    Returns:
        List of generated responses.
    """
    session = ClientSession()
    openai.aiosession.set(session)
    limiter = aiolimiter.AsyncLimiter(requests_per_minute)
    async_responses = [
        _throttled_openai_chat_completion_acreate(
            model=model_config,
            messages=full_context,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            limiter=limiter,
        )
        for full_context in full_contexts
    ]
    responses = await tqdm_asyncio.gather(*async_responses)
    await session.close()
    return [x["choices"][0]["message"]["content"] for x in responses]


async def _throttled_gemini_generate_content(model_name: str, prompt: str, limiter: asyncio.Semaphore) -> str:
    """
    Sends a single prompt to Gemini API with throttling and error handling.

    Args:
        model_name: Gemini model to be evaluated
        prompt: The input string to send to the model.
        limiter: An asyncio semaphore to throttle concurrent requests.

    Returns:
        The response content from the model or a fallback message.
    """
    model = genai.GenerativeModel(model_name)
    async with limiter:
        for attempt in range(100):
            try:
                response = await asyncio.to_thread(model.generate_content, prompt)
                return response.text
            except asyncio.exceptions.TimeoutError:
                logging.info("Async timeout. Sleeping for 50 seconds.")
                await asyncio.sleep(50)
            except Exception as e:
                logging.error(f"Unexpected error: {e}. Retrying after 50 seconds...")
                await asyncio.sleep(50)

        # Return a fallback response after retries
        logging.info(f"Maximum retries reached for prompt: {prompt}")
        return "[Error: No response received after retries]"


async def generate_gemini_responses(model_name: str, prompts: List[str], concurrency_limit: int = 25) -> List[str]:
    """
    Sends multiple prompts to Gemini API asynchronously with throttling.

    Args:
        model_name: Gemini model to be evaluated
        prompts: A list of input prompts to process.
        concurrency_limit: The maximum number of concurrent requests.

    Returns:
        A list of generated responses from the model.
    """
    limiter = asyncio.Semaphore(concurrency_limit)
    tasks = [_throttled_gemini_generate_content(model_name, prompt, limiter) for prompt in prompts]
    response = await tqdm_asyncio.gather(*tasks)
    return [x for x in response]


async def _throttled_together_generate_content(model_name: str, prompt: str, limiter: asyncio.Semaphore) -> str:
    """
    Sends a single prompt to Together API with throttling and error handling.

    Args:
        model_name: Together model to be evaluated.
        prompt: The input string to send to the model.
        limiter: An asyncio semaphore to throttle concurrent requests.

    Returns:
        The response content from the model or a fallback message.
    """
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        raise ValueError('TogetherAI API key is not set. Please export it using: '
                         'export TOGETHER_API_KEY="your_api_key"')
    client = Together(api_key=api_key)
    async with limiter:
        for attempt in range(100):  # Max retries
            try:
                response = await asyncio.to_thread(
                    client.chat.completions.create,
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    stop=["</s>", "**"],
                    temperature=0.0,
                    max_tokens=8190-len(prompt)
                )
                return response.choices[0].message.content
            except asyncio.exceptions.TimeoutError:
                logging.info("Async timeout. Sleeping for 50 seconds.")
                await asyncio.sleep(50)
            except Exception as e:
                logging.error(f"Unexpected error: {e}. Retrying after 50 seconds...")
                await asyncio.sleep(50)

        # Return a fallback response after retries
        logging.info(f"Maximum retries reached for prompt: {prompt}")
        return "[Error: No response received after retries]"


async def generate_together_responses(
    model_name: str, prompts: List[str], concurrency_limit: int = 25
) -> List[str]:
    """
    Sends multiple prompts to Together API asynchronously with throttling.

    Args:
        model_name: Together model to be evaluated.
        prompts: A list of input prompts to process.
        concurrency_limit: The maximum number of concurrent requests.

    Returns:
        A list of generated responses from the model.
    """
    limiter = asyncio.Semaphore(concurrency_limit)
    tasks = [
        _throttled_together_generate_content(model_name, prompt, limiter)
        for prompt in prompts
    ]
    responses = await asyncio.gather(*tasks)
    return [x for x in responses]


def call_model(model_name: str, prompts):
    if "gpt" in model_name:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError('OpenAI API key is not set. Please export it using: '
                             'export OPENAI_API_KEY="your_api_key"')
        openai.api_key = api_key
        all_input_messages = []
        for message in prompts:
            input_mes = [{"role": "system", "content": "You are a helpful assistant."},
                         {"role": "user", "content": message}]
            all_input_messages.append(input_mes)

        responses = asyncio.run(
            generate_from_openai_chat_completion(all_input_messages, model_name, 0.3, 500, 1.0, 500))

        completions = [completion_text.lower() for completion_text in responses]
    elif "gemini" in model_name or 'gemma-3' in model_name:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError('Gemini API key is not set. Please export it using: '
                             'export GEMINI_API_KEY="your_api_key"')
        genai.configure(api_key=api_key)
        responses = asyncio.run(generate_gemini_responses(model_name, prompts))
        completions = [completion_text.lower() for completion_text in responses]
    else:
        responses = asyncio.run(generate_together_responses(model_name, prompts))
        completions = [completion_text.lower() for completion_text in responses]
    return completions

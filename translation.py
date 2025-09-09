import re
import uuid
import json
import time
import requests

import config
from ADC_function import get_html, post_html, is_japanese


def translate(
        src: str,
        target_language: str = config.getInstance().get_target_language(),
        engine: str = config.getInstance().get_translate_engine(),
        app_id: str = "",
        key: str = "",
        delay: int = 0,
) -> str:
    """
    translate japanese kana to simplified chinese
    翻译日语假名到简体中文
    :raises ValueError: Non-existent translation engine
    """
    trans_result = ""
    # 中文句子如果包含&等符号会被谷歌翻译截断损失内容，而且中文翻译到中文也没有意义，故而忽略，只翻译带有日语假名的
    if (is_japanese(src) == False) and ("zh_" in target_language):
        return src
    if engine == "google-free":
        gsite = config.getInstance().get_translate_service_site()
        if not re.match('^translate\.google\.(com|com\.\w{2}|\w{2})$', gsite):
            gsite = 'translate.google.cn'
        url = (
            f"https://{gsite}/translate_a/single?client=gtx&dt=t&dj=1&ie=UTF-8&sl=auto&tl={target_language}&q={src}"
        )
        result = get_html(url=url, return_type="object")
        if not result.ok:
            print('[-]Google-free translate web API calling failed.')
            return ''

        translate_list = [i["trans"] for i in result.json()["sentences"]]
        trans_result = trans_result.join(translate_list)
    elif engine == "azure":
        url = "https://api.cognitive.microsofttranslator.com/translate?api-version=3.0&to=" + target_language
        headers = {
            'Ocp-Apim-Subscription-Key': key,
            'Ocp-Apim-Subscription-Region': "global",
            'Content-type': 'application/json',
            'X-ClientTraceId': str(uuid.uuid4())
        }
        body = json.dumps([{'text': src}])
        result = post_html(url=url, query=body, headers=headers)
        translate_list = [i["text"] for i in result.json()[0]["translations"]]
        trans_result = trans_result.join(translate_list)
    elif engine == "deeplx":
        url = config.getInstance().get_translate_service_site()
        res = requests.post(f"{url}/translate", json={
            'text': src,
            'source_lang': 'auto',
            'target_lang': target_language,
        })
        if res.text.strip():
            trans_result = res.json().get('data')
    else:
        raise ValueError("Non-existent translation engine")

    time.sleep(delay)
    return trans_result



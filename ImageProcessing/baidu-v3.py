from aip import AipFace
import config
import base64


def face_center(filename, model):
    app_id = config.getInstance().conf.get("face", "appid")
    api_key = config.getInstance().conf.get("face", "key")
    app_secret = config.getInstance().conf.get("face", "secret")
    app_id="31706772"
    api_key="n612hyIb9jdSfuSmZiRK4lko"
    app_secret="s6eIWbLFI8fsGbe1sz5dp5YKFBq2Cctu"
    client = AipFace(app_id, api_key, app_secret)
    with open(filename, 'rb') as fp:
        base64_data = base64.b64encode(fp.read())
    result = client.detect(base64_data.decode('utf-8'),"BASE64")
    if result['error_msg']!='SUCCESS':
        raise ValueError(result['error_msg'])
    result = result['result']
    print('[+]Found face      ' + str(result['face_num']))
    # 
    maxRight = 0
    maxTop = 0
    for face in result["face_list"]:
        left = int(face['location']['left'])
        top = int(face['location']['top'])
        width = int(face['location']['width'])
        if left+width > maxRight:
            maxRight = left+width
            maxTop = top
    return maxRight,maxTop

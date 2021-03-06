def bitly(long_url):
    from urllib.parse import urlencode
    import http.client
    import settings
    import json
    url = '/v3/shorten?'
    params = urlencode({
        'login': 'enum',
        'apiKey': settings.bitly_api_key,
        'longUrl': long_url
        })

    req = url + params
    conn = http.client.HTTPConnection("api.bitly.com")
    conn.request("GET",req)

    response = conn.getresponse()
    return json.loads(response.read())['data']['url']

if __name__ == '__main__':
    print(bitly('http://greynode.org'))

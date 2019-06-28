import urllib.request


def file_get_contents(filename):
    res = ''
    if filename.startswith('http'):
        res = urllib.request.urlopen(filename).read().decode()
    else:
        with open(filename, 'r') as f:
            res = f.read()
    return res

# -*- coding: utf-8 -*-
import argparse
import csv
import os
import re
import json
import requests
import urllib.parse
from config import API, USER, PASSWORD  # pylint: disable=E0611


def parse_update(text):
    if text in ['End', 'Next']:
        return 'Q58'
    if re.search(r'^[日一二三四五六]\d', text):
        return 'Q56'
    if re.search(r'^\d[早午晚夜]', text):
        return 'Q56'
    return ''


def parse_link(link):
    if link in ['YT', 'biliblili', 'bilibili', '-']:
        return ''

    downsites = [
        'www.acgntw.website',
        'm.dm530.net',
        'www.dm530.net',
        'www.g2dy.com',
        'www.7676dy.com',
        'www.dilidili.wang',
        'video.99kubo.com',
        '2d-gate.org',
        's-dm.com',
        'www.tucao.tv',
        'rcsos5538313.joinbbs.net',
        'fenglin.to',
        'dhr.moe',
        'vid.me',

        'www.myvideos.cc',
        'www.soonnet.org',
        'www.acfun.cn',
    ]
    for site in downsites:
        if '://' + site + '/' in link:
            return ''

    link = urllib.parse.unquote(link)

    link = link.replace('http://comic.92148.com/', 'https://www.92148.com/')
    link = link.replace('http://www.forcomic.com/', 'http://www.forcomic.info/')
    link = link.replace('http://www2.animeland.tv/', 'https://www.animeland.us/')

    httpslist = [
        'ani.gamer.com.tw',
        'www.92148.com',
        '8drama.com',
        '8maple.ru',
        'www.bilibili.com',
        'www.dailymotion.com',
        'movie.i-kale.net',
        'myself-bbs.com',
        'www.d1-dm.com',
        'www.soku.com',
        'watchcartoonsonline.eu',
        'www.iqiyi.com',
    ]
    for https in httpslist:
        link = link.replace('http://{}/'.format(https), 'https://{}/'.format(https))

    link = link.replace('https://8drama.com/', 'https://8maple.ru/')
    link = link.replace('https://watchcartoonsonline.eu/', 'https://www2.watchcartoonsonline.eu/')

    link = re.sub(r'^https?://bangumi.bilibili.com/anime/(\d+)/?(?:play)?$',
                  r'https://www.bilibili.com/bangumi/media/md\1', link)
    link = re.sub(r'^https?://bangumi.bilibili.com/movie/(\d+)/?$',
                  r'https://www.bilibili.com/bangumi/play/ss\1', link)
    return link


def parse_linkP(link):
    if link == '':
        return ''
    sitemap = {
        'https://8maple.ru/': 'P33',
        'https://ani.gamer.com.tw/animeVideo.php?sn=': 'P34',
        'https://www.bilibili.com/bangumi/': 'P35',
        'https://www.bilibili.com/video/': 'P35',
        'https://docs.google.com/file/d/': 'P36',
        'https://www.92148.com/': 'P37',
        'https://anime1.me/': 'P38',
        'https://anime1.pw/': 'P38',
        'http://dm.tsdm.tv/': 'P39',
        'http://www.forcomic.info/': 'P40',
        'https://www.dailymotion.com/': 'P41',
        'http://list.youku.com/': 'P42',
        'https://v.youku.com/': 'P42',
        'https://myself-bbs.com/': 'P43',
        'https://movie.i-kale.net/': 'P44',
        'https://www.animeland.us/': 'P45',
        'http://www.i-comic.net/': 'P46',
        'https://www.d1-dm.com/': 'P47',
        'http://godanimation.blogspot.tw/': 'P48',
        'https://www.youtube.com/': 'P49',
        'https://youtu.be/': 'P49',
        'https://v.qq.com/': 'P50',
        'https://kiss53880520.blogspot.tw/': 'P51',
        'https://www.soku.com/': 'P52',
        'http://www.tudou.com/': 'P53',
        'https://www.facebook.com/': 'P54',
        'http://2dgate.drama.cool/': 'P55',
        'https://www.iqiyi.com/': 'P56',
        'https://tw.iqiyi.com/': 'P56',
        'https://www2.watchcartoonsonline.eu/': 'P57',
        'http://myanimesharearea.blogspot.com/': 'P58',
        'http://myanimesharearea.blogspot.tw/': 'P58',
        'http://www.99kubo.tv/': 'P59',
        'https://www.bimibimi.cc/': 'P60',
        'http://tiktak.tv/': 'P61',
        'http://video.eyny.com/': 'P62',
        'http://hentaihaven.org/': 'P63',
        'http://www.youmaker.com/': 'P64',
    }
    for site in sitemap:
        if link.startswith(site):
            return sitemap[site]
    return 'P32'


def parse_studio(studio):
    studiomap = {
        'P.A. Works': 'Q59',
        'P.A.WORKS': 'Q59',
        "Brain's Base": 'Q60',
        '京都動畫': 'Q61',
        'J.C.STAFF': 'Q62',
        'Production IMS': 'Q63',
        'Production I.G': 'Q64',
        'WHITE FOX': 'Q75',
        'MADHOUSE': 'Q76',
        'Madhouse': 'Q76',
        'SILVER LINK.': 'Q77',
        'A-1 Pictures': 'Q78',
        'Kinema Citrus': 'Q79',
        'Lerche': 'Q80',
        'feel.': 'Q81',
        'AIC Build': 'Q83',
        'AIC': 'Q83',
        'AIC PLUS+': 'Q83',
        'TROYCA': 'Q84',
        'NOMAD,Inc.': 'Q85',
        'OLM': 'Q86',
        'HAL FILM MAKER': 'Q87',
        'TMS娛樂': 'Q88',
        'TMS Entertainment': 'Q88',
        '8bit': 'Q89',
        'Qualia Animation': 'Q90',
        'GONZO': 'Q91',
        'PRODUCTION REED': 'Q92',
        'Studio 3Hz': 'Q93',
        'STUDIO DEEN': 'Q94',
        'スタジオディーン': 'Q94',
        'Bibury Animation Studios': 'Q95',
        'MAPPA': 'Q96',
        'LIDENFILMS': 'Q97',
        'CloverWorks': 'Q98',
        '動畫工房': 'Q99',
        'ARTLAND': 'Q100',
        'Creators in Pack': 'Q101',
        'project No.9': 'Q102',
        'AXsiZ': 'Q103',
        'XEBEC': 'Q104',
        'CoMix Wave Films': 'Q105',
        'TRIGGER': 'Q106',
        'EGG FIRM': 'Q107',
        'Lesprit': 'Q108',
        '龍之子製作公司': 'Q109',
        'Studio五組': 'Q110',
        'UWAN PICTURES': 'Q111',
        'C-Station': 'Q112',
        'ZERO-G': 'Q113',
        'TNK': 'Q114',
        'Hoods Entertainment': 'Q115',
        'Nexus': 'Q116',


        'Synergy SP': 'Q132',
        '三次元': 'Q131',
        'Ordet': 'Q130',
        'SHAFT': 'Q129',
        'ZEXCS': 'Q128',
        'Diomedéa': 'Q127',
        'Arms': 'Q126',
        'Actas': 'Q125',
        'Magic Bus': 'Q124',
        'PINE JAM': 'Q123',
        '新銳動畫': 'Q122',
        'SHIN-EI動畫': 'Q122',
        '手塚製作公司': 'Q121',
        'WIT STUDIO': 'Q120',
        'Passione': 'Q119',
        'Magia Doraglier': 'Q118',
        'NAZ': 'Q117',
    }
    studio = studio.replace('／', '、')
    studio = studio.replace(' × ', '、')
    studio = studio.replace('×', '、')
    studios = studio.split('、')
    result = []
    for studio in studios:
        if studio == '':
            continue
        if studio in studiomap:
            result.append(studiomap[studio])
        else:
            print(studio)
            input()
    return result


def parse_rating(text):
    if '18' in text:
        return 'Q50'
    if '15' in text:
        return 'Q49'
    if '12' in text:
        return 'Q48'
    if '6' in text:
        return 'Q47'
    if '0' in text:
        return 'Q46'
    return ''


def main(filename):
    session = requests.Session()

    print('fetching login token')
    res = session.get(API, params={
        'action': 'query',
        'meta': 'tokens',
        'type': 'login',
        'format': 'json',
    }).json()
    logintoken = res['query']['tokens']['logintoken']

    print('logging in')
    res = session.post(API, data={
        'action': 'login',
        'lgname': USER,
        'lgpassword': PASSWORD,
        'lgtoken': logintoken,
        'format': 'json',
    }).json()
    if res['login']['result'] == 'Success':
        print('login success')
    else:
        print('login fail')
        return

    res = session.get(API, params={
        'action': 'query',
        'meta': 'tokens',
        'type': 'csrf|rollback',
        'format': 'json',
    }).json()
    csrftoken = res['query']['tokens']['csrftoken']

    with open(filename) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            (
                Qid,
                animetitle,
                seenepisodes,
                allepisodes,
                _percent,
                update,
                comment,
                length,
                wikipedia,
                moegirl,
                link1,
                link2,
                link3,
                link4,
                _sort,
                studio,
                year,
                rating,
            ) = row

            if Qid != '':
                continue

            # animetitle
            animetitle = animetitle.split(' / ')
            othertitle = animetitle[1:]
            animetitle = animetitle[0]

            # update
            update = parse_update(update)

            # wikipedia
            # wikipedia = re.sub(r'^https?://zh.wikipedia.org/wiki/', '', wikipedia)
            wikipedia = urllib.parse.unquote(wikipedia)
            # wikipedia = wikipedia.replace('_', ' ')
            if wikipedia in ['-']:
                wikipedia = ''

            # moegirl
            # moegirl = re.sub(r'^https?://zh.moegirl.org/(zh-hant/)?', '', moegirl)
            moegirl = urllib.parse.unquote(moegirl)
            # moegirl = moegirl.replace('_', ' ')
            moegirl = re.sub(r'#.+?$', '', moegirl)
            if moegirl in ['-']:
                moegirl = ''

            # link
            link1 = parse_link(link1)
            link2 = parse_link(link2)
            link3 = parse_link(link3)
            link4 = parse_link(link4)

            link1P = parse_linkP(link1)
            link2P = parse_linkP(link2)
            link3P = parse_linkP(link3)
            link4P = parse_linkP(link4)

            # studio
            studio = parse_studio(studio)

            # year
            if len(year) == 0:
                pass
            elif len(year) == 4:
                year = '+{}-01-01T00:00:00Z'.format(year)
                precision = 9
            elif len(year) == 6:
                year = '+{}-{}-01T00:00:00Z'.format(year[0:4], year[4:6])
                precision = 10
            else:
                raise Exception('unknown year {}'.format(year))

            # rating
            rating = parse_rating(rating)

            data = {
                'labels': {},
                'claims': {},
                'sitelinks': {},
            }

            data['claims']['P3'] = [{
                'mainsnak': {
                    'snaktype': 'value',
                    'property': 'P3',
                    'datatype': 'wikibase-item',
                    'datavalue': {
                        'value': {
                            'entity-type': 'item',
                            'numeric-id': 53,
                        },
                        'type': 'wikibase-entityid',
                    },
                },
                'type': 'statement',
                'rank': 'normal',
            }]

            print(animetitle)
            data['labels']['zh-tw'] = {
                'language': 'zh-tw',
                'value': animetitle
            }

            if othertitle:
                print('\t othertitle', othertitle)
                data['aliases'] = {
                    'zh-tw': []
                }
                for title in othertitle:
                    data['aliases']['zh-tw'].append({

                        'language': 'zh-tw',
                        'value': title
                    })

            if seenepisodes:
                print('\t seenepisodes', seenepisodes)
                data['claims']['P28'] = [{
                    'mainsnak': {
                        'snaktype': 'value',
                        'property': 'P28',
                        'datatype': 'string',
                        'datavalue': {
                            'value': {
                                'amount': '+{}'.format(seenepisodes),
                                'unit': '1'
                            },
                            'type': 'quantity'
                        }
                    },
                    'type': 'statement',
                    'rank': 'normal',
                }]

            if allepisodes:
                print('\t allepisodes', allepisodes)
                data['claims']['P27'] = [{
                    'mainsnak': {
                        'snaktype': 'value',
                        'property': 'P27',
                        'datatype': 'string',
                        'datavalue': {
                            'value': {
                                'amount': '+{}'.format(allepisodes),
                                'unit': '1'
                            },
                            'type': 'quantity'
                        }
                    },
                    'type': 'statement',
                    'rank': 'normal',
                }]

            if update:
                print('\t update', update)
                data['claims']['P31'] = [{
                    'mainsnak': {
                        'snaktype': 'value',
                        'property': 'P31',
                        'datatype': 'wikibase-item',
                        'datavalue': {
                            'value': {
                                'entity-type': 'item',
                                'numeric-id': update.replace('Q', ''),
                            },
                            'type': 'wikibase-entityid',
                        },
                    },
                    'type': 'statement',
                    'rank': 'normal',
                }]

            if comment:
                print('\t comment', comment)
                data['claims']['P26'] = [{
                    'mainsnak': {
                        'snaktype': 'value',
                        'property': 'P26',
                        'datatype': 'string',
                        'datavalue': {
                            'value': comment,
                            'type': 'string'
                        }
                    },
                    'type': 'statement',
                    'rank': 'normal',
                }]

            if length:
                print('\t length', length)
                data['claims']['P25'] = [{
                    'mainsnak': {
                        'snaktype': 'value',
                        'property': 'P25',
                        'datatype': 'string',
                        'datavalue': {
                            'value': {
                                'amount': '+{}'.format(length),
                                'unit': 'https://xiplus.ddns.net/entity/Q54',
                            },
                            'type': 'quantity'
                        }
                    },
                    'type': 'statement',
                    'rank': 'normal',
                }]

            if wikipedia:
                print('\t wikipedia', wikipedia)
                data['claims']['P65'] = [{
                    'mainsnak': {
                        'snaktype': 'value',
                        'property': 'P65',
                        'datatype': 'string',
                        'datavalue': {
                            'value': wikipedia,
                            'type': 'string'
                        }
                    },
                    'type': 'statement',
                    'rank': 'normal',
                }]
                '''
                data['sitelinks']['zhwiki'] = {
                    'site': 'zhwiki',
                    'title': wikipedia,
                    'badges': [],
                }
                '''

            if moegirl:
                print('\t moegirl', moegirl)
                data['claims']['P66'] = [{
                    'mainsnak': {
                        'snaktype': 'value',
                        'property': 'P66',
                        'datatype': 'string',
                        'datavalue': {
                            'value': moegirl,
                            'type': 'string'
                        }
                    },
                    'type': 'statement',
                    'rank': 'normal',
                }]
                '''
                data['sitelinks']['moegirl'] = {
                    'site': 'moegirl',
                    'title': moegirl,
                    'badges': [],
                }
                '''

            if link1P:
                print('\t', link1P, link1)
                data['claims'][link1P] = [{
                    'mainsnak': {
                        'snaktype': 'value',
                        'property': link1P,
                        'datatype': 'string',
                        'datavalue': {
                            'value': link1,
                            'type': 'string'
                        }
                    },
                    'type': 'statement',
                    'rank': 'normal',
                }]

            if link2P:
                print('\t', link2P, link2)
                data['claims'][link2P] = [{
                    'mainsnak': {
                        'snaktype': 'value',
                        'property': link2P,
                        'datatype': 'string',
                        'datavalue': {
                            'value': link2,
                            'type': 'string'
                        }
                    },
                    'type': 'statement',
                    'rank': 'normal',
                }]

            if link3P:
                print('\t', link3P, link3)
                data['claims'][link3P] = [{
                    'mainsnak': {
                        'snaktype': 'value',
                        'property': link3P,
                        'datatype': 'string',
                        'datavalue': {
                            'value': link3,
                            'type': 'string'
                        }
                    },
                    'type': 'statement',
                    'rank': 'normal',
                }]

            if link4P:
                print('\t', link4P, link4)
                data['claims'][link4P] = [{
                    'mainsnak': {
                        'snaktype': 'value',
                        'property': link4P,
                        'datatype': 'string',
                        'datavalue': {
                            'value': link4,
                            'type': 'string'
                        }
                    },
                    'type': 'statement',
                    'rank': 'normal',
                }]

            if studio:
                print('\t studio', studio)
                data['claims']['P30'] = []
                for item in studio:
                    data['claims']['P30'].append({
                        'mainsnak': {
                            'snaktype': 'value',
                            'property': 'P30',
                            'datatype': 'wikibase-item',
                            'datavalue': {
                                'value': {
                                    'entity-type': 'item',
                                    'numeric-id': item.replace('Q', ''),
                                },
                                'type': 'wikibase-entityid',
                            },
                        },
                        'type': 'statement',
                        'rank': 'normal',
                    })

            if year:
                print('\t year', year)
                data['claims']['P29'] = [{
                    'mainsnak': {
                        'snaktype': 'value',
                        'property': 'P29',
                        'datatype': 'string',
                        'datavalue': {
                            'value': {
                                'time': '{}'.format(year),
                                'timezone': 0,
                                'before': 0,
                                'after': 0,
                                'precision': precision,
                                'calendarmodel': 'http://www.wikidata.org/entity/Q1985727'
                            },
                            'type': 'time',
                        }
                    },
                    'type': 'statement',
                    'rank': 'normal',
                }]

            if rating:
                print('\t rating', rating)
                data['claims']['P23'] = [{
                    'mainsnak': {
                        'snaktype': 'value',
                        'property': 'P23',
                        'datatype': 'wikibase-item',
                        'datavalue': {
                            'value': {
                                'entity-type': 'item',
                                'numeric-id': rating.replace('Q', ''),
                            },
                            'type': 'wikibase-entityid',
                        },
                    },
                    'type': 'statement',
                    'rank': 'normal',
                }]

            print(data)
            input()
            # item = datasite.editEntity({}, data, summary=u'匯入新動畫項目')
            result = session.post(API, data={
                'action': 'wbeditentity',
                'format': 'json',
                'new': 'item',
                'token': csrftoken,
                'data': json.dumps(data),
                'bot': 1
            }).json()
            print(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    args = parser.parse_args()
    main(args.filename)

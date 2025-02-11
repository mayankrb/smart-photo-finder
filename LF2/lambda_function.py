import json
import boto3
import requests
from requests_aws4auth import AWS4Auth

#comment to check if pipeline is working

def push_to_lex(query):
    #added old comment 1 for checking
    lex = boto3.client('lex-runtime')
    print("lex client initialized")
    response = lex.post_text(
        botName='PhotoSearchBot',                 
        botAlias='PhotoSearchBot',
        userId="id",           
        inputText=query
    )
    print("lex-response", response)
    labels = []
    if 'slots' not in response:
        print("No photo collection for query {}".format(query))
    else:
        print ("slot: ",response['slots'])
        slot_val = response['slots']
        for key,value in slot_val.items():
            if value!=None:
                if value[-1]=='s':
                    value = value[:-1]
                labels.append(value)
        print("Labels gotten are: ", labels)
    return labels


def search_elastic_search(labels):
    aws_access_key_id = '*'
    aws_secret_access_key='*'
    print("Inside open-search")
    region = 'us-east-1' 
    service = 'es'
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(aws_access_key_id, aws_secret_access_key, region, service)
    url = 'https://search-photos-nqsvss3p4rs7oxvs6rogq2ardq.us-east-1.es.amazonaws.com/photos/_search?q='
    resp = []
    for label in labels:
        if (label is not None) and label != '':
            url2 = url+label
            resp.append(requests.get(url2, auth=awsauth).json())
    #print (resp)
    output = []
    for r in resp:
        if 'hits' in r:
             for val in r['hits']['hits']:
                key = val['_source']['objectKey']
                if key not in output:
                    output.append("https://smart-photo-finder-storage.s3.amazonaws.com/"+key)
    print(output)
    return output
    

def lambda_handler(event, context):
    # TODO implement
    print(event)
    q = event['queryStringParameters']['q']
    print(q)
    labels = push_to_lex(q)
    print("labels", labels)
    if len(labels) != 0:
        img_paths = list(set(search_elastic_search(labels)))
    if not img_paths:
        return{
            'statusCode':404,
            'headers': {"Access-Control-Allow-Origin":"*","Access-Control-Allow-Methods":"*","Access-Control-Allow-Headers": "*"},
            'body': json.dumps('No Results found')
        }
    else:  
        print(img_paths)
        return{
            'statusCode': 200,
            'headers': {"Access-Control-Allow-Origin":"*","Access-Control-Allow-Methods":"*","Access-Control-Allow-Headers": "*"},
            'body': json.dumps(img_paths)
        }

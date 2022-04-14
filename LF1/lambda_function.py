import json
import os
import time
import logging
import boto3
import base64
from datetime import datetime
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

#adding comment for demo purposes
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
 
region = 'us-east-1'
service = 'es'
aws_access_key_id = '*'
aws_secret_access_key='*' 
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(aws_access_key_id, aws_secret_access_key, region, service)
host = "search-photos-nqsvss3p4rs7oxvs6rogq2ardq.us-east-1.es.amazonaws.com"
rekognition_client = boto3.client('rekognition')
 
es = OpenSearch(
        hosts = [{'host': host, 'port': 443}],
        http_auth = awsauth, 
        use_ssl = True,
        verify_certs = True, 
        connection_class = RequestsHttpConnection
    )
 
def get_custom_labels(bucket, file_name):
    s3 = boto3.client("s3")
    metadata = s3.head_object(
        Bucket = bucket, 
        Key = file_name
    )
    if "customlabels" in metadata["Metadata"].keys():
        customlabels = metadata["Metadata"]["customlabels"]
    else:
        customlabels = ""
    customLabels = customlabels.split(',')
    return customLabels
 
def lambda_handler(event, context):
    print("Lambda invoked...")
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug(credentials)
    records = event['Records']
    print("Working on records...")
    for record in records:
        print("Working on record...")
        s3object = record['s3']
        bucket = s3object['bucket']['name']
        objectKey = s3object['object']['key']
        print(bucket, objectKey)
        image = {
            'S3Object' : {
                'Bucket' : bucket,
                'Name' : objectKey
            }
        }
        print(image["S3Object"])
        response = rekognition_client.detect_labels(Image=image, Bucket=bucket)
        print("get labels...")
        print(get_custom_labels(bucket, objectKey))
        labels = list(map(lambda x : x['Name'], response['Labels']))
        labels.extend(get_custom_labels(bucket, objectKey))
        labels = [x.lower() for x in labels]
        timestamp = datetime.now().strftime('%Y-%d-%mT%H:%M:%S')
        print(labels)
        esObject = json.dumps({
            'objectKey' : objectKey,
            'bucket' : bucket,
            'createdTimesatamp' : timestamp,
            'labels' : labels
        })
        print('hitting es index...')
        es.index(index = "photos", doc_type = "Photo", id = objectKey, body = esObject, refresh = True)
        print('ending index...')
 
 
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }

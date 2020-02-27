import os
import boto3

aws_s3_bucket        = os.environ['AWS_BUCKET']
aws_s3_accesskey     = os.environ['AWS_ACCESS_KEY_ID']
aws_s3_secretkey     = os.environ['AWS_SECRET_ACCESS_KEY']

def aws_save_image(file_name):
    s3_resource = boto3.resource('s3')
    s3_resource.Bucket(aws_s3_bucket).upload_file(file_name, file_name)


def aws_get_url(file_name):
    s3_client = boto3.client('s3')
    s3_image_url = s3_client.generate_presigned_url(
        ClientMethod = 'get_object',
        Params       = {'Bucket': aws_s3_bucket, 'Key': file_name},
        ExpiresIn    = 10,
        HttpMethod   = 'GET'
    )
    
    return s3_image_url

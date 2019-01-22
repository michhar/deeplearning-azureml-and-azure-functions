import logging
import azure.functions as func
from azureml.core import Workspace
import os
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    image_url = req.params.get('img')
    logging.info(type(image_url))

    # Get an existing workspace
    ws = Workspace.get(name='azuremlws',
                        subscription_id=os.getenv('AZURE_SUB', ''), 
                        resource_group='azureml')

    # Write the config file that holds the workspace info for loading later
    # ws.write_config()

    # Write a config.json (fill in template values)
    # config_temp = json.load('aml_config_template.json')
    # config_temp['subscription_id'] = os.getenv('AZURE_SUB', '')
    # 

    # Get the workspace from config.json
    # ws = Workspace.from_config()

    # path = os.path.join(os.getcwd(), "HttpTrigger", "file.txt")

    return json.dumps('foo')

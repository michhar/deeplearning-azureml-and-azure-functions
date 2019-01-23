import logging
import azure.functions as func
from azureml.core import Workspace, Experiment
from azureml.exceptions import ProjectSystemException
from azureml.core.compute import ComputeTarget, AmlCompute
from azureml.core.compute_target import ComputeTargetException
from azureml.train.dnn import PyTorch
import shutil
import os
import json


def main(req: func.HttpRequest) -> (func.HttpResponse):
    logging.info('Python HTTP trigger function processed a request.')

    image_url = req.params.get('img')
    logging.info(type(image_url))

    # Write a config.json (fill in template values with system vars)
    config_temp = {'subscription_id': os.getenv('AZURE_SUB', ''),
        'resource_group': os.getenv('RESOURCE_GROUP', ''),
        'workspace_name': os.getenv('WORKSPACE_NAME', '')}
    with open(os.path.join(os.getcwd(), 'HttpTrigger', 'config.json'), 'w') as f:
        json.dump(config_temp, f)

    # Get the workspace from config.json
    try:
        ws = Workspace.from_config(os.path.join(os.getcwd(), 'HttpTrigger', 'config.json'))
    except ProjectSystemException as err:
        print(err)

    # choose a name for your cluster
    cluster_name = "gpucluster"

    try:
        compute_target = ComputeTarget(workspace=ws, name=cluster_name)
        print('Found existing compute target.')
    except ComputeTargetException:
        print('Creating a new compute target...')
        compute_config = AmlCompute.provisioning_configuration(vm_size='STANDARD_NC6', 
                                                            max_nodes=4)
        # create the cluster
        compute_target = ComputeTarget.create(ws, cluster_name, compute_config)
        compute_target.wait_for_completion(show_output=True)

    # use get_status() to get a detailed status for the current cluster. 
    print(compute_target.get_status().serialize())

    # Create a project directory and copy training script to ii
    project_folder = os.path.join(os.getcwd(), 'HttpTrigger', 'project')
    os.makedirs(project_folder, exist_ok=True)
    shutil.copy(os.path.join(os.getcwd(), 'HttpTrigger', 'pytorch_train.py'), project_folder)

    # Create an experiment
    experiment_name = 'fish-no-fish'
    experiment = Experiment(ws, name=experiment_name)


    script_params = {
        '--num_epochs': 30,
        '--output_dir': './outputs'
    }

    estimator = PyTorch(source_directory=project_folder, 
                        script_params=script_params,
                        compute_target=compute_target,
                        entry_script='pytorch_train.py',
                        use_gpu=True)

    return json.dumps('foo')

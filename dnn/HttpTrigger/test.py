import logging
from azureml.core import Workspace, Experiment, Datastore
from azureml.exceptions import ProjectSystemException
from azureml.core.compute import ComputeTarget, AmlCompute
from azureml.core.compute_target import ComputeTargetException
from azureml.train.dnn import PyTorch
import shutil
import os
import json
import time


def main():
    logging.info('Python driver for an AML PyTorch Experiment run')

    # Write a config.json (fill in template values with system vars)
    config_temp = {'subscription_id': os.getenv('AZURE_SUB', ''),
        'resource_group': os.getenv('RESOURCE_GROUP', ''),
        'workspace_name': os.getenv('WORKSPACE_NAME', '')}
    with open(os.path.join(os.getcwd(), 'config.json'), 'w') as f:
        json.dump(config_temp, f)

    # Get the workspace from config.json
    try:
        ws = Workspace.from_config(os.path.join(os.getcwd(), 'config.json'))
    # Authentication didn't work
    except ProjectSystemException as err:
        return json.dumps('ProjectSystemException')
    # Need to create the workspace
    except Exception as err:
        ws = Workspace.create(name=os.getenv('WORKSPACE_NAME', ''),
                      subscription_id=os.getenv('AZURE_SUB', ''), 
                      resource_group=os.getenv('RESOURCE_GROUP', ''),
                      create_resource_group=True,
                      location='westus2' # Or other supported Azure region   
                     )

        

    # choose a name for your cluster - under 16 characters
    cluster_name = "gpuforpytorch"

    try:
        compute_target = ComputeTarget(workspace=ws, name=cluster_name)
        print('Found existing compute target.')
    except ComputeTargetException:
        print('Creating a new compute target...')
        # AML Compute config - if max_nodes are set, it becomes persistent storage that scales
        compute_config = AmlCompute.provisioning_configuration(vm_size='STANDARD_NC6',
                                                            min_nodes=0,
                                                            max_nodes=2)
        # create the cluster
        compute_target = ComputeTarget.create(ws, cluster_name, compute_config)
        compute_target.wait_for_completion(show_output=True)

    # use get_status() to get a detailed status for the current cluster. 
    # print(compute_target.get_status().serialize())

    # Create a project directory and copy training script to ii
    project_folder = os.path.join(os.getcwd(), 'project')
    os.makedirs(project_folder, exist_ok=True)
    shutil.copy(os.path.join(os.getcwd(), 'pytorch_train.py'), project_folder)

    # Create an experiment
    experiment_name = 'fish-no-fish'
    experiment = Experiment(ws, name=experiment_name)

    # Use an AML Data Store for training data
    ds = Datastore.register_azure_blob_container(workspace=ws, 
        datastore_name='funcdefaultdatastore', 
        container_name=os.getenv('STORAGE_CONTAINER_NAME_TRAINDATA', ''),
        account_name=os.getenv('STORAGE_ACCOUNT_NAME', ''), 
        account_key=os.getenv('STORAGE_ACCOUNT_KEY', ''),
        create_if_not_exists=True)

    # Use an AML Data Store to save models back up to
    ds_models = Datastore.register_azure_blob_container(workspace=ws, 
        datastore_name='modelsdatastorage', 
        container_name=os.getenv('STORAGE_CONTAINER_NAME_MODELS', ''),
        account_name=os.getenv('STORAGE_ACCOUNT_NAME', ''), 
        account_key=os.getenv('STORAGE_ACCOUNT_KEY', ''),
        create_if_not_exists=True)

    # Set up for training ("trans" flag means - use transfer learning and 
    # this should download a model on compute)
    script_params = {
        '--data_dir': ds.as_mount(),
        '--num_epochs': 30,
        '--learning_rate': 0.01,
        '--output_dir': './outputs',
        '--trans': 'True'
    }

    # Instantiate PyTorch estimator with upload of final model to
    # a specified blob storage container (this can be anything)
    estimator = PyTorch(source_directory=project_folder, 
                        script_params=script_params,
                        compute_target=compute_target,
                        entry_script='pytorch_train.py',
                        use_gpu=True,
                        inputs=[ds_models.as_upload(path_on_compute='./outputs/model_finetuned.pth')])

    run = experiment.submit(estimator)
    details = run.get_details()
    print(details)
    logging.info(details)
    
    # # The following would certainly be blocking
    # while run.get_status() not in ['Completed', 'Failed']: # For example purposes only, not exhaustive
    #    print('Run {} not in terminal state'.format(run.id))
    #    time.sleep(10)
    status = run.get_status()
    print(status)
    logging.info(status)


if __name__ == '__main__':
    main()
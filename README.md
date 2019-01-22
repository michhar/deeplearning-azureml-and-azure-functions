# Training a Model with Azure ML and Azure Functions

Automating the training of new model given new code and/or new data and labels provided by a data scientist, is a challenge for the dev ops or app development professional.  This challenge is what is addressed here.  A general solution would be to integrate model training into an Azure Function.  Read on for more details.

The intent of this repository is to communicate the process of training a model using a Python-based Azure Function and the Azure ML Python SDK and to provide a code sample for doing so.  Training a model with the Azure ML Python SDK involves setting, possibly provisioning and consuming an Azure Compute option (e.g. an N-Series Data Science Virtual Machine) - the model _is not_ trained within the Azure Function Consumption Plan.  Triggers for the Azure Function could be HTTP, Azure Blob Storage containers via Event Grid, or by other means.

The motivation behind this process was to provide a way to automate the model training process once the data scientist had provided new data and labels which were stored in Azure Blob containers.  The idea is that once new labels were provided, it would signal training a new model and subsequently performing evaluation and A/B testing.  The downstream event from the Azure Function could be moving a model to a separate "models" Blob container.  This new model could, then, be part of an IoT Edge Module build, for example, or other app build and release.

The following diagram represents this process as part of a larger deployment.

<img src="images/arch_diagram.png" width="70%" alignment="center">

## Instructions

The instruction below is only an example - it follows [this Azure Docs tutorial](https://docs.microsoft.com/en-us/azure/azure-functions/functions-create-first-function-python) which should be referenced as needed.



The commands are listed here for quick reference (but if it doesn't work, check doc above as it may have updated - note, you will still need to `pip install requirements.txt` to test locally):

### Set up virtual environment

In a bash terminal, make a directory for the azure function and `cd` into it.

* Create a fresh env for each function
* Make sure `.env` resides in main folder (same place you find `requirements.txt`)

```
    python3.6 -m venv .env

    source .env/bin/activate
```

### Test function locally

```
    pip install -r requirements.txt
    
    func host start
```

### Deploy function to Azure

```
    az login

    az group create --name azfunc --location westus

    az storage account create --name azfuncstorage123 --location westus --resource-group azfunc --sku Standard_LRS

    az functionapp create --resource-group azfunc --os-type Linux --consumption-plan-location westus --runtime python --name dnnfuncapp --storage-account azfuncstorage123

    
    func azure functionapp publish dnnfuncapp --build-native-deps
```

Add `AZURE_SUB` as a key/value pair (using your subscription id) under **Application settings** in the "Application settings" configuration link/tab. 

### Test deployment

```
    curl https://dnnfuncapp.azurewebsites.net/api/HttpTrigger?<a key defined in code>=<some test value>
```






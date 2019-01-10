# Repositorio de utilidades para AWS

Este repositorio contiene algunas de las herramientas creadas para el día a día usados en la administración de servicios en AWS.
No todos son bonitos ni perfectamente hechos, pero muchos cumplen con su cometido y siempre esta la posibilidad de mejorarlos.


## manage/buttler.py
Script que permite iniciar o detener "ambientes".
La división lógica se basa en tags incorporados en las instancias, tanto EC2 como RDS.

El script lee un archivo de configuración `buttler.conf` donde tiene definidos varios parametros, tales como los perfiles de AWS (aws_access_key y aws_secret_access_key), tags a revisar o saltar, etc.

```
usage: buttler.py [-h] --profile PROFILE [--debug] [--region REGION] --config
                  CONFIG [--skip-rds] [--skip-ec2] [--verbose] [--env ENV]
                  (--start | --stop | --status | --reserve | --free)

A little script which will help you start or stop EC2 instances and/or RDS
instances.

optional arguments:
  -h, --help         show this help message and exit
  --profile PROFILE  Set the profile to use when fetching or uploading
                     parameters.
  --debug            Debug mode, TODO
  --region REGION    Sets the region from where to gather data. Defaults to
                     us-east-1
  --config CONFIG    Specify the config file.
  --skip-rds         Skip start/stop of RDS instances.
  --skip-ec2         Skip start/stop of EC2 instances.
  --verbose          Show more information.
  --env ENV          Target environment, ex: all, qa, dev, uat. The tag must
                     exists.
  --start            Start instances.
  --stop             Stop intances
  --status           Shows instances status
  --reserve          Reserve the specified environment.
  --free             Free the specified environment
  ```

## ssm/menu_parameters.py

Simple menu hecho en python que muestra un listado de parametros creados en Parameter Store para su posterior visualizacion y/o edición.

El mismo espera un path como parametro y utiliza el perfil por defecto si ninguno es provisto al momento de ejecutar.

```
usage: menu_parameters.py [-h] [--profile PROFILE] [--debug] [--region REGION]
                          --path PATH

App to put/get parameters from SSM/Parameter Store in AWS.

optional arguments:
  -h, --help         show this help message and exit
  --profile PROFILE  Set the profile to use when fetching or uploading
                     parameters. If no profile is provided, ENV variables and
                     .aws/config is used by default.
  --debug            Debug mode, TODO
  --region REGION    Sets the region from where to gather data. Defaults to
                     us-east-1
  --path PATH        Sets the path from where to look for paramet
  ```
## ssm/put_parameters.py

Script para popular y crear parametros en Parameters Store.
El mismo toma como parametro un archivo `.json` donde estan definidos todos los datos necesarios.

```
usage: put_parameters.py [-h] --filein FILEIN [--profile PROFILE] [--debug]
                         [--region REGION]

App to put/get parameters from SSM/Parameter Store in AWS.

optional arguments:
  -h, --help         show this help message and exit
  --filein FILEIN    Json source file.
  --profile PROFILE  Set the profile to use when fetching or uploading
                     parameters. If no profile is provided, ENV variables and
                     .aws/config is used by default.
  --debug            Debug mode, TODO
  --region REGION    Sets the region from where to gather data. Defaults to
                     us-east-1
```

## ssm/get_parameters.py

Script que hace un dump de los parametros en Parameter Store a un archivo o consola.
El mismo necesita que se le pase el `path` como parametro y leera de forma recursiva la informacion en AWS.

Util para guardar backups de parametros a un archivo.

```
usage: get_parameters.py [-h] [--profile PROFILE] [--path PATH]
                         [--fileout FILEOUT] [--debug] [--region REGION]

A litle tool to get parameters from SSM/Parameter Store and save them into a
file.

optional arguments:
  -h, --help         show this help message and exit
  --profile PROFILE  Set the profile to use when fetching or uploading
                     parameters. If no profile is provided, ENV variables and
                     .aws/config is used by default.
  --path PATH        Path from where to get the parameter data.
  --fileout FILEOUT  Filename of the file data will be saved. Data will be
                     json formatted.
  --debug            Debug mode, TODO
  --region REGION    Sets the region from where to gather data. Defaults to
                     us-east-1
 ```

## ec2/check_space.py

Pequeño script que chequea el espacio en disco en una instancia, discriminando via particiones declaradas en el archivo de configuracion `check_space.conf` y envia un mensaje via **SNS** cuando se llega al limite establecido.

Utiliza las librerias `psutil` de python.

```
usage: check_space.py [-h] [--profile PROFILE] [--debug] [--region REGION]
                      --config CONFIG [--dry-run]

Check free space on partitions. If any of them are above the defined
threshold, then a notification is send via a SNS Topic.

optional arguments:
  -h, --help         show this help message and exit
  --profile PROFILE  Set the profile to use when fetching or uploading
                     parameters. If no profile is provided, ENV variables and
                     .aws/config is used by default.
  --debug            Debug mode, TODO
  --region REGION    Sets the region from where to gather data. Defaults to
                     us-east-1
  --config CONFIG    Specify the config file.
  --dry-run          Checks everything that is supposed to, but doesn't really
                     send any notification
  ```

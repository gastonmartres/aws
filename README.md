# Repositorio de utilidades para AWS

Este repositorio contiene algunas de las herramientas creadas para el día a día usados en la administración de servicios en AWS.
No todos son bonitos ni perfectamente hechos, pero muchos cumplen con su cometido y siempre esta la posibilidad de mejorarlos.


**buttler.py**
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
  

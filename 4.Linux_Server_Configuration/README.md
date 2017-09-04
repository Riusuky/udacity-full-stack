# Linux Server configuration

The objective of this project was to set up and configure a Linux server to host the previously developed [Item Catalog](../3.Item_Catalog/) project.

## Server Details

The server infrastructure used to complete this project was the [Amazon Lightsail](https://amazonlightsail.com/).

* IP: `18.220.125.255`
* URL: [http://ec2-18-220-125-255.us-east-2.compute.amazonaws.com](http://ec2-18-220-125-255.us-east-2.compute.amazonaws.com)

## Server Set Up

Before deploying the [Item Catalog](../3.Item_Catalog/) project, some configuration steps were performed to ensure the server security:

* All system packages were updated to most recent versions.
* Password SSH authentication was disabled so that users must use a SSH Key-Based authentication in order to log in to the server.
* Ensured that users cannot log in as root.
* The default port for SSH connection was changed to port 2200.
* Server Firewall was configured to only allow connections for ports 2200 (SSH), 80 (HTTP) and 123 (NTP).
* Configured the local timezone to UTC.

## Software Requirements

In order to deploy the [Item Catalog](../3.Item_Catalog/) project, all requirements listed in the project's [README](../3.Item_Catalog/README.md) were installed. Besides these, some additional software  were installed:

* [Apache](https://www.apache.org/) and the [mod_wsgi](https://modwsgi.readthedocs.io/en/develop/): used to deploy the application.
* [pip](https://pip.pypa.io/en/stable/): used to install Python packages.

#!/usr/bin/env python

import json
import yaml
import os
import heatclient.client
import keystoneclient.v2_0.client
import uuid

def parse(template):
    return yaml.safe_load(template)

def get_identity_client(username, password, tenant_name):
    auth_url = os.environ['OS_AUTH_URL']

    return keystoneclient.v2_0.client.Client(username=username,
                                             password=password,
                                             tenant_name=tenant_name,
                                             auth_url=auth_url)

def get_heat_client(username=None, password=None, tenant_name=None):
     keystone = get_identity_client(username, password, tenant_name)
     token = keystone.auth_token
     try:
         endpoint = keystone.service_catalog.url_for(
             service_type='orchestration',
             endpoint_type='publicURL')
     except keystoneclient.exceptions.EndpointNotFound:
         return None
     else:
         return heatclient.client.Client('1',
              endpoint,
              token=token,
              username=username,
              password=password)

hc = get_heat_client(os.environ['OS_USERNAME'], os.environ['OS_PASSWORD'], os.environ['OS_TENANT_NAME'])

dib_template = open('dib.yaml', 'r')
dib_yaml = parse(dib_template)
template_file = open('OpenShift.yaml', 'r')
template_yaml = parse(template_file)
for res in template_yaml['resources']:
    if template_yaml['resources'][res]['type'] == 'OS::Nova::Server':
        # build install script
        content = '#!/bin/bash\n\nset -e\ninstall-packages heat-cfntools\n'
        content = content + 'install -D /tmp/in_target.d/install.d/metadata /var/lib/heat-cfntools/cfn-init-data\n\n'
        content = content + '/usr/bin/cfn-init\n\n'

        yaml_content_dib = {'/elements/dibt/install.d/30-dibt': {'content': content, 'mode': '00755', 'owner': 'root', 'group': 'root'}}

        yaml_content_metadata = {'/elements/dibt/install.d/metadata': {'content': json.dumps(template_yaml['resources'][res]['Metadata'])}}
            
        files = {}
        files.update(yaml_content_dib)
        files.update(yaml_content_metadata)
        for res in dib_yaml['resources']:
            if dib_yaml['resources'][res]['type'] == 'OS::Nova::Server':
                dib_yaml['resources'][res]['Metadata']['AWS::CloudFormation::Init']['config']['files'] = files

#               print yaml.dump(dib_yaml)

                # create dib stacks for all server resources in this stack

                stack_name =  'dib' + str(uuid.uuid4()).replace('-', '_')
                kwargs ={'stack_name': stack_name, 'template': yaml.dump(dib_yaml),
                         'parameters': {'os_username': os.environ['OS_USERNAME'],
                             'os_password': os.environ['OS_PASSWORD'],
                             'os_tenant_name': os.environ['OS_TENANT_NAME'],
                             'os_auth_url': os.environ['OS_AUTH_URL'],
                             'dib_image_name': stack_name,
                             'key_name': 'goofy'}}
                hc.stacks.create(**kwargs)

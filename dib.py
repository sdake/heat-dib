#!/usr/bin/env python

import json
import yaml
import os
from keystoneclient.v2_0 import client as ks_client
import heatclient
from heatclient import client as heat_client
import uuid

def parse(template):
    return yaml.safe_load(template)

keystone = ks_client.Client(username=os.environ['OS_USERNAME'], password=os.environ['OS_PASSWORD'], tenant_name=os.environ['OS_TENANT_NAME'], auth_url=os.environ['OS_AUTH_URL'])
kwargs = {
    'token': keystone.auth_token,
    'insecure': False,
    'timeout': 600,
    'ca_file': None,
    'cert_file': None,
    'key_file': None,
    'tenant_id': '',
    'username': os.environ['OS_USERNAME'],
    'password': os.environ['OS_PASSWORD']
}
endpoint = keystone.service_catalog.url_for(service_type='orchestration', endpoint_type='publicURL')
hc = heat_client.Client('1', endpoint, **kwargs)

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

                # create dib stacks for all server resources in this stack

                stack_name =  'dib' + str(uuid.uuid4()).replace('-', '_')
                kwargs ={'stack_name': stack_name, 'template': yaml.dump(dib_yaml),
                	 'parameters': {'os_username': os.environ['OS_USERNAME'],
                	     'os_password': os.environ['OS_PASSWORD'],
                	     'os_tenant_name': os.environ['OS_TENANT_NAME'],
                	     'os_auth_url': os.environ['OS_AUTH_URL'],
                	     'dib_image_name': stack_name,
                	     'key_name': 'goofy'},
                             'timeout_mins': '6000',
                             'disable_rollback': True}
                hc.stacks.create(**kwargs)

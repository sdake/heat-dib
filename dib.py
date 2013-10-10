#!/usr/bin/env python

import json
import yaml

def parse(template):
    return yaml.safe_load(template)

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

        print yaml.dump(dib_yaml)

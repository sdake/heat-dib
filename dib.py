#!/usr/bin/env python

import yaml

def parse(template):
    return yaml.safe_load(template)

yaml_content = dict()
dib_template = open('dib.yaml', 'r')
dib_yaml = parse(dib_template)
template_file = open('OpenShift.yaml', 'r')
template_yaml = parse(template_file)
for res in template_yaml['resources']:
    if template_yaml['resources'][res]['type'] == 'OS::Nova::Server':
        rsrc = template_yaml['resources'][res]
        rsrc_init = rsrc['Metadata']
        print rsrc_init
        packages = rsrc_init['AWS::CloudFormation::Init']['config']['packages']['yum']
        content = '#!/bin/bash\n\nset -e\ninstall-packages '
        for package in packages:
            content = content + package
        filename = '/elements/' + res + '/install.d/30-' + res
        yaml_content[res] = {'%s' % filename: \
            {'content': rsrc_init, 'mode': '00400', 'owner': 'root', \
            'group': 'root'}}

for res in yaml_content:
    files = list()
    files.append(yaml_content[res])
    new_yaml = {'config': {'files': files}}
#    print yaml.dump(new_yaml)


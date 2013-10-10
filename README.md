heat-dib
========

Heat Disk Image Builder Tool

This tool uses Heat to process an existing Heat template into a pre-built image
using Fedora 19's diskimage-builder and load it into glance.

Instructions
============
source devstack/openrc admin admin
python dib.py

At the moment the code only registers the image with glance, but does not create
a new template to use with it.

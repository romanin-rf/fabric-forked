<img alt="PyPI - Package Version" src="https://img.shields.io/pypi/v/fabric-forked">
<img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/fabric-forked">
<img alt="PyPI - Fabric Licence" src="https://img.shields.io/pypi/l/fabric">
<img alt="PyPI - FabricForked Licence" src="https://img.shields.io/pypi/l/fabric-forked">

# Welcome to FabricForked!

## Description (FabricForked)

**FabricForked** is a fork of the [Fabric](https://github.com/fabric/fabric) library, which *transplants the existing library functionality to a new typing* and *corrects some elements WITHOUT STRUCTURALLY CHANGING ANYTHING*!

## Description (Fabric)

[Fabric](https://github.com/fabric/fabric) - is a ***high level Python library*** designed to *execute shell commands remotely over SSH*, yielding useful *Python objects* in return. It builds on top of [Invoke](https://pyinvoke.org) (*subprocess command execution and command-line features*) and [Paramiko](https://paramiko.org) (*SSH protocol implementation*), extending their APIs to complement one another and provide additional functionality.

To find out what's new in this version of [Fabric](https://github.com/fabric/fabric), please see [the changelog](https://fabfile.org/changelog.html#%7B%7D).

The project maintainer keeps a [roadmap](https://bitprophet.org/projects#roadmap) on his website.

## Usage

The [Fabric](https://github.com/fabric/fabric) **methods have not changed** in any way, the only thing you will have to do is **redefine the imports** on **FabricForked**:
```python
import os

password = os.environ.get('FABRIC_FORKED_SSH_PASSWORD', None)

import fabric_forked as fabric
from fabric_forked import Connection, Result


with Connection('localhost', port=22, user='fabricforked', connect_kwargs={'password': password}) as connection:
    result = connection.run()
    if result is not None:
        ...
```
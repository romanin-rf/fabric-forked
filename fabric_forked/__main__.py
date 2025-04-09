"""
This code provides the ability to run fabric
package as a script
Usage: python -m fabric
"""

from .fabric.main import program


if __name__ == '__main__':
    program.run()
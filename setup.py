from distutils.core import setup

setup(
    name='projector_tools',
    python_requires='>=3.8',
    author='Martin Privat',
    version='0.0.2',
    packages=['projector_tools'],
    license='Creative Commons Attribution-Noncommercial-Share Alike license',
    description='Remote control video projectors',
    long_description=open('README.md').read(),
    install_requires=[
        "pyserial",
        "hidapi",
        "numpy"
    ]
)
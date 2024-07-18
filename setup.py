from setuptools import setup, find_packages


with open('requirements.txt', 'r') as fp:
    install_requires = fp.read().splitlines()

setup(
    name='sherlock',
    description='Investigation tool to find potential attack by using Perfetto traces',
    version='0.0.1',
    packages=find_packages(),
    license="APACHE",
    url="https://github.com/google/sherlock",
    install_requires=install_requires,
    requires = ["setuptools"]
)
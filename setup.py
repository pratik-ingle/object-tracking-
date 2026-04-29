from setuptools import setup, find_packages

setup(
    name='opti_tracker',
    version='0.1.0',
    packages=find_packages(),
    install_requires=['numpy', 'python-dotenv'],
    python_requires='>=3.8',
)
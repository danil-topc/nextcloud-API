import os
import setuptools

SETUPDIR = os.path.dirname(__file__)
PKGDIR = os.path.join(SETUPDIR, 'src')

with open('./README.md', 'r') as f:
    long_description = f.read()


setuptools.setup(
    name='nextcloud',
    version='0.0.1',
    author='EnterpriseyIntranet',
    description="Python wrapper for NextCloud api",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/EnterpriseyIntranet/nextcloud-API",
    packages=setuptools.find_packages(PKGDIR),
    include_package_data=True,
    install_requires=['requests'],
    package_dir={'': PKGDIR},
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        "Operating System :: OS Independent"
    ],
)

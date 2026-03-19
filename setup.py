from setuptools import find_packages, setup
import os                  
from glob import glob      

package_name = 'wheel_loader_manager'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')), # <--- comma!
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='gizmoros2',
    maintainer_email='kiranpunarthum@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
        'system_manager = wheel_loader_manager.system_manager:main',
        'system_manager2 = wheel_loader_manager.system_manager2:main',
        'system_manager3 = wheel_loader_manager.system_manager3:main',
        'system_manager4 = wheel_loader_manager.system_manager4:main',
        ],
    },
)

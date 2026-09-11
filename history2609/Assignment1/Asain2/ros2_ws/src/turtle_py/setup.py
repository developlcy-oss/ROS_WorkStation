from setuptools import find_packages, setup

package_name = 'turtle_py'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        (
            'share/ament_index/resource_index/packages',
            ['resource/' + package_name]
        ),
        (
            'share/' + package_name,
            ['package.xml']
        ),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='pa3',
    maintainer_email='developlcy@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'distance_publisher = turtle_py.distance_publisher:main',
            'distance_warning = turtle_py.distance_warning:main',
            'square_controller = turtle_py.square_controller:main',
            'turtle_tf_broadcaster = turtle_py.turtle_tf_broadcaster:main',
            'waypoint_marker = turtle_py.waypoint_marker:main',
            'polygonController = turtle_py.polygonController:main',
        ],
    },
)
from setuptools import setup

setup(name='deme',
      version='0.9',
      description="Deme",
      long_description="",
      author='Mike Mintz',
      author_email='',
      license='GNU AFFERO GENERAL PUBLIC LICENSE',
      packages=['deme_django'],
      zip_safe=False,
      install_requires=[
          'Django',
          'South',
          'psycopg2',
          'django-pure-pagination',
          ],
      )
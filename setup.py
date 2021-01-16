from cx_Freeze import setup, Executable

includefiles = ['templates', 'static', 'chromedriver.exe', 'data.csv', 'subscribe.csv']  #
includes = ['jinja2.ext', 'jinja2']  # add jinja2.ext here

setup(
    name='bilibili lottery helper',
    version='1.0',
    description='bilibili lottery helper',
    # Add includes to the options
    options={'build_exe': {'include_files': includefiles, 'includes': includes}},
    executables=[Executable('app.py')]
)

# python setup.py build

import setuptools

setuptools.setup(
    name="steam-achievement-compiler",
    author="Tyler Sontag",
    packages=setuptools.find_packages(),
    install_requires=[
        "flask",
        "requests"
    ]
)
